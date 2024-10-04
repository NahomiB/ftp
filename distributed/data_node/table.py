from control import configurar_socket_control
import json
import os
import socket
import threading
import time
from utils import funcion_hash, obtener_id, encontrar_sucesor, obtener_ip_host, hacer_ping_nodo


class NodoDato:
    def __init__(self, puerto=0):
        # Configurar el socket de control
        self.socket, self.host, self.puerto = configurar_socket_control(puerto)
        
        # Generar el identificador usando la función hash
        self.identificador = funcion_hash(obtener_id(self.host, self.puerto))
        
        # Inicializar estructuras de datos
        self.datos = {}
        self.datos_eliminados = {}
        self.tabla_fingers_mayor = []
        self.tabla_fingers_menor = []
        
        # Inicializar predecesor y sucesores
        self.predecesor = None
        self.sucesores = []
        self.sucesor = None
        self.k_sucesores = 3
        
        # Inicializar mutex y contadores para operaciones de lectura
        self.mutex_lectura = threading.Lock()
        self.contador_lectura = 0
        self.actualizando = False
        
        # Mutex para unirse a la red
        self.mutex_union = threading.Lock()
        
        # Hilo para actualizaciones
        self.hilo_actualizacion = threading.Thread(target=actualizar, args=(self,))
        self.detener_actualizacion = False
        self.termino_primera_actualizacion = False
        
        # Verbosidad
        self.verbose = True
        self.verbose_actualizacion = True
        
        # Hilo para el listener de broadcast
        self.hilo_listener_broadcast = threading.Thread(target=escuchador_broadcast, args=(self,))
        
        # Mutex para el sucesor
        self.mutex_sucesor = threading.Lock()
        
        # Hilo para verificar el sucesor más cercano
        self.hilo_verificar_sucesor_cercano = threading.Thread(target=verificar_sucesor_mas_cercano, args=(self,))
        
        # Mutex para el predecesor
        self.mutex_predecesor = threading.Lock()
        
        # Hilo para verificar datos no poseídos
        self.hilo_verificar_datos_no_poseidos = threading.Thread(target=verificar_datos_sin_propietarios, args=(self,))
        
        # Mutex para la versión
        self.mutex_version = threading.Lock()


# Obtener el identificador del sucesor de un nodo en una tabla de dedos
def obtener_sucesor_tabla(tabla_dedos, id):
    # Recorrer la tabla de dedos
    for i in range(len(tabla_dedos)):
        # Verificar si el identificador del dedo es mayor que el id del nodo
        if tabla_dedos[i][0] > id:
            # Obtener el índice del sucesor (anterior al encontrado)
            indice = max(i - 1, 0)
            return (tabla_dedos[indice][1], tabla_dedos[indice][2])

    # Si no se encontró un sucesor, devolver el último elemento de la tabla
    indice = len(tabla_dedos) - 1
    return (tabla_dedos[indice][1], tabla_dedos[indice][2])


def encontrar_sucesor_tabla(nodo_dato: NodoDato, id):
    # Esperar hasta que no esté actualizando
    while nodo_dato.actualizando:
        pass

    # Adquirir el mutex de lectura
    nodo_dato.mutex_lectura.acquire()
    nodo_dato.contador_lectura += 1
    nodo_dato.mutex_lectura.release()

    # Lógica para encontrar el sucesor en la tabla de dedos
    if len(nodo_dato.tabla_fingers_mayor) == 0 and len(nodo_dato.tabla_fingers_menor) == 0:
        # Si no hay dedos, devolver el sucesor o la dirección del nodo
        resultado = (nodo_dato.sucesor[1], nodo_dato.sucesor[2]) if nodo_dato.sucesor else (nodo_dato.host, nodo_dato.puerto)

    elif len(nodo_dato.tabla_fingers_mayor) > 0 and id > nodo_dato.identificador:
        # Si el id es mayor que el identificador del nodo, buscar en la tabla de dedos más grande
        resultado = obtener_sucesor_tabla(nodo_dato.tabla_fingers_mayor, id)
    
    elif len(nodo_dato.tabla_fingers_menor) > 0 and id > nodo_dato.identificador:
        # Si el id es mayor y hay dedos menores, devolver el primer dedo menor
        resultado = nodo_dato.tabla_fingers_menor[0][1], nodo_dato.tabla_fingers_menor[0][2]

    elif len(nodo_dato.tabla_fingers_menor) > 0:
        # Si hay dedos menores, buscar el sucesor en la tabla de dedos menor
        resultado = obtener_sucesor_tabla(nodo_dato.tabla_fingers_menor, id)
    
    else:
        # Devolver el último dedo de la tabla de dedos más grande
        indice = len(nodo_dato.tabla_fingers_mayor) - 1
        resultado = (nodo_dato.tabla_fingers_mayor[indice][1], nodo_dato.tabla_fingers_mayor[indice][2])

    # Liberar el mutex de lectura
    nodo_dato.mutex_lectura.acquire()
    nodo_dato.contador_lectura -= 1
    nodo_dato.mutex_lectura.release()

    return resultado

