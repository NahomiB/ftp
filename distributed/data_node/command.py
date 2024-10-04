import os
import json
from utils import funcion_hash, obtener_id, hacer_ping_nodo
from table import obtener_k_sucesores, NodoDato


def manejar_comando_union(nodo_dato: NodoDato, ip, puerto, socket_cliente):
    """
    Agrega un nodo como sucesor de este nodo.
    """

    # Esperar hasta que la primera actualización del nodo esté completa
    while not nodo_dato.termino_primera_actualizacion:
        pass

    # Adquirir el mutex para evitar condiciones de carrera al unirse
    nodo_dato.mutex_union.acquire()

    # Calcular el ID del nodo que intenta unirse
    id_nodo_unirse = funcion_hash(obtener_id(ip, puerto))

    try:
        # Adquirir el mutex del predecesor para acceder de manera segura a su información
        nodo_dato.mutex_predecesor.acquire()
        predecesor = nodo_dato.predecesor  # Obtener el predecesor actual
        nodo_dato.mutex_predecesor.release()  # Liberar el mutex

        # Verificar si el nodo que intenta unirse debe ser agregado como sucesor
        if predecesor is None or (
            predecesor[0] > nodo_dato.identificador and 
            (id_nodo_unirse <= nodo_dato.identificador or id_nodo_unirse > predecesor[0])
        ) or (
            predecesor[0] < id_nodo_unirse and 
            id_nodo_unirse <= nodo_dato.identificador
        ):
            # Si no hay predecesor, establecer el nodo actual como su propio predecesor
            if not predecesor:
                predecesor = nodo_dato.identificador, nodo_dato.host, nodo_dato.puerto

            # Enviar la información del predecesor al nodo que intenta unirse
            socket_cliente.send(f"220 {predecesor[1]}:{predecesor[2]}".encode())
            
            # Esperar la respuesta del nodo que intenta unirse
            respuesta = socket_cliente.recv(1024).decode().strip()

            if respuesta.startswith("220"):  # Comprobar si la respuesta es exitosa
                items = []

                # Intentar obtener los datos del nodo actual
                while True:
                    try:
                        items = list(nodo_dato.datos.items())
                        break  # Salir del bucle si se obtienen los datos
                    except Exception as e:
                        if nodo_dato.verbose:
                            print(f"Error: {e}")  # Imprimir error si ocurre

                # Transferir los datos al nodo que intenta unirse
                for clave, valor in items:
                    id_clave = funcion_hash(clave)

                    # Verificar si la clave debe ser transferida al nodo que intenta unirse
                    if (
                        predecesor[0] > id_nodo_unirse and 
                        (id_clave <= id_nodo_unirse or id_clave > predecesor[0])
                    ) or (
                        predecesor[0] < id_clave and 
                        id_clave <= id_nodo_unirse
                    ):
                        if isinstance(valor[0], dict):  # Si el valor es un diccionario (carpeta)
                            
                            # Codificar los datos de la carpeta en formato JSON
                            datos = f"{json.dumps(valor[0])}".encode()
                            # Enviar información sobre la carpeta
                            socket_cliente.sendall(f"Carpeta {valor[1]} {len(datos)} {clave}".encode())

                            # Esperar la respuesta del nodo que intenta unirse
                            respuesta = socket_cliente.recv(1024).decode().strip()

                            if respuesta.startswith("220"):  # Comprobar si la respuesta es exitosa
                                socket_cliente.sendall(datos)  # Enviar los datos de la carpeta

                                respuesta = socket_cliente.recv(1024).decode().strip()  # Esperar respuesta

                                # Verificar si la transferencia fue exitosa
                                if (not respuesta) or not respuesta.startswith("220"):
                                    raise Exception(f"Algo salió mal enviando datos {ip}:{puerto} {clave}")

                                if nodo_dato.verbose:
                                    print(f"Transferencia completa {clave}")

                        else:  # Si el valor es un archivo
                            # Enviar información sobre el archivo
                            socket_cliente.sendall(f"Archivo {valor[1]} {os.stat(valor[0]).st_size} {clave}".encode())

                            respuesta = socket_cliente.recv(1024).decode().strip()  # Esperar respuesta

                            if respuesta.startswith("220"):  # Comprobar si la respuesta es exitosa
                                # Leer y enviar el archivo en bloques
                                with open(valor[0], "rb") as archivo:
                                    datos = archivo.read(4096)
                                    conteo = 0
                                    while datos:  # Enviar hasta que no queden datos
                                        socket_cliente.sendall(datos)
                                        conteo += len(datos)
                                        datos = archivo.read(4096)

                                respuesta = socket_cliente.recv(1024).decode().strip()  # Esperar respuesta

                                # Verificar si la transferencia fue exitosa
                                if (not respuesta) or not respuesta.startswith("220"):
                                    raise Exception(f"Algo salió mal replicando {ip}:{puerto} {clave}")

                                if nodo_dato.verbose:
                                    print(f"Transferencia completa {clave}")

                # Indicar que la transferencia ha terminado
                socket_cliente.send(b"226 Transferencia completa.\r\n")

                # Actualizar el predecesor del nodo actual
                nodo_dato.mutex_predecesor.acquire()
                nodo_dato.predecesor = id_nodo_unirse, ip, puerto
                nodo_dato.mutex_predecesor.release()

        else:
            # Enviar un mensaje de error si no se puede agregar el nodo
            socket_cliente.send(f"550 {predecesor[1]}:{predecesor[2]}".encode())

    except Exception as e:
        if nodo_dato.verbose:
            print(f"Error: {e}")  # Imprimir error si ocurre

    # Liberar el mutex al finalizar la función
    nodo_dato.mutex_union.release()
 
