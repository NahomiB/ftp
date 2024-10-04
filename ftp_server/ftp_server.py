import datetime
import os
import platform
import random
import socket
import threading
import time
import uuid


# Constantes de manejo del servidor

NUMERO_DE_ESCUCHAS = 5

transferencia_en_progreso = False
cierre_en_progreso = False

def obtener_nodo_almacenamiento():
    return True

def encontrar_sucesor():
    return True

def actualizar_nodos_almacenamiento():
    return True

def gestionar_conexion_cliente(socket_cliente):
    """
    Gestiona la conexión de un cliente FTP, recibiendo comandos, interpretándolos 
    y enviando respuestas según la funcionalidad del servidor.
    """
    directorio_actual = os.path.normpath("/app")  # Directorio de trabajo inicial
    socket_datos = None  # Inicializar socket de datos

    try:
        while True:
            comando = socket_cliente.recv(1024).decode().strip()  # Recibir comando del cliente
            print(f"Comando recibido: {comando}")
            
            # Procesar el comando recibido
            if comando.startswith('USER'):
                gestionar_comando_usuario(socket_cliente)
            elif comando.startswith('PASS'):
                gestionar_comando_contrasenha(socket_cliente, comando)
            elif comando.startswith('ACCT'):
                gestionar_comando_cuenta(socket_cliente)
            elif comando.startswith('REIN'):
                gestionar_comando_reiniciar_sesion(socket_cliente)
            elif comando.startswith('QUIT'):
                gestionar_comando_logout(socket_cliente)
                
            # Comandos de navegación del sistema de archivos
            elif comando.startswith('CWD'):
                directorio_actual = gestionar_comando_cambiar_directorio(comando, directorio_actual, socket_cliente)
            elif comando.startswith('CDUP'):
                directorio_actual = gestionar_comando_cambiar_directorio("CWD ..", directorio_actual, socket_cliente)
            elif comando.startswith('SMNT'):
                gestionar_comando_no_implementado()
            
            
            # Comandos relacionados con la transferencia de archivos
            elif comando.startswith('PORT'):
                socket_datos = gestionar_comando_port(comando, socket_cliente)
            elif comando.startswith('TYPE'):
                tipo_transferencia = gestionar_comando_tipo_transferencia(socket_cliente, comando)
            elif comando.startswith('PASV'):
                socket_datos = gestionar_comando_pasivo(socket_cliente)
            elif comando.startswith('STRU'):
                estructura = gestionar_comando_estructura_archivo(socket_cliente, comando)
            elif comando.startswith('MODE'):
                modo = gestionar_comando_modo_transferencia(socket_cliente, comando)
            
            # Comandos relacionados con servicios de FTP
            elif comando.startswith('RETR'):
                gestionar_comando_descargar_archivo(comando[5:].strip(), socket_cliente, socket_datos, directorio_actual)
                socket_datos = None  # Cerrar socket de datos después de descarga
            elif comando.startswith('STOR'):
                gestionar_comando_subir_archivo(comando[5:].strip(), socket_cliente, socket_datos, directorio_actual)
                socket_datos = None
            elif comando.startswith('STOU'):
                # Se genera el nombre único en el momento
                gestionar_comando_subir_archivo(f"archivo_{uuid.uuid4().hex}", socket_cliente, socket_datos, directorio_actual)
                socket_datos = None
            elif comando.startswith('RNFR'):
                gestionar_comando_renombrar_archivo(comando[5:].strip(), socket_cliente, directorio_actual)
            elif comando.startswith('DELE'):
                gestionar_comando_eliminar_archivo(comando[5:].strip(), socket_cliente, directorio_actual)
            elif comando.startswith('RMD'):
                gestionar_comando_eliminar_directorio(comando[4:].strip(), socket_cliente, directorio_actual)
            elif comando.startswith('MKD'):
                gestionar_comando_crear_directorio(comando[4:].strip(), socket_cliente, directorio_actual)
            elif comando.startswith('PWD'):
                gestionar_comando_pwd(socket_cliente, directorio_actual)
            elif comando.startswith('NLST') or comando.startswith('LIST'):
                gestionar_comando_listado_directorio(socket_cliente, socket_datos, comando, directorio_actual)
                socket_datos = None  # Resetear socket de datos después de uso
            elif comando.startswith('SYST'):
                gestionar_comando_sistema(socket_cliente)        
            # Si el comando no es reconocido
            else:
                socket_cliente.send(b'503 Error de sintaxis, comando no reconocido.\r\n')
    except (ConnectionAbortedError, ConnectionResetError):
        print("Conexión perdida con el cliente.")
    finally:
        if socket_datos:
            socket_datos.close()
        socket_cliente.close()

# Funciones que gestionan comandos específicos del servidor FTP

def gestionar_comando_usuario(socket_cliente):
    """Responde al comando USER, autenticando al cliente sin requerir contraseña."""
    # Esta implementación se puede cambiar si se necesita un usuario para acceder a los datos.
    socket_cliente.send(b'230 Usuario autenticado.\r\n')
    
def gestionar_comando_contrasenha(socket_cliente, comando):
    """
    Maneja el comando PASS, extrayendo la contraseña y realizando la autenticación.
    """
    partes_comando = comando.split(' ', 1)  # Dividir el comando en dos partes: el comando y el resto
    contrasenha = partes_comando[1] if len(partes_comando) > 1 else ''  # Extraer la contraseña

    if contrasenha:  # Comprobar si la contraseña no está vacía
        socket_cliente.send(b'230 Contrasenha aceptada.\r\n')
        # Aquí es donde se debe mejorar la lógica para validar la contraseña si se quiere algo más robusto.
    else:
        socket_cliente.send(b'530 La contrasenha no puede estar vacia.\r\n')  # Enviar error si la contraseña está vacía
           
def gestionar_comando_cuenta(socket_cliente):
    """
    Maneja el comando ACCT, que en algunos sistemas FTP se usa para proporcionar información adicional 
    de la cuenta del usuario. En este caso, no se requiere autenticación adicional y el comando se considera innecesario.

    Envía una respuesta indicando que el comando no es necesario en este servidor.
    """
    socket_cliente.send(b'202 Comando no implementado, innecesario en este sitio.\r\n')
    