# Obtener una lista de cadenas ip:puerto de los k sucesores de un nodo
def obtener_k_sucesores(nodo_dato: NodoDato):
    k = nodo_dato.k_sucesores
    resultado = []

    # Esperar hasta que no esté actualizando
    while nodo_dato.actualizando:
        pass

    # Adquirir el mutex de lectura
    nodo_dato.mutex_lectura.acquire()
    nodo_dato.contador_lectura += 1
    nodo_dato.mutex_lectura.release()

    # Obtener los k sucesores
    for _, ip, puerto in nodo_dato.sucesores:
        if k > 0:
            resultado.append(f"{ip}:{puerto}") 
            k -= 1
        else:
            break

    # Liberar el mutex de lectura
    nodo_dato.mutex_lectura.acquire()
    nodo_dato.contador_lectura -= 1
    nodo_dato.mutex_lectura.release()
    return resultado

# Manejar el comando de obtener sucesor
def manejar_comando_gs(nodo_dato: NodoDato, id_clave, socket_cliente):
    nodo_dato.mutex_predecesor.acquire()
    propietario_clave = (
        nodo_dato.predecesor is None or
        (nodo_dato.predecesor[0] > nodo_dato.identificador and (id_clave <= nodo_dato.identificador or id_clave > nodo_dato.predecesor[0])) or
        (nodo_dato.predecesor[0] < id_clave and id_clave <= nodo_dato.identificador)
    )
    nodo_dato.mutex_predecesor.release()

    if propietario_clave:
        socket_cliente.send(f"220".encode())
    else:
        ip, puerto = encontrar_sucesor_tabla(nodo_dato, id_clave)
        socket_cliente.send(f"550 {ip}:{puerto}".encode())

# Manejar el comando de obtener k sucesores
def manejar_comando_gk(nodo_dato: NodoDato, socket_cliente):
    socket_cliente.send(f"220 {' '.join(obtener_k_sucesores(nodo_dato))}".encode())

# Enviar el mensaje de aceptación 220
def manejar_comando_ping(socket_cliente):
    socket_cliente.send(f"220".encode())

def difundir_buscar_sucesor(nodo_dato: NodoDato):
    ip_broadcast = '<broadcast>'
    puerto_broadcast = 37020
    mensaje = json.dumps({'action': 'report'})
    
    # Crear un socket UDP para la difusión
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(5)  # Establecer un tiempo de espera de 5 segundos
        
        try:
            # Enviar el mensaje de difusión
            sock.sendto(mensaje.encode(), (ip_broadcast, puerto_broadcast))

            if nodo_dato.verbose_actualizacion:
                print(f"Mensaje de difusión enviado: {mensaje}")
            
            sucesor_mas_cercano = None

            while True:
                try:
                    # Esperar respuestas de otros nodos
                    respuesta, _ = sock.recvfrom(1024)
                    datos_respuesta = json.loads(respuesta.decode())
                    
                    if datos_respuesta.get('action') == 'reporting':
                        ip = datos_respuesta.get('ip')
                        puerto = datos_respuesta.get('port')

                        # Ignorar la respuesta del propio nodo
                        if ip != nodo_dato.host or puerto != nodo_dato.puerto:
                            id = funcion_hash(obtener_id(ip, puerto))

                            # Evaluar el sucesor más cercano
                            if sucesor_mas_cercano is None:
                                sucesor_mas_cercano = id, ip, puerto
                            
                            elif (sucesor_mas_cercano[0] < nodo_dato.identificador and 
                                  (id > nodo_dato.identificador or id < sucesor_mas_cercano[0])):
                                sucesor_mas_cercano = id, ip, puerto

                            elif (sucesor_mas_cercano[0] > nodo_dato.identificador and 
                                  id < sucesor_mas_cercano[0] and id > nodo_dato.identificador):
                                sucesor_mas_cercano = id, ip, puerto
        
                except socket.timeout:
                    return sucesor_mas_cercano  # Retornar el sucesor más cercano al tiempo de espera

        except Exception as e:
            if nodo_dato.verbose_actualizacion:
                print(f"Excepción en difundir_buscar_sucesor: {e}")