def manejar_comando_ss(nodo_dato: NodoDato, ip, puerto, socket_cliente):
    """Maneja el comando de sucesor, actualizando el sucesor del nodo."""
    # Se calcula el ID del nuevo sucesor a partir de la IP y puerto del nodo que se está uniendo
    nuevo_id_sucesor = funcion_hash(obtener_id(ip, puerto))

    # Se adquiere el mutex para acceder al sucesor de manera segura
    nodo_dato.mutex_sucesor.acquire()
    nodo_dato.sucesor = nuevo_id_sucesor, ip, puerto  # Actualiza el sucesor
    nodo_dato.mutex_sucesor.release()  # Libera el mutex

def manejar_comando_sp(nodo_dato: NodoDato, ip, puerto, socket_cliente):
    """Maneja el comando de predecesor, actualizando el predecesor del nodo."""
    nodo_dato.mutex_predecesor.acquire()  # Adquiere el mutex para el predecesor

    try:
        nuevo_id_predecesor = funcion_hash(obtener_id(ip, puerto))  # Calcula el ID del nuevo predecesor
        
        # Si no hay predecesor, se asigna el nuevo predecesor
        if nodo_dato.predecesor is None:
            nodo_dato.predecesor = nuevo_id_predecesor, ip, puerto
            socket_cliente.send(f"220".encode())  # Envía una respuesta de éxito

        # Si el nuevo predecesor ya es el mismo que el actual
        elif nuevo_id_predecesor == nodo_dato.predecesor[0]:
            socket_cliente.send(f"220".encode())  # Envía una respuesta de éxito

        # Verifica si el nuevo predecesor debe ser actualizado
        elif (nodo_dato.identificador < nodo_dato.predecesor[0] and 
              (nodo_dato.predecesor[0] < nuevo_id_predecesor or nuevo_id_predecesor < nodo_dato.identificador)) or \
             (nodo_dato.predecesor[0] < nuevo_id_predecesor and nuevo_id_predecesor < nodo_dato.identificador):
            nodo_dato.predecesor = nuevo_id_predecesor, ip, puerto  # Actualiza el predecesor
            socket_cliente.send(f"220".encode())  # Envía una respuesta de éxito

        else:
            # Verifica si el predecesor actual está activo
            if not hacer_ping_nodo(nodo_dato.predecesor[1], nodo_dato.predecesor[2], nodo_dato.verbose):
                nodo_dato.predecesor = nuevo_id_predecesor, ip, puerto  # Actualiza el predecesor
                socket_cliente.send(f"220".encode())  # Envía una respuesta de éxito

            else:
                # Si el predecesor está activo, se envía un mensaje de error
                socket_cliente.send(f"550 {nodo_dato.predecesor[1]}:{nodo_dato.predecesor[2]}".encode())

    finally:
        nodo_dato.mutex_predecesor.release()  # Libera el mutex