def gestionar_comando_reiniciar_sesion(socket_cliente):
    """
    Maneja el comando REIN (Reinitialize), que termina la sesión actual del usuario,
    restablece todos los parámetros a sus valores predeterminados y mantiene abierta la conexión de control.
    """
    try:
        # Restablecer todos los parámetros de la sesión a sus valores predeterminados
        # Se limpia la información de la sesión, eliminando usuario, contraseñas, etc.
        
        # En este caso no se realiza ninguna acción porque no se guardan datos relacionados con la sesión.

        # Enviar mensaje indicando que la sesión ha sido reiniciada y se espera el comando USER
        socket_cliente.send(b'220 Sesion reiniciada. Envie el comando USER para comenzar una nueva sesion.\r\n')
    
    except Exception as e:
        # Manejo de errores
        socket_cliente.send(b'550 Error al reiniciar la sesion.\r\n')

def gestionar_comando_logout(socket_cliente):
    """
    Maneja el comando QUIT (Logout), cerrando la sesión del usuario.
    """
    try:
        if transferencia_en_progreso:
            # Si hay una transferencia en progreso, se mantiene abierta la conexión de control
            cierre_en_progreso = True
            socket_cliente.send(b'226 Transferencia en progreso, la conexion se cerrara al finalizar.\r\n')
        else:
            # No hay transferencias, se puede cerrar la conexión de control
            socket_cliente.send(b'221 Sesion terminada. Cerrando conexion.\r\n')
            socket_cliente.close()  # Cierra la conexión de control
        
    except Exception as e:
        # Manejo de errores
        socket_cliente.send(b'550 Error al cerrar la sesion.\r\n')
        
def gestionar_comando_no_implementado(socket_cliente, comando):
    """
    Maneja comandos no implementados en el servidor FTP.
    """
    # Enviar un mensaje de error 502 (Command not implemented)
    respuesta = f'502 Comando "{comando}" no implementado.\r\n'
    socket_cliente.send(respuesta.encode('utf-8'))  # Enviar respuesta al cliente

def gestionar_comando_cambiar_directorio(comando, directorio_actual, socket_cliente):
    """
    Maneja el comando CWD, cambiando el directorio de trabajo actual. Retorna el nuevo directorio de trabajo si el cambio es exitoso, o el directorio actual si hay un error.
    """
    try:
        nuevo_directorio = os.path.normpath(comando[4:].strip())  # Extrae y normaliza el nuevo directorio del comando
        
        # Maneja el caso de '..' (directorio padre)
        if nuevo_directorio == "..":
            directorio_actual = os.path.dirname(directorio_actual)  # Cambia al directorio padre
        else:
            # Intenta crear el nuevo camino combinado del directorio actual con el nuevo
            directorio_potencial = os.path.normpath(os.path.join(directorio_actual, nuevo_directorio))
            
            # Verifica si el nuevo directorio existe y es accesible
            if os.path.isdir(directorio_potencial):
                directorio_actual = directorio_potencial
                socket_cliente.send(b'250 Directorio cambiado con exito.\r\n')
            else:
                socket_cliente.send(b'550 El directorio no existe o no es accesible.\r\n')
        
    except Exception as e:
        # Enviar un mensaje de error en caso de un problema inesperado
        socket_cliente.send(b'550 Error al cambiar de directorio.\r\n')

    return directorio_actual

def gestionar_comando_port(comando, cliente_socket):
    """
    Maneja el comando PORT, estableciendo una conexión entre el cliente y el servidor.
    """
    # Dividir el comando para obtener los componentes
    partes_direccion = comando.split()[1].split(',')
    
    direccion_ip = '.'.join(partes_direccion[:4])
    
    # Calcular el puerto a partir de las dos últimas partes del comando
    puerto_datos = int(partes_direccion[4]) * 256 + int(partes_direccion[5])

    try:
    # Crear un socket de datos para conectarse al cliente
        socket_datos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_datos.connect((direccion_ip, puerto_datos))
        
        # Enviar un mensaje 200 si la conexión fue exitosa
        cliente_socket.send(b'200 Comando PORT ejecutado con exito.\r\n')
        
    except socket.error:
        # Enviar un mensaje 425 si la conexión falla
        cliente_socket.send(b'425 No se pudo abrir la conexion de datos.\r\n')
        socket_datos = None  # Asegurarse de que el socket de datos no se use en caso de error

    return socket_datos
   
def gestionar_comando_pasivo(socket_cliente, rango_puertos=(40500, 40600)):
    """
    Maneja el comando PASV, creando un socket en un puerto dentro de un rango especificado
    y enviando al cliente la información sobre el modo pasivo.
    """

    # Intenta encontrar un puerto disponible dentro del rango especificado
    for puerto in random.sample(range(*rango_puertos), rango_puertos[1] - rango_puertos[0]):
        try:
            # Crear un socket para la conexión de datos
            socket_datos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_datos.bind(('0.0.0.0', puerto))  # Asigna el puerto disponible
            socket_datos.listen(1)  # Escucha conexiones entrantes
            break
        except OSError:
            continue  # Intenta con el siguiente puerto en caso de error
    else:
        # Si no se encontró un puerto disponible, lanza un error
        raise IOError("No hay puertos disponibles en el rango especificado")

    # Obtiene el número de puerto en el que está escuchando
    puerto = socket_datos.getsockname()[1]
    print(f"Escuchando en el puerto: {puerto}")

    # Prepara la dirección IP y la respuesta para el cliente
    ip = socket_cliente.getsockname()[0]  # Obtiene la dirección IP del servidor
    p1, p2 = divmod(puerto, 256)  # Calcula los bytes del puerto
    respuesta = f"227 Entrando en Modo Pasivo ({ip.replace('.', ',')},{p1},{p2}).\r\n"
    socket_cliente.send(respuesta.encode('utf-8'))  # Envía la respuesta al cliente

    # Acepta la conexión de datos del cliente
    socket_datos_cliente, addr = socket_datos.accept()
    print(f"Conexión de datos aceptada desde: {addr}")

    return socket_datos_cliente