def verificar_sucesor_mas_cercano(nodo_dato: NodoDato):
    while not nodo_dato.detener_actualizacion:
        # Difundir el mensaje para buscar sucesores
        sucesor_difundido = difundir_buscar_sucesor(nodo_dato)

        if sucesor_difundido:
            nodo_dato.mutex_sucesor.acquire()  # Adquirir el mutex para acceder al sucesor
            
            # Actualizar el sucesor si es necesario
            if nodo_dato.sucesor is None or sucesor_difundido[0] < nodo_dato.sucesor[0]:
                nodo_dato.sucesor = sucesor_difundido

            nodo_dato.mutex_sucesor.release()  # Liberar el mutex

        time.sleep(10)  # Esperar 10 segundos antes de la siguiente verificación

def verificar_datos_sin_propietarios(nodo_dato: NodoDato):
    while not nodo_dato.detener_actualizacion:
        try:
            items = []

            # Intentar obtener los items de los datos
            while True:
                try:
                    items = list(nodo_dato.datos.items())
                    break
                except Exception as e:
                    if nodo_dato.verbose:
                        print(f"Error: {e}")

            # Recorrer los items para verificar la propiedad
            for clave, valor in items:
                id_clave = funcion_hash(clave)

                nodo_dato.mutex_predecesor.acquire()  # Adquirir mutex para acceder al predecesor
                es_propietario_clave = (nodo_dato.predecesor is None or 
                                        (nodo_dato.predecesor[0] > nodo_dato.identificador and 
                                        (id_clave <= nodo_dato.identificador or id_clave > nodo_dato.predecesor[0])) or 
                                        (nodo_dato.predecesor[0] < id_clave and id_clave <= nodo_dato.identificador))
                nodo_dato.mutex_predecesor.release()  # Liberar mutex

                if not es_propietario_clave:
                    try:
                        nodo_ip, nodo_puerto = nodo_dato.host, nodo_dato.puerto
                        ip, puerto = encontrar_sucesor(id_clave, nodo_ip, nodo_puerto, True, nodo_dato.verbose_actualizacion)
                    except Exception:
                        continue

                    try:
                        # Crear socket para conectar al nodo sucesor
                        nodo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        nodo_socket.connect((ip, puerto))
                    except Exception:
                        continue

                    try:
                        nodo_socket.sendall(f"RP".encode())

                        respuesta = nodo_socket.recv(1024).decode().strip()

                        if respuesta.startswith("220"):
                            if isinstance(valor[0], dict):
                                datos = f"{json.dumps(valor[0])}".encode()
                                nodo_socket.sendall(f"Folder {valor[1]} {len(datos)} {clave}".encode())

                                respuesta = nodo_socket.recv(1024).decode().strip()

                                if respuesta.startswith("220"):
                                    nodo_socket.sendall(datos)

                                    respuesta = nodo_socket.recv(1024).decode().strip()

                                    if (not respuesta) or not respuesta.startswith("220"):
                                        raise Exception(f"Algo salió mal reasignando {ip}:{puerto} {clave}")

                                    if nodo_dato.verbose_actualizacion:
                                        print(f"Transferencia completa {clave}")

                                if respuesta.startswith("404"):
                                    nodo_dato.datos.pop(clave)  # Eliminar clave si no se encuentra

                            else:
                                nodo_socket.sendall(f"File {valor[1]} {os.stat(valor[0]).st_size} {clave}".encode())

                                respuesta = nodo_socket.recv(1024).decode().strip()

                                if respuesta.startswith("220"):
                                    with open(valor[0], "rb") as archivo:
                                        datos = archivo.read(4096)
                                        contador = 0
                                        while datos:
                                            nodo_socket.sendall(datos)
                                            contador += len(datos)
                                            datos = archivo.read(4096)

                                    respuesta = nodo_socket.recv(1024).decode().strip()

                                    if (not respuesta) or not respuesta.startswith("220"):
                                        raise Exception(f"Algo salió mal reasignando {ip}:{puerto} {clave}")

                                    if nodo_dato.verbose_actualizacion:
                                        print(f"Transferencia completa {clave}")

                                if respuesta.startswith("404"):
                                    nodo_dato.datos.pop(clave)  # Eliminar clave si no se encuentra

                            nodo_socket.send(b"226 Transferencia completa.\r\n")

                    finally:
                        nodo_socket.close()  # Asegurarse de cerrar el socket

        except Exception as e:
            if nodo_dato.verbose_actualizacion:
                print(f"Error: {e}")

        time.sleep(10)  # Esperar 10 segundos antes de la siguiente verificación