def manejar_comando_rp(nodo_dato: NodoDato, socket_cliente):
    """Maneja el comando RP para recibir datos de archivos y carpetas."""
    try:
        # Envía un mensaje de éxito al cliente
        socket_cliente.send(f"220".encode())

        while True:
            # Espera la respuesta del cliente
            respuesta = socket_cliente.recv(1024).decode().strip()

            if respuesta.startswith("Folder"):
                # Procesa el comando para recibir una carpeta
                args = respuesta[7:].strip().split(" ")  # Obtiene los argumentos

                version = int(args[0])  # Obtiene la versión
                size = int(args[1])  # Obtiene el tamaño
                path = " ".join(args[2:])  # Obtiene la ruta

                # Verifica si la carpeta no ha sido eliminada y si la versión es válida
                if (path not in nodo_dato.datos_eliminados or nodo_dato.datos_eliminados[path] != version) and (path not in nodo_dato.datos or nodo_dato.datos[path][1] < version):
                    # Envía un mensaje de éxito al cliente
                    socket_cliente.send(f"220".encode())

                    datos_json = ""
                    conteo = 0
                    # Recibe los datos de la carpeta
                    while conteo < size:
                        datos = socket_cliente.recv(4096)
                        datos_json += datos.decode()
                        conteo += len(datos)

                    # Almacena los datos recibidos en el nodo
                    nodo_dato.datos[path] = json.loads(datos_json), version
                    socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito

                    if nodo_dato.verbose:
                        print(f"Transferencia completa {path}")

                elif path in nodo_dato.datos_eliminados and nodo_dato.datos_eliminados[path] == version:
                    # Si la carpeta ha sido eliminada, envía un mensaje de error
                    socket_cliente.send(f"404".encode())

                else:
                    # Si la versión no es válida, envía un mensaje de error
                    socket_cliente.send(f"403".encode())

            elif respuesta.startswith("File"):
                # Procesa el comando para recibir un archivo
                args = respuesta[5:].strip().split(" ")
                
                version = int(args[0])  # Obtiene la versión
                size = int(args[1])  # Obtiene el tamaño
                clave = " ".join(args[2:])  # Obtiene la clave

                # Verifica si el archivo no ha sido eliminado y si la versión es válida
                if (clave not in nodo_dato.datos_eliminados or nodo_dato.datos_eliminados[clave] != version) and (clave not in nodo_dato.datos or nodo_dato.datos[clave][1] < version):
                    path = os.path.normpath("/app/" + str(nodo_dato.identificador) + os.path.dirname(clave)[4:])  # Ruta donde se almacenará el archivo
                    os.makedirs(path, exist_ok=True)  # Crea la carpeta si no existe

                    path = os.path.normpath(path + "/" + clave[len(os.path.dirname(clave)):])  # Ruta completa del archivo

                    with open(path, "wb") as file:  # Abre el archivo en modo binario
                        socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito

                        conteo = 0
                        # Recibe los datos del archivo
                        while conteo < size:
                            datos = socket_cliente.recv(4096)
                            file.write(datos)  # Escribe los datos en el archivo
                            conteo += len(datos)
                        
                        # Almacena la ruta y la versión del archivo en el nodo
                        nodo_dato.datos[clave] = path, version
                        socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito

                        if nodo_dato.verbose:
                            print(f"Transferencia completa {clave}")

                elif clave in nodo_dato.datos_eliminados and nodo_dato.datos_eliminados[clave] == version:
                    # Si el archivo ha sido eliminado, envía un mensaje de error
                    socket_cliente.send(f"404".encode())

                else:
                    # Si la versión no es válida, envía un mensaje de error
                    socket_cliente.send(f"403".encode())

            elif respuesta.startswith("226"):
                # Si se recibe el código de finalización de transferencia, sale del bucle
                break

    except Exception as e:
        # Manejo de excepciones, imprime el error si está habilitado
        if nodo_dato.verbose:
            print(f"Error: {e}")

def manejar_comando_ed(nodo_dato: NodoDato, clave, socket_cliente):
    """Maneja el comando ED, verifica si la clave existe y responde el tipo de dato."""
    if clave in nodo_dato.datos:
        elemento = nodo_dato.datos[clave][0]

        # Verifica si el elemento es una carpeta o un archivo
        if isinstance(elemento, dict):
            socket_cliente.send(f"220 Carpeta".encode())  # Envía que es una carpeta
        else:
            socket_cliente.send(f"220 Archivo".encode())  # Envía que es un archivo

    else:
        # Si la clave no se encuentra, envía un mensaje de error
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())

