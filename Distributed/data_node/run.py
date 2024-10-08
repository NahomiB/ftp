import sys

sys.path.append('/app')
sys.path.append('/app/distributed/data_node')

import threading; 
import time
from command import (manejar_comando_dele, manejar_comando_dele_dir, manejar_comando_ed, manejar_comando_union, manejar_comando_lista, manejar_comando_mkd, manejar_comando_lectura, manejar_comando_retr, manejar_comando_rmd, manejar_comando_rp, manejar_comando_sp, manejar_comando_ss, manejar_comando_stor, manejar_comando_stor_dir); 
from table import (manejar_comando_gk, manejar_comando_gs, manejar_comando_ping, solicitud_unirse_automatica, NodoDato)

def manejar_cliente(nodo_dato, socket_cliente):
    """Recibe el comando solicitado por el cliente y realiza la acción correspondiente."""
    try:
        comando = socket_cliente.recv(1024).decode().strip()
        
        print("Comando recibido")
        print(comando)

        if nodo_dato.verbose:
            print(f"Comando recibido: {comando}")

        # Comandos de mantenimiento de conexión
        if comando.startswith('PING'):
            manejar_comando_ping(socket_cliente)
        
        # Comandos de gestión de claves
        elif comando.startswith('GS'):
            clave = comando[3:].strip()
            manejar_comando_gs(nodo_dato, int(clave), socket_cliente)

        elif comando.startswith('GK'):
            manejar_comando_gk(nodo_dato, socket_cliente)

        elif comando.startswith('RP'):
            manejar_comando_rp(nodo_dato, socket_cliente)

        # Comandos de gestión de nodos
        elif comando.startswith('JOIN'):
            ip, puerto = comando[5:].strip().split(":")
            manejar_comando_union(nodo_dato, ip, int(puerto), socket_cliente)

        elif comando.startswith('SS'):
            ip, puerto = comando[3:].strip().split(":")
            manejar_comando_ss(nodo_dato, ip, int(puerto), socket_cliente)

        elif comando.startswith('SP'):
            ip, puerto = comando[3:].strip().split(":")
            manejar_comando_sp(nodo_dato, ip, int(puerto), socket_cliente)

        # Comandos de gestión de archivos y directorios
        elif comando.startswith('ED'):
            clave = comando[3:].strip()
            manejar_comando_ed(nodo_dato, clave, socket_cliente)

        elif comando.startswith('LIST'):
            clave = comando[5:].strip()
            manejar_comando_lista(nodo_dato, clave, socket_cliente)

        elif comando.startswith('MKD'):
            clave = comando[4:].strip()
            manejar_comando_mkd(nodo_dato, clave, socket_cliente)

        elif comando.startswith('STORDIR'):
            args = comando[8:].strip().split(" ")
            idx_dirname, idx_info = [int(idx) for idx in args[:2]]
            args = " ".join(args[2:])
            manejar_comando_stor_dir(nodo_dato, args[:idx_dirname - 1], args[idx_dirname:idx_info - 1], args[idx_info:], socket_cliente)

        elif comando.startswith('DELEDIR'):
            args = comando[8:].strip().split(" ")
            idx_dirname = int(args[0])
            args = " ".join(args[1:])
            manejar_comando_dele_dir(nodo_dato, args[:idx_dirname - 1], args[idx_dirname:], socket_cliente)

        elif comando.startswith('RETR'):
            args = comando[5:].strip().split(" ")
            idx = int(args[0])
            clave = " ".join(args[1:])
            manejar_comando_retr(nodo_dato, clave, idx, socket_cliente)

        elif comando.startswith('STOR'):
            clave = comando[5:].strip()
            manejar_comando_stor(nodo_dato, clave, socket_cliente)

        elif comando.startswith('DELE'):
            clave = comando[5:].strip()
            manejar_comando_dele(nodo_dato, clave, socket_cliente)

        elif comando.startswith('RMD'):
            clave = comando[4:].strip()
            manejar_comando_rmd(nodo_dato, clave, socket_cliente)

        elif comando.startswith('READ'):
            clave = comando[5:].strip()
            manejar_comando_lectura(nodo_dato, clave, socket_cliente)

    except ConnectionResetError:
        if nodo_dato.verbose:
            print("Conexión restablecida por el par")
    finally:
        socket_cliente.close()

def aceptar_conexiones(nodo_dato):
    """Crea un hilo para aceptar todas las conexiones entrantes."""
    print("Inicio de aceptar conexiones")
    while True:
        socket_cliente, direccion = nodo_dato.socket.accept()

        if nodo_dato.verbose:
            print(f"Conexión aceptada de {direccion}")

        hilo_manejar_cliente = threading.Thread(target=manejar_cliente, args=(nodo_dato, socket_cliente,))
        hilo_manejar_cliente.start()
        
        print("Fin de aceptar conexiones")
        
        
def iniciar_nodo():
    nodo_dato = NodoDato()

    hilo_aceptar_conexiones = threading.Thread(target=aceptar_conexiones, args=(nodo_dato,))
    hilo_aceptar_conexiones.start()
    
    solicitud_unirse_automatica(nodo_dato)

    while True:
        print("-------------------------------------------------")
        print()

        while nodo_dato.actualizando:
            pass

        print(f"Nodo {nodo_dato.puerto}")
        print(f"Predecessor: {nodo_dato.predecesor}")
        print(f"Sucesores: {nodo_dato.sucesores}")
        print(f"Tabla de dedos (mayores): {nodo_dato.tabla_fingers_mayor}")
        print(f"Tabla de dedos (menores): {nodo_dato.tabla_fingers_menor}")


if __name__ == "__main__":
    iniciar_nodo()