def gestionar_comando_tipo_transferencia(socket_cliente, comando):
    """
    Maneja el comando TYPE, cambiando el tipo de transferencia según lo especificado en la sección de Representación y Almacenamiento de Datos.
    """

    # Definición de tipos de transferencia y su valor por defecto
    tipo_predeterminado = 'A N'  # ASCII No imprimible por defecto
    tipo_transferencia = tipo_predeterminado  # Inicializa con el tipo predeterminado

    # Procesa el comando TYPE
    partes_comando = comando.split()
    
    if len(partes_comando) == 2:  # Solo un parámetro (tipo)
        tipo_transferencia = partes_comando[1]
        
        if tipo_transferencia == 'I':
            socket_cliente.send(b'200 Tipo de transferencia: imagen.\r\n')
        elif tipo_transferencia == 'A':
            socket_cliente.send(b'200 Tipo de transferencia: ASCII.\r\n')
        elif tipo_transferencia == 'N':
            socket_cliente.send(b'200 Tipo de transferencia: no imprimible.\r\n')
        elif tipo_transferencia == 'E':
            socket_cliente.send(b'200 Tipo de transferencia: EBCDIC.\r\n')
        elif tipo_transferencia == 'L':
            socket_cliente.send(b'200 Tipo de transferencia: byte local.\r\n')
        else:
            socket_cliente.send(b'504 Comando no implementado.\r\n')
    
    elif len(partes_comando) == 3:  # Dos parámetros (tipo y segundo parámetro)
        tipo_transferencia = partes_comando[1]
        segundo_parametro = partes_comando[2]

        if tipo_transferencia == 'A':
            # Maneja ASCII con el segundo parámetro
            if segundo_parametro == 'T':
                socket_cliente.send(b'200 Tipo de transferencia: ASCII, efectores de formato Telnet.\r\n')
            else:
                socket_cliente.send(b'504 Comando no implementado.\r\n')
        elif tipo_transferencia == 'I':
            # Maneja el modo imagen
            socket_cliente.send(b'200 Tipo de transferencia: imagen.\r\n')
        elif tipo_transferencia == 'L':
            # Maneja el byte local y espera un tamaño
            try:
                tamaño_byte = int(segundo_parametro)
                socket_cliente.send(b'200 Tipo de transferencia: byte local de tamanho {}.\r\n'.format(tamaño_byte).encode('utf-8'))
            except ValueError:
                socket_cliente.send(b'501 Error en el tamanho del byte local.\r\n')
        else:
            socket_cliente.send(b'504 Comando no implementado.\r\n')

    else:
        socket_cliente.send(b'501 Sintaxis de comando invalida.\r\n')

    # Si se cambia solo el primer argumento a algo diferente a 'A', el formato vuelve al predeterminado
    if len(partes_comando) == 2 and partes_comando[1] != 'A':
        tipo_transferencia = tipo_predeterminado
        
    return tipo_transferencia

def gestionar_comando_estructura_archivo(socket_cliente, comando):
    """
    Responde al comando STRU, cambiando la estructura del archivo.
    La estructura predeterminada es File.
    """
    estructuras_permitidas = {
        'F': 'Archivo (sin estructura de registros)',
        'R': 'Estructura de registros',
        'P': 'Estructura de página'
    }
    
    # Estructura predeterminada
    estructura_actual = 'F'  # File

    # Procesa el comando STRU
    partes_comando = comando.split()

    if len(partes_comando) == 2:  # Un argumento
        estructura = partes_comando[1]
        
        if estructura in estructuras_permitidas:
            estructura_actual = estructura
            respuesta = f'200 Estructura del archivo cambiada a: {estructuras_permitidas[estructura]}.\r\n'
            socket_cliente.send(respuesta.encode('utf-8'))
        else:
            socket_cliente.send(b'504 Comando no implementado. Estructura no valida.\r\n')
    else:
        socket_cliente.send(b'501 Sintaxis de comando invalida.\r\n')
        
    return estructura_actual

def gestionar_comando_modo_transferencia(socket_cliente, comando):
    """
    Responde al comando MODE, cambiando el modo de transferencia de datos.
    El modo predeterminado es Stream.
    """
    modos_permitidos = {
        'S': 'Transmisión en flujo',
        'B': 'Bloque',
        'C': 'Comprimido'
    }
    
    # Modo predeterminado
    modo_actual = 'S'  # Stream

    # Procesa el comando MODE
    partes_comando = comando.split()

    if len(partes_comando) == 2:  # Un argumento
        modo = partes_comando[1]
        
        if modo in modos_permitidos:
            modo_actual = modo
            respuesta = f'200 Modo de transferencia cambiado a: {modos_permitidos[modo]}.\r\n'
            socket_cliente.send(respuesta.encode('utf-8'))
        else:
            socket_cliente.send(b'504 Comando no implementado. Modo no valido.\r\n')
    else:
        socket_cliente.send(b'501 Sintaxis de comando invalida.\r\n')

    return modo_actual