def verificar_sucesores(nodo_dato: NodoDato):
    """Actualizar la lista de sucesores y replicar datos si es necesario."""
    try:
        nuevos_sucesores = []

        nodo_dato.mutex_sucesor.acquire()
        lista_sucesores = [nodo_dato.sucesor] + nodo_dato.sucesores if nodo_dato.sucesor else nodo_dato.sucesores
        nodo_dato.mutex_sucesor.release()
        
        # Encontrar el primer sucesor activo
        for sucesor in lista_sucesores:
            if hacer_ping_nodo(sucesor[1], sucesor[2], nodo_dato.verbose_actualizacion):
                nuevos_sucesores.append(sucesor)
                break

        if len(nuevos_sucesores) == 0:
            sucesor = difundir_buscar_sucesor(nodo_dato)

            if sucesor is not None:
                nodo_dato.mutex_sucesor.acquire()
                nodo_dato.sucesor = sucesor
                nodo_dato.mutex_sucesor.release()

                return verificar_sucesores(nodo_dato)

            nodo_dato.actualizando = True

            # Esperar hasta que no haya lecturas en curso
            while nodo_dato.contador_lectura > 0:
                pass

            nodo_dato.predecesor = None
            nodo_dato.sucesor = None
            nodo_dato.sucesores = []

            nodo_dato.actualizando = False

            return True
        
        nodo_dato.mutex_predecesor.acquire()
        id_predecesor = nodo_dato.predecesor[0] if nodo_dato.predecesor else nuevos_sucesores[0][0]
        nodo_dato.mutex_predecesor.release()

        # Completar la lista de sucesores hasta k
        while len(nuevos_sucesores) < nodo_dato.k_sucesores:
            try:
                ip, puerto = encontrar_sucesor(nuevos_sucesores[-1][0] + 1, nuevos_sucesores[-1][1], nuevos_sucesores[-1][2], True, nodo_dato.verbose_actualizacion)
            except Exception:
                break
            
            id = funcion_hash(obtener_id(ip, puerto))

            if id != nodo_dato.identificador:
                nuevos_sucesores.append((id, ip, puerto))
            else:
                break

        # Replicar datos en los nuevos sucesores
        for nuevo_sucesor in nuevos_sucesores:
            nodo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            nodo_socket.connect((nuevo_sucesor[1], nuevo_sucesor[2]))
            
            if nodo_dato.verbose_actualizacion:
                print(f"Replicando en {nuevo_sucesor[1]}:{nuevo_sucesor[2]}")
            
            nodo_socket.sendall(f"RP".encode())

            respuesta = nodo_socket.recv(1024).decode().strip()

            if respuesta.startswith("220"):
                items = []

                while True:
                    try:
                        items = list(nodo_dato.datos.items())
                        break
                    except Exception as e:
                        if nodo_dato.verbose:
                            print(f"Error: {e}")

                for clave, valor in items:
                    id_clave = funcion_hash(clave)

                    if (id_predecesor > nodo_dato.identificador and 
                        (id_clave <= nodo_dato.identificador or id_clave > id_predecesor)) or (id_predecesor < id_clave and id_clave <= nodo_dato.identificador):
                        if isinstance(valor[0], dict):
                            datos = f"{json.dumps(valor[0])}".encode()
                            nodo_socket.sendall(f"Folder {valor[1]} {len(datos)} {clave}".encode())

                            respuesta = nodo_socket.recv(1024).decode().strip()

                            if respuesta.startswith("220"):
                                nodo_socket.sendall(datos)

                                respuesta = nodo_socket.recv(1024).decode().strip()

                                if (not respuesta) or not respuesta.startswith("220"):
                                    raise Exception(f"Algo salió mal replicando {nuevo_sucesor[1]}:{nuevo_sucesor[2]} {clave}")

                                if nodo_dato.verbose_actualizacion:
                                    print(f"Transferencia completa {clave}")

                        else:
                            nodo_socket.sendall(f"File {valor[1]} {os.stat(valor[0]).st_size} {clave}".encode())

                            respuesta = nodo_socket.recv(1024).decode().strip()

                            if respuesta.startswith("220"):
                                with open(valor[0], "rb") as archivo:
                                    datos = archivo.read(4096)
                                    while datos:
                                        nodo_socket.sendall(datos)
                                        datos = archivo.read(4096)

                                respuesta = nodo_socket.recv(1024).decode().strip()

                                if (not respuesta) or not respuesta.startswith("220"):
                                    raise Exception(f"Algo salió mal replicando {nuevo_sucesor[1]}:{nuevo_sucesor[2]} {clave}")

                                if nodo_dato.verbose_actualizacion:
                                    print(f"Transferencia completa {clave}")

                nodo_socket.send(b"226 Transferencia completa.\r\n")
            
            nodo_socket.close()

        nodo_dato.actualizando = True

        while nodo_dato.contador_lectura > 0:
            pass

        nodo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        nodo_socket.connect((nuevos_sucesores[0][1], nuevos_sucesores[0][2]))

        if nodo_dato.verbose_actualizacion:
            print(f"Notificando Sucesor {nuevos_sucesores[0][1]}:{nuevos_sucesores[0][2]}")
        
        nodo_socket.sendall(f"SP {nodo_dato.host}:{nodo_dato.puerto}".encode())

        respuesta = nodo_socket.recv(1024).decode().strip()
        nodo_socket.close()

        if respuesta.startswith("550"):
            ip, puerto = respuesta[4:].split(":")
            puerto = int(puerto)
            nodo_dato.sucesor = funcion_hash(obtener_id(ip, puerto)), ip, puerto
            nodo_dato.actualizando = False
            return verificar_sucesores(nodo_dato)

        nodo_dato.sucesor = nuevos_sucesores[0]
        nodo_dato.sucesores = nuevos_sucesores  

        nodo_dato.actualizando = False

        return True

    except Exception as e:
        nodo_dato.actualizando = False
        
        if nodo_dato.verbose_actualizacion:
            print(f"Error al verificar sucesores: {e}")

        return False