def manejar_comando_lista(nodo_dato: NodoDato, clave, socket_cliente):
    """Maneja el comando LIST, lista el contenido de una carpeta según la dirección dada."""
    if clave in nodo_dato.datos:
        dirs = nodo_dato.datos[clave][0]  # Obtiene los directorios de la clave

        try:
            # Envía el mensaje de éxito y la lista de sucesores
            socket_cliente.send(f"220 {' '.join(obtener_k_sucesores(nodo_dato))}".encode())
            respuesta = socket_cliente.recv(1024).decode().strip()  # Espera la respuesta del cliente

            if respuesta.startswith("220"):
                resultado = []

                # Intenta obtener la lista de directorios
                while True:
                    try:
                        resultado = list(dirs.values())  # Obtiene los valores de los directorios
                        break
                    except Exception as e:
                        if nodo_dato.verbose:
                            print(f"Error: {e}")

                # Envía la lista de directorios al cliente
                socket_cliente.sendall('\n'.join(resultado).encode('utf-8'))

                if nodo_dato.verbose:
                    print("Transferencia completa")

        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        # Si la clave no existe, envía un mensaje de error
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())

def manejar_comando_mkd(nodo_dato: NodoDato, clave, socket_cliente):
    """Crea una carpeta en la dirección solicitada."""
    if clave not in nodo_dato.datos:
        nodo_dato.datos[clave] = {}, 0  # Inicializa la carpeta como un diccionario vacío

        try:
            socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito

        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        # Si la carpeta ya existe, envía un mensaje de error
        socket_cliente.send(f"553 Acción solicitada no realizada: El archivo ya existe.".encode())

def manejar_comando_lectura(nodo_dato: NodoDato, clave, socket_cliente):
    """Maneja el comando READ, devuelve los elementos de un directorio."""
    if clave in nodo_dato.datos:
        dirs, _ = nodo_dato.datos[clave]  # Obtiene los directorios y su información

        try:
            items = []

            # Intenta obtener la lista de elementos en el directorio
            while True:
                try:
                    items = list(dirs.items())  # Obtiene los ítems del directorio
                    break
                except Exception as e:
                    if nodo_dato.verbose:
                        print(f"Error: {e}")

            carpetas = []
            archivos = []

            # Clasifica los ítems en carpetas y archivos
            for directorio, info in items:
                if info.startswith('drwxr-xr-x'):
                    carpetas.append(directorio)  # Es una carpeta
                else:
                    archivos.append(directorio)  # Es un archivo

            # Prepara la respuesta con el conteo de carpetas y listas
            directorios = '\n'.join([str(len(carpetas))] + carpetas + archivos)
            socket_cliente.send(f"220 {directorios}".encode())  # Envía la lista al cliente
        
        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        # Si la clave no existe, envía un mensaje de error
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())

def manejar_comando_rmd(nodo_dato: NodoDato, clave, socket_cliente):
    """Maneja el comando RMD, elimina un directorio."""
    if clave in nodo_dato.datos:
        dirs, version = nodo_dato.datos.pop(clave)  # Elimina el directorio y obtiene su versión
        nodo_dato.datos_eliminados[clave] = version  # Registra el directorio como eliminado

        try:
            items = []

            # Intenta obtener la lista de elementos en el directorio eliminado
            while True:
                try:
                    items = list(dirs.items())
                    break
                except Exception as e:
                    if nodo_dato.verbose:
                        print(f"Error: {e}")

            carpetas = []
            archivos = []

            # Clasifica los ítems en carpetas y archivos
            for directorio, info in items:
                if info.startswith('drwxr-xr-x'):
                    carpetas.append(directorio)  # Es una carpeta
                else:
                    archivos.append(directorio)  # Es un archivo

            # Prepara la respuesta con el conteo de carpetas y listas
            directorios = '\n'.join([str(len(carpetas))] + carpetas + archivos)
            socket_cliente.send(f"220 {directorios}".encode())  # Envía la lista al cliente

        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        # Si la clave no existe, envía un mensaje de error
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())

def manejar_comando_stor_dir(nodo_dato: NodoDato, folder, dirname, info, socket_cliente):
    """Almacena un directorio en la dirección solicitada."""
    if folder in nodo_dato.datos:
        dirs, version = nodo_dato.datos[folder]
        dirs[dirname] = info  # Añade el nuevo directorio

        nodo_dato.mutex_version.acquire()  # Bloquea el mutex para la versión
        nodo_dato.datos[folder] = dirs, version + 1  # Actualiza la versión
        nodo_dato.mutex_version.release()  # Libera el mutex

        try:
            socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito
            
        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        # Si la carpeta no existe, envía un mensaje de error
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())