def gestionar_comando_descargar_archivo(nombre_archivo, socket_cliente, socket_datos, directorio_actual, ip_nodo=None, puerto_nodo=None):
    """
    Maneja el comando RETR, que transfiere una copia del archivo especificado al cliente.
    """
    
    ruta_completa = os.path.join(directorio_actual, nombre_archivo)

    try:
        while ip_nodo is None or puerto_nodo is None:
            ip_nodo, puerto_nodo = obtener_nodo_almacenamiento()

        # Encontrar el sucesor donde se almacena el archivo
        try:
            ip_nodo, puerto_nodo = encontrar_sucesor(ruta_completa, ip_nodo, puerto_nodo)
        except Exception as e:
            print(f"Error al encontrar el sucesor: {e}")
            gestionar_comando_descargar_archivo(nombre_archivo, socket_cliente, socket_datos, directorio_actual)
            return

        # Conectar al nodo donde se encuentra el archivo
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_nodo:
            socket_nodo.connect((ip_nodo, puerto_nodo))
            print(f"Conexión establecida con el nodo {ip_nodo}:{puerto_nodo}")
            socket_nodo.sendall(f"RETR 0 {ruta_completa}".encode())

            respuesta = socket_nodo.recv(1024).decode().strip()

            if respuesta.startswith("220"):
                parametros = respuesta[4:].strip().split(" ")
                tamaño_archivo = int(parametros[0])

                nodos_auxiliares = [direccion.split(":") for direccion in parametros[1:]] if len(parametros) > 1 else []

                if socket_cliente:
                    socket_cliente.send(b"150 Abriendo conexion de datos en modo binario.\r\n")

                    contador_bytes = 0
                    socket_nodo.send(b"220 Ok")

                    while contador_bytes < tamaño_archivo:
                        try:
                            datos = socket_nodo.recv(4096)
                            if not datos:
                                break
                        except Exception as e:
                            print(f"Error al recibir datos: {e}")
                            if not nodos_auxiliares:
                                cerrar_conexion_y_enviar_error(socket_nodo, socket_cliente)
                                return

                            while nodos_auxiliares:
                                ip_aux, puerto_aux = nodos_auxiliares.pop(0)
                                if reintentar_conexion(socket_nodo, ip_aux, puerto_aux, contador_bytes, ruta_completa):
                                    break
                            continue

                        socket_datos.sendall(datos)
                        contador_bytes += len(datos)

                    print("Transferencia completada.")
                    if socket_cliente:
                        socket_cliente.send(b"226 Transferencia completa.\r\n")

                elif respuesta.startswith("550"):
                    ip_aux, puerto_aux = respuesta.split(" ")[1].split(":")
                    gestionar_comando_descargar_archivo(nombre_archivo, socket_cliente, socket_datos, directorio_actual, ip_aux, int(puerto_aux))
                    return

                else:
                    socket_cliente.send(b"550 Archivo no encontrado.\r\n")

    except Exception as e:
        print(f"Se ha producido un error: {e}")
        if socket_cliente:
            socket_cliente.send(b"451 Accion abortada: error local en el procesamiento.\r\n")
            
    socket_datos.close()

def reintentar_conexion(socket_nodo, ip_aux, puerto_aux, contador_bytes, ruta_archivo):
    """
    Intenta reconectar a un nodo auxiliar para continuar la descarga.
    """
    try:
        socket_nodo.close()
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((ip_aux, puerto_aux))
        
        print(f"Conexión establecida con el nodo auxiliar {ip_aux}:{puerto_aux}")
        
        socket_nodo.sendall(f"RETR {contador_bytes} {ruta_archivo}".encode())

        respuesta = socket_nodo.recv(1024).decode().strip()
        if respuesta.startswith("220"):
            socket_nodo.send(b"220 Ok")
            return True
        
    except Exception as e:
        print(f"Error al conectarse al nodo auxiliar: {e}")
    
    return False

def cerrar_conexion_y_enviar_error(socket_nodo, socket_cliente):
    """
    Cierra la conexión y envía un mensaje de error al cliente.
    """
    socket_nodo.close()
    if socket_cliente:
        socket_cliente.send(b"451 Accion abortada: error local en el procesamiento.\r\n")

def gestionar_comando_subir_archivo(nombre_archivo, socket_cliente, socket_datos, directorio_actual, ip_nodo=None, puerto_nodo=None):
    
    ruta_archivo = os.path.join(directorio_actual, nombre_archivo)

    try:
        while ip_nodo is None or puerto_nodo is None:
            ip_nodo, puerto_nodo = obtener_nodo_almacenamiento()

        # Localizar el sucesor donde se debe guardar el archivo
        ip_nodo, puerto_nodo = encontrar_sucesor(ruta_archivo, ip_nodo, puerto_nodo)

        # Establecer conexión con el nodo
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_nodo:
            socket_nodo.connect((ip_nodo, puerto_nodo))
            print(f"Conectado a {ip_nodo}:{puerto_nodo}")
            socket_nodo.sendall(f"STOR {ruta_archivo}".encode())

            respuesta = socket_nodo.recv(1024).decode().strip()

            if respuesta.startswith("220"):
                if socket_cliente:
                    socket_cliente.send(b"150 Abriendo conexion de datos en modo binario para la transferencia del archivo.\r\n")

                socket_nodo.send(b"220 Ok")

                contador_bytes = 0
                while True:
                    datos = socket_datos.recv(4096)
                    if not datos:
                        break
                    socket_nodo.sendall(datos)
                    contador_bytes += len(datos)

                # Proceso de cierre y confirmación
                if registrar_archivo_stor(nombre_archivo, f"-rw-r--r-- 1 0 0 {contador_bytes} {datetime.now().strftime('%b %d %H:%M')} {os.path.basename(nombre_archivo)}", directorio_actual):
                    if socket_cliente:
                        socket_cliente.send(b"226 Transferencia completa.\r\n")
                    print("Transferencia completa.")
                else:
                    if socket_cliente:
                        socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")
                    print("Error al registrar el archivo.")

            elif respuesta.startswith("550"):
                ip_aux, puerto_aux = respuesta.split(" ")[1].split(":")
                gestionar_comando_subir_archivo(nombre_archivo, socket_cliente, socket_datos, directorio_actual, ip_aux, int(puerto_aux))
                return

    except Exception as e:
        print(f"Se ha producido un error: {e}")
        if socket_cliente:
            socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")
        else:
            raise e

