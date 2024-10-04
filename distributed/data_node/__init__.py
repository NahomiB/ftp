import threading; 
from command import (manejar_eliminar_comando, manejar_eliminar_dir_comando, manejar_ed_comando, manejar_unir_comando, manejar_listar_comando, manejar_crear_dir_comando, manejar_leer_comando, manejar_recuperar_comando, manejar_rmd_comando, manejar_rp_comando, manejar_sp_comando, manejar_ss_comando, manejar_stor_comando, manejar_stor_dir_comando, funcion_hash, obtener_ip_host); 
from table import (manejar_gk_comando, manejar_gs_comando, manejar_ping_comando, solicitud_unir_automatica, NodoDato)

def manejar_cliente(nodo_dato, socket_cliente):
    """Recibe el comando solicitado por el cliente y realiza la acción correspondiente."""
    try:
        comando = socket_cliente.recv(1024).decode().strip()

        if nodo_dato.verbose:
            print(f"Comando recibido: {comando}")

        # Comandos de mantenimiento de conexión
        if comando.startswith('PING'):
            manejar_ping_comando(socket_cliente)
        
        # Comandos de gestión de claves
        elif comando.startswith('GS'):
            clave = comando[3:].strip()
            manejar_gs_comando(nodo_dato, int(clave), socket_cliente)

        elif comando.startswith('GK'):
            manejar_gk_comando(nodo_dato, socket_cliente)

        elif comando.startswith('RP'):
            manejar_rp_comando(nodo_dato, socket_cliente)

        # Comandos de gestión de nodos
        elif comando.startswith('JOIN'):
            ip, puerto = comando[5:].strip().split(":")
            manejar_unir_comando(nodo_dato, ip, int(puerto), socket_cliente)

        elif comando.startswith('SS'):
            ip, puerto = comando[3:].strip().split(":")
            manejar_ss_comando(nodo_dato, ip, int(puerto), socket_cliente)

        elif comando.startswith('SP'):
            ip, puerto = comando[3:].strip().split(":")
            manejar_sp_comando(nodo_dato, ip, int(puerto), socket_cliente)

        # Comandos de gestión de archivos y directorios
        elif comando.startswith('ED'):
            clave = comando[3:].strip()
            manejar_ed_comando(nodo_dato, clave, socket_cliente)

        elif comando.startswith('LIST'):
            clave = comando[5:].strip()
            manejar_listar_comando(nodo_dato, clave, socket_cliente)

        elif comando.startswith('MKD'):
            clave = comando[4:].strip()
            manejar_crear_dir_comando(nodo_dato, clave, socket_cliente)

        elif comando.startswith('STORDIR'):
            args = comando[8:].strip().split(" ")
            idx_dirname, idx_info = [int(idx) for idx in args[:2]]
            args = " ".join(args[2:])
            manejar_stor_dir_comando(nodo_dato, args[:idx_dirname - 1], args[idx_dirname:idx_info - 1], args[idx_info:], socket_cliente)

        elif comando.startswith('DELEDIR'):
            args = comando[8:].strip().split(" ")
            idx_dirname = int(args[0])
            args = " ".join(args[1:])
            manejar_eliminar_dir_comando(nodo_dato, args[:idx_dirname - 1], args[idx_dirname:], socket_cliente)

        elif comando.startswith('RETR'):
            args = comando[5:].strip().split(" ")
            idx = int(args[0])
            clave = " ".join(args[1:])
            manejar_recuperar_comando(nodo_dato, clave, idx, socket_cliente)

        elif comando.startswith('STOR'):
            clave = comando[5:].strip()
            manejar_stor_comando(nodo_dato, clave, socket_cliente)

        elif comando.startswith('DELE'):
            clave = comando[5:].strip()
            manejar_eliminar_comando(nodo_dato, clave, socket_cliente)

        elif comando.startswith('RMD'):
            clave = comando[4:].strip()
            manejar_rmd_comando(nodo_dato, clave, socket_cliente)

        elif comando.startswith('READ'):
            clave = comando[5:].strip()
            manejar_leer_comando(nodo_dato, clave, socket_cliente)

    except ConnectionResetError:
        if nodo_dato.verbose:
            print("Conexión restablecida por el par")
    finally:
        socket_cliente.close()

def aceptar_conexiones(nodo_dato):
    """Crea un hilo para aceptar todas las conexiones entrantes."""
    while True:
        socket_cliente, direccion = nodo_dato.socket.accept()

        if nodo_dato.verbose:
            print(f"Conexión aceptada de {direccion}")

        hilo_manejar_cliente = threading.Thread(target=manejar_cliente, args=(nodo_dato, socket_cliente,))
        hilo_manejar_cliente.start()


def iniciar_nodo():
    nodo_dato = NodoDato()
    nodo_dato.verbose = False

    hilo_aceptar_conexiones = threading.Thread(target=aceptar_conexiones, args=(nodo_dato,))
    hilo_aceptar_conexiones.start()
    
    solicitud_unir_automatica(nodo_dato)

    while True:
        input("Presiona Enter para continuar...")

        print("-------------------------------------------------")
        print()

        while nodo_dato.updating:
            pass

        print(f"Nodo {nodo_dato.puerto}")
        print(f"Predecessor: {nodo_dato.predecessor}")
        print(f"Sucesores: {nodo_dato.successors}")
        print(f"Tabla de dedos (mayores): {nodo_dato.finger_table_bigger}")
        print(f"Tabla de dedos (menores): {nodo_dato.finger_table_smaller}")

if __name__ == "__main__":
    iniciar_nodo()