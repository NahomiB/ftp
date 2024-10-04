import socket
from utils import obtener_ip_host


def configurar_socket_control(puerto=0, max_conexiones=5):
    """
    Configura y devuelve el socket de control para el nodo.
    """
    try:
        # Crear un socket TCP
        socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Permitir reutilizar la dirección
        socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Vincular el socket
        socket_servidor.bind(('0.0.0.0', puerto))
        
        # Escuchar conexiones
        socket_servidor.listen(max_conexiones)
        
        ip = obtener_ip_host()
        puerto_asignado = socket_servidor.getsockname()[1]
        
        print(f"Escuchando en {ip}:{puerto_asignado}")
        
        return socket_servidor, ip, puerto_asignado

    except Exception as e:
        print(f"Error al configurar el socket: {e}")
        return None, None, None