def registrar_archivo_stor(nombre_directorio, info_archivo, directorio_actual, ip_nodo=None, puerto_nodo=None):
    """
    Inserta un archivo en la lista de la carpeta padre.
    """
    
    # Normaliza la ruta del directorio
    ruta_directorio = os.path.normpath(os.path.join(directorio_actual, nombre_directorio))

    try:
        # Obtener nodo de almacenamiento si no se especifica
        while ip_nodo is None or puerto_nodo is None:
            ip_nodo, puerto_nodo = obtener_nodo_almacenamiento()

        # Localizar el sucesor para el directorio actual
        ip_nodo, puerto_nodo = encontrar_sucesor(directorio_actual, ip_nodo, puerto_nodo)

        # Establecer conexión con el nodo de almacenamiento
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_nodo:
            socket_nodo.connect((ip_nodo, puerto_nodo))
            print(f"Conectado a {ip_nodo}:{puerto_nodo}")

            # Preparar el comando STORDIR
            longitud_directorio = len(directorio_actual) + 1
            longitud_ruta = longitud_directorio + len(ruta_directorio) + 1
            comando = f"STORDIR {longitud_directorio} {longitud_ruta} {directorio_actual} {ruta_directorio} {info_archivo}"
            socket_nodo.sendall(comando.encode())

            # Esperar la respuesta del nodo
            respuesta = socket_nodo.recv(1024).decode().strip()

            # Manejar la respuesta
            if respuesta.startswith("220"):
                print("Archivo insertado correctamente.")
                return True
            
            elif respuesta.startswith("550"):
                ip_aux, puerto_aux = respuesta.split(" ")[1].split(":")
                return registrar_archivo_stor(nombre_directorio, info_archivo, directorio_actual, ip_aux, int(puerto_aux))

            else:
                print("Error inesperado al insertar el archivo.")
                return False

    except Exception as e:
        print(f"Se ha producido un error: {e}")
        return False

def gestionar_comando_eliminar_archivo(nombre_archivo, socket_cliente, directorio_actual, ip_nodo=None, puerto_nodo=None):
    """Respuesta para el comando DELE, busca el nodo donde se encuentra el archivo especificado y, si lo encuentra, lo elimina de ese nodo."""
    ruta_archivo = os.path.join(directorio_actual, nombre_archivo)

    try:
        # Obtener el nodo de almacenamiento si no se ha especificado
        while ip_nodo is None or puerto_nodo is None:
            ip_nodo, puerto_nodo = obtener_nodo_almacenamiento()

        # Encontrar el sucesor donde se almacena el archivo
        try:
            ip_nodo, puerto_nodo = encontrar_sucesor(ruta_archivo, ip_nodo, puerto_nodo)
        except Exception as e:
            print(f"Error al encontrar el sucesor: {e}")
            gestionar_comando_eliminar_archivo(nombre_archivo, socket_cliente, directorio_actual)
            return

        # Conectar al nodo donde se encuentra el archivo
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((ip_nodo, puerto_nodo))

        print(f"Conectado a {ip_nodo}:{puerto_nodo}")
        socket_nodo.sendall(f"DELE {ruta_archivo}".encode())

        # Recibir respuesta del nodo
        respuesta = socket_nodo.recv(1024).decode().strip()

        if respuesta.startswith("220"):
            socket_nodo.close()

            if enviar_comando_eliminar_dir(nombre_archivo, directorio_actual) and socket_cliente:
                socket_cliente.send(b"250 Archivo eliminado exitosamente.\r\n")
            elif socket_cliente:
                socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")

        elif respuesta.startswith("550"):
            ip, puerto = respuesta.split(" ")[1].split(":")
            socket_nodo.close()
            gestionar_comando_eliminar_archivo(nombre_archivo, socket_cliente, directorio_actual, ip, int(puerto))
            return

        elif socket_cliente:
            socket_cliente.send(b"550 Archivo no encontrado.\r\n")

    except Exception as e:
        print(f"Error: {e}")
        if socket_cliente:
            socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")

def enviar_comando_eliminar_dir(nombre_directorio, directorio_actual, ip_nodo=None, puerto_nodo=None):
    """Elimina un archivo de la lista de la carpeta padre."""
    ruta_directorio = os.path.normpath(os.path.join(directorio_actual, nombre_directorio))

    try:
        # Obtener el nodo de almacenamiento si no se ha especificado
        while ip_nodo is None or puerto_nodo is None:
            ip_nodo, puerto_nodo = obtener_nodo_almacenamiento()

        # Encontrar el sucesor donde se debe eliminar el archivo
        try:
            ip_nodo, puerto_nodo = encontrar_sucesor(directorio_actual, ip_nodo, puerto_nodo)
        except Exception as e:
            print(f"Error al encontrar el sucesor: {e}")
            return enviar_comando_eliminar_dir(nombre_directorio, directorio_actual)

        # Conectar al nodo correspondiente
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((ip_nodo, puerto_nodo))
        
        print(f"Conectado a {ip_nodo}:{puerto_nodo}")
        
        # Enviar el comando DELEDIR con la longitud del directorio actual y las rutas
        socket_nodo.sendall(f"DELEDIR {len(directorio_actual) + 1} {directorio_actual} {ruta_directorio}".encode())

        # Recibir respuesta del nodo
        respuesta = socket_nodo.recv(1024).decode().strip()

        if respuesta.startswith("220"):
            socket_nodo.close()
            return True

        elif respuesta.startswith("550"):
            ip, puerto = respuesta.split(" ")[1].split(":")
            socket_nodo.close()
            return enviar_comando_eliminar_dir(nombre_directorio, directorio_actual, ip, int(puerto))
        
        else:
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