def actualizar_tabla_finger(nodo_dato: NodoDato):
    """Actualiza la Tabla Finger de un nodo solicitado."""
    try:
        nueva_tabla_finger_mayor = []
        nueva_tabla_finger_menor = []
        
        if len(nodo_dato.sucesores) > 0:
            ip_nodo_solicitado, puerto_nodo_solicitado = nodo_dato.sucesores[0][1], nodo_dato.sucesores[0][2]

            for i in range(161):
                try:
                    ip, puerto = encontrar_sucesor(nodo_dato.identificador + 2 ** i, ip_nodo_solicitado, puerto_nodo_solicitado, True, nodo_dato.verbose_actualizacion)
                except:
                    break
                
                id_nodo = funcion_hash(obtener_id(ip, puerto))

                ip_nodo_solicitado, puerto_nodo_solicitado = ip, puerto

                if id_nodo > nodo_dato.identificador and (len(nueva_tabla_finger_mayor) == 0 or (nueva_tabla_finger_mayor[-1][0] != id_nodo and nueva_tabla_finger_mayor[0][0] != id_nodo)):
                    nueva_tabla_finger_mayor.append((id_nodo, ip, puerto))
                
                elif id_nodo < nodo_dato.identificador:
                    for j in range(161 - i):
                        try:
                            ip, puerto = encontrar_sucesor(2 ** j, ip_nodo_solicitado, puerto_nodo_solicitado, True, nodo_dato.verbose_actualizacion)
                        except:
                            break

                        id_nodo = funcion_hash(obtener_id(ip, puerto))

                        ip_nodo_solicitado, puerto_nodo_solicitado = ip, puerto
                        
                        if id_nodo >= nodo_dato.identificador:
                            break

                        if len(nueva_tabla_finger_menor) == 0 or (nueva_tabla_finger_menor[-1][0] != id_nodo and nueva_tabla_finger_menor[0][0] != id_nodo):
                            nueva_tabla_finger_menor.append((id_nodo, ip, puerto))

                    break
                
                elif id_nodo == nodo_dato.identificador:
                    break
                    

        nodo_dato.actualizando = True

        while nodo_dato.contador_lectura > 0:
            pass

        nodo_dato.tabla_fingers_mayor = nueva_tabla_finger_mayor
        nodo_dato.tabla_fingers_menor = nueva_tabla_finger_menor

        nodo_dato.actualizando = False

        return True

    except Exception as e:
        nodo_dato.actualizando = False

        if nodo_dato.verbose_actualizacion:
            print(f"Error: {e}")
        
        return False