def manejar_comando_dele_dir(nodo_dato: NodoDato, folder, dirname, socket_cliente):
    """Elimina un directorio en la dirección solicitada."""
    if folder in nodo_dato.datos:
        dirs, version = nodo_dato.datos[folder]
        dirs.pop(dirname)  # Elimina el directorio
        nodo_dato.mutex_version.acquire()  # Bloquea el mutex para la versión
        nodo_dato.datos[folder] = dirs, version + 1  # Actualiza la versión
        nodo_dato.mutex_version.release()  # Libera el mutex

        if nodo_dato.verbose:
            print(f"Se eliminó {dirname}")
        
        try:
            socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito
            
        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        # Si la carpeta no existe, envía un mensaje de error
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())

def manejar_comando_retr(nodo_dato: NodoDato, clave, idx, socket_cliente):
    """Recupera información de una dirección."""
    if clave in nodo_dato.datos:
        path = nodo_dato.datos[clave][0]  # Obtiene la ruta del archivo

        try:
            with open(path, "rb") as file:  # Modo binario
                size = os.stat(path).st_size  # Obtiene el tamaño del archivo

                if nodo_dato.verbose:
                    print(f"Tamaño del archivo: {size} bytes")

                socket_cliente.send(f"220 {size} {' '.join(obtener_k_sucesores(nodo_dato))}".encode())  # Envía el tamaño y sucesores

                respuesta = socket_cliente.recv(1024).decode().strip()  # Espera la respuesta del cliente

                if respuesta.startswith("220"):
                    file.seek(idx)  # Se posiciona en el índice
                    datos = file.read(4096)
                    count = 0

                    while datos:
                        socket_cliente.sendall(datos)  # Envía los datos al cliente
                        count += len(datos)
                        datos = file.read(4096)  # Lee más datos

                    if nodo_dato.verbose:
                        print("Transferencia completa")
        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        # Si la clave no existe, envía un mensaje de error
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())

def manejar_comando_stor(nodo_dato: NodoDato, clave, socket_cliente):
    """Almacena información en una dirección."""
    try:
        # Normaliza la ruta del directorio donde se almacenará la información
        path = os.path.normpath("/app/" + str(nodo_dato.identificador) + os.path.dirname(clave)[4:])
        os.makedirs(path, exist_ok=True)  # Crea el directorio si no existe

        path = os.path.normpath(path + "/" + clave[len(os.path.dirname(clave)):])  # Normaliza la ruta del archivo

        with open(path, "wb") as file:  # Modo binario
            socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito

            respuesta = socket_cliente.recv(1024).decode().strip()  # Espera la respuesta del cliente

            if respuesta.startswith("220"):
                while True:
                    datos = socket_cliente.recv(4096)  # Recibe datos del cliente

                    if not datos:
                        break  # Sale del bucle si no hay más datos

                    file.write(datos)  # Escribe los datos en el archivo
                
                # Actualiza la versión del archivo en el nodo
                nodo_dato.mutex_version.acquire()  # Bloquea el mutex para la versión
                nodo_dato.datos[clave] = path, (nodo_dato.datos[clave][1] + 1 if clave in nodo_dato.datos else 0)
                nodo_dato.mutex_version.release()  # Libera el mutex

    except Exception as e:
        if nodo_dato.verbose:
            print(f"Error: {e}")

def manejar_comando_dele(nodo_dato: NodoDato, clave, socket_cliente):
    """Maneja el comando DELE, elimina el archivo solicitado."""
    if clave in nodo_dato.datos:
        try:
            _, version = nodo_dato.datos.pop(clave)  # Elimina el archivo y obtiene su versión
            nodo_dato.datos_eliminados[clave] = version  # Registra el archivo como eliminado
            
            socket_cliente.send(f"220".encode())  # Envía un mensaje de éxito

        except Exception as e:
            if nodo_dato.verbose:
                print(f"Error: {e}")
    else:
        socket_cliente.send(f"550 Acción solicitada no realizada: Archivo no disponible o no encontrado.".encode())  # Envía un mensaje de error si no se encuentra el archivo