def gestionar_comando_renombrar_archivo(nombre_antiguo, socket_cliente, directorio_actual, ip_nodo=None, puerto_nodo=None):
    """Maneja el comando RNFR para renombrar un directorio."""
    ruta_directorio = os.path.join(directorio_actual, nombre_antiguo)

    try:
        while ip_nodo is None or puerto_nodo is None:
            ip_nodo, puerto_nodo = obtener_nodo_almacenamiento()

        try:
            ip_nodo, puerto_nodo = encontrar_sucesor(ruta_directorio, ip_nodo, puerto_nodo)
        except:
            gestionar_comando_renombrar_archivo(nombre_antiguo, socket_cliente, directorio_actual)
            return
        
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((ip_nodo, puerto_nodo))
        
        print(f"Conectado a {ip_nodo}:{puerto_nodo}")
        
        socket_nodo.sendall(f"ED {ruta_directorio}".encode())

        respuesta = socket_nodo.recv(1024).decode().strip()
        
        socket_nodo.close()

        if respuesta.startswith("220"):
            tipo = respuesta[4:]
            
            socket_cliente.send(b"350 Accion de archivo solicitada pendiente de mas informacion.\r\n")

            respuesta = socket_cliente.recv(1024).decode().strip()

            if respuesta.startswith("RNTO"):
                nuevo_nombre = respuesta[5:]
                nueva_ruta = os.path.join(directorio_actual, nuevo_nombre)
                
                if tipo == "Archivo":
                    if duplicar_archivo(ruta_directorio, nueva_ruta):
                        gestionar_comando_eliminar_archivo(os.path.basename(ruta_directorio), None, os.path.normpath(os.path.dirname(ruta_directorio)))
                        socket_cliente.send(b"250 Accion de archivo solicitada, completada.\r\n")
                    else:
                        socket_cliente.send(b"550 Accion solicitada abortada: error local en el procesamiento.\r\n")
                
                elif tipo == "Carpeta":
                    if duplicar_carpeta(ruta_directorio, nueva_ruta):
                        gestionar_comando_eliminar_directorio(os.path.basename(ruta_directorio), None, os.path.normpath(os.path.dirname(ruta_directorio)))
                        socket_cliente.send(b"250 Accion de archivo solicitada, completada.\r\n")
                    else:
                        socket_cliente.send(b"550 Accion solicitada abortada: error local en el procesamiento.\r\n")

        else:
            socket_cliente.send(b"550 Accion solicitada no realizada.\r\n")

    except Exception as e:
        print(f"Error: {e}")
        socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")

def duplicar_archivo(archivo_origen, archivo_destino):
    """Copia un archivo a una nueva ubicación."""
    try:
        socket_vinculado = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_vinculado.bind(('0.0.0.0', 0))
        socket_vinculado.listen(1)

        socket_salida = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        entrada_paquete = [None]

        def aceptar_conexion():
            entrada_paquete[0] = socket_vinculado.accept()[0]

        threading.Thread(target=aceptar_conexion, args=()).start()

        socket_salida.connect((obtener_ip_host(), socket_vinculado.getsockname()[1]))

        time.sleep(1)
        socket_vinculado.close()
        socket_entrada = entrada_paquete[0]

        finalizado_retr = [False]
        finalizado_stor = [False]

        def retr():
            gestionar_comando_descargar_archivo(os.path.basename(archivo_origen), None, socket_entrada, os.path.dirname(archivo_origen))
            socket_entrada.close()
            finalizado_retr[0] = True

        def stor():
            gestionar_comando_subir_archivo(os.path.basename(archivo_destino), None, socket_salida, os.path.dirname(archivo_destino))
            socket_salida.close()
            finalizado_stor[0] = True

        threading.Thread(target=retr, args=()).start()
        threading.Thread(target=stor, args=()).start()
    
        while (not finalizado_retr[0]) or (not finalizado_stor[0]):
            pass

        return True
    except:
        return False

def obtener_ip_host():
    """Obtiene la dirección IP de la máquina local."""
    try:
        # Crear un socket UDP
        socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Conectar a un servidor DNS público para determinar la IP local
        socket_udp.connect(("8.8.8.8", 80))
        ip_local = socket_udp.getsockname()[0]
    except Exception as e:
        print(f"Error al obtener la IP: {e}")
        ip_local = None  # Manejo de errores para devolver None si falla
    finally:
        socket_udp.close()  # Asegurarse de cerrar el socket

    return ip_local

def duplicar_carpeta(origen_carpeta, destino_carpeta):
    """Crea una copia de una carpeta en una nueva ubicación."""
    gestionar_comando_crear_directorio(os.path.basename(destino_carpeta), None, os.path.dirname(destino_carpeta))

    try:
        nodo_ip, nodo_puerto = None, None

        # Obtener el nodo de almacenamiento
        while nodo_ip is None or nodo_puerto is None:
            nodo_ip, nodo_puerto = obtener_nodo_almacenamiento()

        # Buscar el sucesor de la carpeta
        try:
            nodo_ip, nodo_puerto = encontrar_sucesor(origen_carpeta, nodo_ip, nodo_puerto)
        except:
            return duplicar_carpeta(origen_carpeta, destino_carpeta)

        # Conectar al nodo correspondiente
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((nodo_ip, nodo_puerto))
        
        print(f"Conectado a {nodo_ip}:{nodo_puerto}")
        
        # Enviar comando para leer el contenido de la carpeta
        socket_nodo.sendall(f"LEER {origen_carpeta}".encode())

        respuesta = socket_nodo.recv(1024).decode().strip()
        print(respuesta)

        socket_nodo.close()

        if respuesta.startswith("220"):
            lineas = respuesta[4:].split("\n")
            cantidad_carpetas = int(lineas[0])

            subcarpetas = lineas[1:cantidad_carpetas + 1] if cantidad_carpetas > 0 else []
            archivos = lineas[cantidad_carpetas + 1:] if len(lineas) > cantidad_carpetas + 1 else []

            for subcarpeta in subcarpetas:
                print(f"Duplicar {subcarpeta} a {os.path.join(destino_carpeta, os.path.basename(subcarpeta))}")

                if not duplicar_carpeta(subcarpeta, os.path.join(destino_carpeta, os.path.basename(subcarpeta))):
                    return False
                
            for archivo in archivos:
                print(f"Duplicar {archivo} a {os.path.join(destino_carpeta, os.path.basename(archivo))}")
                
                if not duplicar_archivo(archivo, os.path.join(destino_carpeta, os.path.basename(archivo))):
                    return False    
                
            return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def gestionar_comando_eliminar_directorio(nombre_directorio, socket_cliente, directorio_actual, nodo_ip=None, nodo_puerto=None):
    """Responde al comando RMD; busca el nodo donde debe estar el directorio solicitado y lo elimina si lo encuentra."""
    ruta_directorio = os.path.normpath(os.path.join(directorio_actual, nombre_directorio))

    try:
        # Obtener nodo de almacenamiento si no se proporciona
        while nodo_ip is None or nodo_puerto is None:
            nodo_ip, nodo_puerto = obtener_nodo_almacenamiento()

        try:
            nodo_ip, nodo_puerto = encontrar_sucesor(ruta_directorio, nodo_ip, nodo_puerto)
        except Exception:
            gestionar_comando_eliminar_directorio(nombre_directorio, socket_cliente, directorio_actual)
            return

        # Conectar al nodo
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((nodo_ip, nodo_puerto))

        print(f"Conectado a {nodo_ip}:{nodo_puerto}")
        
        # Enviar comando para eliminar directorio
        socket_nodo.sendall(f"RMD {ruta_directorio}".encode())
        respuesta = socket_nodo.recv(1024).decode().strip()

        if respuesta.startswith("220"):
            socket_nodo.close()
            lineas = respuesta[4:].split("\n")
            contador_directorios = int(lineas[0])

            directorios = lineas[1:contador_directorios + 1] if contador_directorios > 0 else []
            archivos = lineas[contador_directorios + 1:] if len(lineas) > contador_directorios + 1 else []

            # Eliminar subdirectorios
            for directorio in directorios:
                print(f"RMD {directorio}")
                gestionar_comando_eliminar_directorio(directorio, None, os.path.normpath(os.path.dirname(directorio)))
                
            # Eliminar archivos en el directorio
            for archivo in archivos:
                print(f"DELE {archivo}")
                gestionar_comando_eliminar_archivo(archivo, None, os.path.normpath(os.path.dirname(archivo)))

            # Eliminar el directorio principal
            if enviar_comando_eliminar_dir(ruta_directorio, directorio_actual) and socket_cliente:
                socket_cliente.send(f'250 "{ruta_directorio}" eliminado.\r\n'.encode())

        elif respuesta.startswith("550"):
            ip, puerto = respuesta.split(" ")[1].split(":")
            socket_nodo.close()
            gestionar_comando_eliminar_directorio(nombre_directorio, socket_cliente, directorio_actual, ip, int(puerto))
            return
        
        else:
            if socket_cliente:
                socket_cliente.send(b"550 El directorio no existe.\r\n")

    except Exception as e:
        print(f"Error: {e}")
        if socket_cliente:
            socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")