def actualizar(nodo_dato: NodoDato):
    """Hilo para actualizar el estado del nodo, verificando los sucesores y actualizando la tabla finger."""
    if not nodo_dato.hilo_verificar_sucesor_cercano.is_alive():
        nodo_dato.hilo_verificar_sucesor_cercano.start()

    while not nodo_dato.detener_actualizacion:
        
        print("Dentro de actualizar")
        
        nodo_dato.mutex_union.acquire()

        if verificar_sucesores(nodo_dato):
            if actualizar_tabla_finger(nodo_dato):
                print("Dentro de actualizar tabla finger")
                
                if not nodo_dato.termino_primera_actualizacion:
                    
                    print("Dentro de primera actualizacion")
                    
                    nodo_dato.termino_primera_actualizacion = True
                    nodo_dato.hilo_listener_broadcast.start()
                    nodo_dato.hilo_verificar_datos_no_poseidos.start()

        nodo_dato.mutex_union.release()

        time.sleep(5)   

def solicitud_unirse_automatica(nodo_dato: NodoDato, indice=0):
    """Intenta unirse a las IPs predeterminadas; si falla al conectarse a todas, intenta usar broadcast."""
    cache_direcciones = []
    
    if indice < len(cache_direcciones):
        try:
            request_join(nodo_dato, *cache_direcciones[indice])

            if nodo_dato.verbose:
                print(f"Conexión exitosa a {cache_direcciones[indice][0]}:{cache_direcciones[indice][1]}")
        except:
            if nodo_dato.verbose:
                print(f"Error al conectar a {cache_direcciones[indice][0]}:{cache_direcciones[indice][1]} - {indice}")
            
            solicitud_unirse_automatica(nodo_dato, indice + 1)    
    else:
        if nodo_dato.verbose:
            print("Todas las IPs predeterminadas fallaron, intentando usar Broadcast...")
        
        solicitud_unirse_broadcast(nodo_dato)

def escuchador_broadcast(nodo_dato: NodoDato):
    """Espera un nodo que utiliza broadcast para encontrar el anillo, 
    informa de este nodo si está disponible y envía su IP y puerto."""
    puerto_broadcast = 37020

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', puerto_broadcast))
        sock.settimeout(1)

        while not nodo_dato.detener_actualizacion:
            try:
                datos, direccion = sock.recvfrom(1024)

                if not nodo_dato.detener_actualizacion:
                    if nodo_dato.verbose_actualizacion:
                        print(f"Mensaje recibido de {direccion}: {datos.decode()}")
                    
                    datos_solicitud = json.loads(datos.decode().strip())
                    accion = datos_solicitud.get('action')
                    
                    if accion == 'report':
                        
                        datos_respuesta = json.dumps({
                            'action': 'reporting',
                            'ip': nodo_dato.host,
                            'port': nodo_dato.puerto
                        })
                        
                        print("Enviando respuesta")
                        
                        sock.sendto(datos_respuesta.encode(), direccion)

                        if nodo_dato.verbose_actualizacion:
                            print(f"Respuesta enviada a {direccion}: {datos_respuesta}")

            except:
                pass

def solicitud_unirse_broadcast(nodo_dato: NodoDato):
    """Utiliza broadcast para encontrar un nodo activo en la red local."""
    ip_broadcast = '<broadcast>'
    puerto_broadcast = 37020
    mensaje = json.dumps({'action': 'report'})
    
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5)
            
            try:
                sock.sendto(mensaje.encode(), (ip_broadcast, puerto_broadcast))

                if nodo_dato.verbose:
                    print(f"Mensaje de broadcast enviado: {mensaje}")
                
                while True:
                    try:
                        respuesta, _ = sock.recvfrom(1024)
                        datos_respuesta = json.loads(respuesta.decode())
                        
                        if datos_respuesta.get('action') == 'reporting':
                            ip = datos_respuesta.get('ip')
                            puerto = datos_respuesta.get('port')

                            try:
                                request_join(nodo_dato, ip, puerto)

                                if nodo_dato.verbose:
                                    print(f"Conexión exitosa a {ip}:{puerto}")
                                
                                return
                            except:
                                pass
                    
                    except socket.timeout:
                        if nodo_dato.verbose:
                            print("Tiempo de espera del request broadcast agotado")
                        break
            except Exception as e:
                if nodo_dato.verbose:
                    print(f"Excepción en solicitud_unirse_broadcast: {e}")

