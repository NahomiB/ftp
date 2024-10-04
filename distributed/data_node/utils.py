import hashlib
import socket

def funcion_hash(clave):
    """Retorna un hash entero de 160 bits del input clave."""
    # Generar el hash SHA-1 de la clave y convertirlo a un entero
    return int(hashlib.sha1(clave.encode('utf-8')).hexdigest(), 16)

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

def obtener_id(host, puerto):
    """Genera una identificación basada en la dirección IP y el puerto."""
    return f"{host}:{puerto}"

def hacer_ping_nodo(ip_nodo, puerto_nodo, verbose=True):
    """Envía un ping a un nodo dado y verifica si está disponible."""
    socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        socket_nodo.connect((ip_nodo, puerto_nodo))
        socket_nodo.sendall("PING".encode())
        
        if verbose:
            print(f"Ping a {ip_nodo}:{puerto_nodo}")

        respuesta = socket_nodo.recv(1024).decode().strip()
        socket_nodo.close()

        return respuesta.startswith("220")
    except Exception as e:
        socket_nodo.close()
        if verbose:
            print(f"Error al hacer ping a {ip_nodo}:{puerto_nodo}: {e}")
        return False

def encontrar_sucesor(id_clave, ip_nodo, puerto_nodo, hash=False, verbose=True):
    """Encuentra el sucesor de una clave dada en el nodo especificado."""
    if not hash:
        id_clave = funcion_hash(id_clave)
    
    socket_nodo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_nodo.connect((ip_nodo, puerto_nodo))

    if verbose:
        print(f"Conectado a {ip_nodo}:{puerto_nodo}")
    
    socket_nodo.sendall(f"GS {id_clave}".encode())

    respuesta = socket_nodo.recv(1024).decode().strip()

    if respuesta.startswith("220"):
        socket_nodo.close()
        return ip_nodo, puerto_nodo
    
    ip, puerto = respuesta.split(" ")[1].split(":")
    socket_nodo.close()
        
    return encontrar_sucesor(id_clave, ip, int(puerto), True, verbose)