def gestionar_comando_crear_directorio(nombre_directorio, socket_cliente, directorio_actual, nodo_ip=None, nodo_puerto=None):
    """Responde al comando MKD; crea un nuevo directorio en el servidor en la ruta actual con el nombre especificado en nombre_directorio.
       Esta información se almacena en el nodo adecuado."""
    ruta_nuevo_directorio = os.path.normpath(os.path.join(directorio_actual, nombre_directorio))

    try:
        # Obtener nodo de almacenamiento si no se proporciona
        while nodo_ip is None or nodo_puerto is None:
            nodo_ip, nodo_puerto = obtener_nodo_almacenamiento()

        try:
            nodo_ip, nodo_puerto = encontrar_sucesor(ruta_nuevo_directorio, nodo_ip, nodo_puerto)
        except Exception:
            gestionar_comando_crear_directorio(nombre_directorio, socket_cliente, directorio_actual)
            return

        # Conectar al nodo
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((nodo_ip, nodo_puerto))
        
        print(f"Conectado a {nodo_ip}:{nodo_puerto}")
        
        # Enviar comando para crear directorio
        socket_nodo.sendall(f"MKD {ruta_nuevo_directorio}".encode())
        respuesta = socket_nodo.recv(1024).decode().strip()

        if respuesta.startswith("220"):
            socket_nodo.close()

            # Enviar comando para almacenar información del directorio
            if registrar_archivo_stor(nombre_directorio, f"drwxr-xr-x 1 0 0 0 {datetime.now().strftime('%b %d %H:%M')} {os.path.basename(nombre_directorio)}", directorio_actual):
                if socket_cliente:
                    socket_cliente.send(f'257 "{ruta_nuevo_directorio}" creado.\r\n'.encode())
            else:
                if socket_cliente:
                    socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")

        elif respuesta.startswith("550"):
            ip, puerto = respuesta.split(" ")[1].split(":")
            socket_nodo.close()
            gestionar_comando_crear_directorio(nombre_directorio, socket_cliente, directorio_actual, ip, int(puerto))
            return
        
        else:
            if socket_cliente:
                socket_cliente.send(b"550 El directorio ya existe.\r\n")

    except Exception as e:
        print(f"Error: {e}")
        if socket_cliente:
            socket_cliente.send(b"451 Accion solicitada abortada: error local en el procesamiento.\r\n")

def gestionar_comando_sistema(socket_cliente):
    """Responde al comando SYST, indicando el tipo de sistema operativo del servidor."""
    sistema_operativo = platform.system()  # Obtiene el sistema operativo
    version = platform.release()            # Obtiene la versión del sistema operativo
    
    # Formato de respuesta personalizado
    respuesta = f'215 {sistema_operativo} Type: {version}\r\n'
    socket_cliente.send(respuesta.encode())

def gestionar_comando_pwd(socket_cliente, directorio_actual):
    """Responde al comando PWD, enviando el directorio de trabajo actual."""
    socket_cliente.send(f'257 "{directorio_actual}" es el directorio actual.\r\n'.encode())

def gestionar_comando_listado_directorio(socket_cliente, socket_datos, comando, directorio_actual):
    """
    Responde a los comandos NLST y LIST, enviando la lista de archivos en el directorio actual.
    Si se proporciona un socket de datos, se envía el listado a través de él.
    """
    if not socket_datos:
        return  # Si no hay socket de datos, no hacemos nada

    # Procesar el comando y determinar el directorio
    argumentos = comando.split()
    if len(argumentos) == 1:
        directorio = directorio_actual
    else:
        directorio = os.path.normpath(argumentos[1])
    
    # Enviar el listado del directorio
    enviar_listado_directorio(socket_cliente, socket_datos, directorio)
    
    # Cerrar el socket de datos
    try:
        socket_datos.close()
    except Exception as e:
        print(f"Error al cerrar el socket de datos: {e}")

