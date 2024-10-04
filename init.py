
import os
from platform import node
import threading
from distributed.data_node import aceptar_conexiones
from distributed.data_node.table import NodoDato


def iniciar_nodo():
    nodo_dato = NodoDato()
    nodo_dato.verbose = False
    
    app_path = os.path.normpath('/app')
    node.data[app_path] = {}, 0

    hilo_aceptar_conexiones = threading.Thread(target=aceptar_conexiones, args=(nodo_dato,))
    hilo_aceptar_conexiones.start()

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