def request_join(nodo_dato: NodoDato, ip_nodo, puerto_nodo):
    """Función para unirse a un nodo existente en la red."""
    
    node_ip, node_port = encontrar_sucesor(obtener_id(nodo_dato.host, nodo_dato.puerto), node_ip, node_port, verbose=nodo_dato.verbose)

    try:
        node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        node_socket.connect((node_ip, node_port))
        
        if nodo_dato.verbose:
            print(f"Connected to {node_ip}:{node_port}")
        
        node_socket.sendall(f"JOIN {nodo_dato.host}:{nodo_dato.puerto}".encode())

        response = node_socket.recv(1024).decode().strip()

        if response.startswith("220"):
            nodo_dato.detener_actualizacion = True
            
            while nodo_dato.hilo_actualizacion.is_alive() or nodo_dato.hilo_listener_broadcast.is_alive() or nodo_dato.hilo_verificar_sucesor_cercano.is_alive() or nodo_dato.hilo_verificar_datos_no_poseidos.is_alive():
                pass

            nodo_dato.termino_primera_actualizacion = False

            nodo_dato.sucesor = funcion_hash(obtener_id(node_ip, node_port)), node_ip, node_port

            predecessor_ip, predecessor_port = response[4:].split(":")
            predecessor_port = int(predecessor_port)

            nodo_dato.mutex_predecesor.acquire()
            nodo_dato.predecesor = (obtener_id(predecessor_ip, predecessor_port)), predecessor_ip, predecessor_port
            nodo_dato.mutex_predecesor.release()

            node_socket.send(f"220".encode())

            while(True):
                response = node_socket.recv(1024).decode().strip()

                if response.startswith("Folder"):
                    args = response[7:].strip().split(" ")
                    
                    version = int(args[0])
                    size = int(args[1])
                    path = " ".join(args[2:])

                    if path not in nodo_dato.datos or nodo_dato.datos[path][1] < version:
                        node_socket.send(f"220".encode())
                            
                        datos_json = ""

                        count = 0
                        while count < size:
                            datos = node_socket.recv(4096)
                            datos_json += datos.decode()
                            count += len(datos)

                        nodo_dato.datos[path] = json.loads(datos_json), version
                        node_socket.send(f"220".encode())

                        if nodo_dato.verbose:
                            print(f"Transfer complete {path}")

                    else:
                        node_socket.send(f"403".encode())

                elif response.startswith("File"):
                    args = response[5:].strip().split(" ")
                    
                    version = int(args[0])
                    size = int(args[1])
                    key = " ".join(args[2:])

                    if key not in nodo_dato.datos or nodo_dato.datos[key][1] < version:
                        os.makedirs(os.path.dirname(key), exist_ok=True)

                        with open(key, "wb") as file: # binary mode
                            node_socket.send(f"220".encode())

                            count = 0
                            while count < size:
                                datos = node_socket.recv(4096)
                                file.write(datos)
                                count += len(datos)
                            
                            nodo_dato.datos[key] = key, version
                            node_socket.send(f"220".encode())

                            if nodo_dato.verbose:
                                print(f"Transfer complete {key}")

                    else:
                        node_socket.send(f"403".encode())

                elif response.startswith("226"):
                    break

            node_socket.close()

            predecessor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            predecessor_socket.connect((predecessor_ip, predecessor_port))

            predecessor_socket.sendall(f"SS {nodo_dato.host}:{nodo_dato.puerto}".encode())

            if nodo_dato.verbose:
                print(f"Notified Predecessor {predecessor_ip}:{predecessor_port}")

            nodo_dato.detener_actualizacion = False
            nodo_dato.hilo_actualizacion.start()

        elif response.startswith("550"):
            ip, port = response.split(" ")[1].split(":")
            node_socket.close()
            request_join(nodo_dato, ip, int(port))
            return

    except Exception as e:
        if nodo_dato.verbose:
            print(f"Error: {e}")