def enviar_listado_directorio(socket_cliente, socket_datos, directorio_actual, nodo_ip=None, nodo_puerto=None):

    try:
        # Asegurarse de obtener la dirección del nodo
        while nodo_ip is None or nodo_puerto is None:
            nodo_ip, nodo_puerto = obtener_nodo_almacenamiento()

        # Encontrar el sucesor del directorio actual
        try:
            nodo_ip, nodo_puerto = encontrar_sucesor(directorio_actual, nodo_ip, nodo_puerto)
        except:
            enviar_listado_directorio(socket_cliente, socket_datos, directorio_actual)
            return

        # Crear socket para conectarse al nodo
        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_nodo.connect((nodo_ip, nodo_puerto))
        
        print(f"Conectado a {nodo_ip}:{nodo_puerto}")
        
        socket_nodo.sendall(f"LIST {directorio_actual}".encode())

        respuesta = socket_nodo.recv(1024).decode().strip()

        if respuesta.startswith("220"):
            socket_cliente.send(b"150 Aqui viene el listado del directorio.\r\n")

            direcciones = respuesta[4:].split(" ") if len(respuesta) > 4 else []
            nodos_auxiliares = [(direccion.split(":")[0], int(direccion.split(":")[1])) for direccion in direcciones]

            socket_nodo.send(b"220 Ok")

            datos = ""

            while True:
                try:
                    trozo = socket_nodo.recv(4096).decode('utf-8')
                except:
                    if not nodos_auxiliares:
                        socket_nodo.close()
                        socket_cliente.send(b"451 Solicitud abortada: error local en el procesamiento.\r\n")
                        return

                    # Cambiar al siguiente nodo auxiliar si hay errores
                    while nodos_auxiliares:
                        socket_nodo.close()
                        ip, puerto = nodos_auxiliares.pop(0)

                        socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        try:
                            socket_nodo.connect((ip, puerto))
                            print(f"Conectado auxiliar a {ip}:{puerto}")
            
                            socket_nodo.sendall(f"LIST {directorio_actual}".encode())
                            respuesta = socket_nodo.recv(1024).decode().strip()

                            if respuesta.startswith("220"):
                                direcciones = respuesta[4:].split(" ") if len(respuesta) > 4 else []
                                nodos_auxiliares += [(direccion.split(":")[0], int(direccion.split(":")[1])) for direccion in direcciones]
                                
                                socket_nodo.send(b"220 Ok")

                                datos = ""
                                break

                            elif respuesta.startswith("550"):
                                ip, puerto = respuesta.split(" ")[1].split(":")
                                nodos_auxiliares.append((ip, int(puerto)))

                        except:
                            pass

                    continue

                if trozo:
                    datos += trozo
                else:
                    break
            
            socket_datos.sendall(datos.encode('utf-8'))

            socket_nodo.close()
            socket_cliente.send(b"226 Transferencia de directorio completada.\r\n")
            print("Transferencia completa")

        elif respuesta.startswith("550"):
            ip, puerto = respuesta.split(" ")[1].split(":")
            socket_nodo.close()
            enviar_listado_directorio(socket_cliente, socket_datos, directorio_actual, ip, int(puerto))
            return
        
        else:
            socket_cliente.send(b"550 Fallo al listar el directorio.\r\n")

    except Exception as e:
        print(f"Error: {e}")
        socket_cliente.send(b"451 Solicitud abortada: error local en el procesamiento.\r\n")

def manejar_conexiones_entrantes(servidor_socket):
    """
    Espera conexiones entrantes de los clientes FTP y lanza un nuevo hilo para cada cliente.
    """
    print("Servidor FTP en espera de conexiones...")
    while True:
        # Acepta una nueva conexión
        cliente_socket, direccion_cliente = servidor_socket.accept()
        print(f"Nueva conexión aceptada desde: {direccion_cliente}")
        
        # Envía mensaje de bienvenida al cliente
        cliente_socket.send(b"220 Bienvenido al servidor FTP.\r\n")
        
        # Crea un nuevo hilo para manejar la conexión del cliente
        hilo_cliente = threading.Thread(target=gestionar_conexion_cliente, args=(cliente_socket,))
        hilo_cliente.daemon = True  # Permite que el hilo se cierre cuando el programa principal termina
        hilo_cliente.start()
        
def configurar_socket_servidor(host='0.0.0.0', puerto=21):
    """
    Configura el socket de control del servidor FTP para aceptar conexiones de clientes.
    
    Parámetros:
    host -- Dirección IP en la que el servidor escucha (por defecto '0.0.0.0', todas las interfaces)
    puerto -- Puerto en el que el servidor escucha (por defecto 21, puerto FTP estándar)
    
    Retorna:
    server_socket -- El socket configurado para aceptar conexiones de clientes
    """
    try:
        # Crear un socket TCP/IP
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Vincular el socket a la dirección y puerto proporcionados
        servidor.bind((host, puerto))
    except OSError:
        # Si el puerto no está disponible, asignar uno dinámicamente
        print("El puerto especificado no está disponible, asignando un puerto dinámico.")
        servidor.bind((host, 0))

    # Escuchar hasta 5 conexiones entrantes
    servidor.listen(NUMERO_DE_ESCUCHAS)
    
    # Obtener el puerto final en el que está escuchando el servidor
    puerto_final = servidor.getsockname()[1]
    print(f"Servidor escuchando en {host}:{puerto_final}")
    
    return servidor
    
def iniciar_servidor_ftp():
    """
    Configura el servidor FTP y comienza a aceptar conexiones entrantes.
    """
    # Inicializa el socket de control para manejar las conexiones de los clientes
    servidor_socket = configurar_socket_servidor()
    
    # Lanza un hilo separado para mantener la lista de nodos de almacenamiento actualizada
    hilo_nodos_almacenamiento = threading.Thread(target=actualizar_nodos_almacenamiento)
    hilo_nodos_almacenamiento.daemon = True  # Hace que el hilo termine cuando el programa termina
    hilo_nodos_almacenamiento.start()
    
    # Comienza a aceptar conexiones de clientes
    manejar_conexiones_entrantes(servidor_socket)

if __name__ == "__main__":
    iniciar_servidor_ftp()
