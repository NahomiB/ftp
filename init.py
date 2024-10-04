import sys

sys.path.append('/app')
sys.path.append('/app/distributed/data_node')
    
import os
from platform import node
import threading
<<<<<<< HEAD
from distributed.data_node.run import aceptar_conexiones
=======

from distributed.data_node import aceptar_conexiones
>>>>>>> 613d42f4c424481a7854f053a828dc6542514817
from distributed.data_node.table import NodoDato


def iniciar_nodo():
    nodo_dato = NodoDato()
    nodo_dato.verbose = False
    
    app_path = os.path.normpath('/app')
    nodo_dato.datos[app_path] = {}, 0

    hilo_aceptar_conexiones = threading.Thread(target=aceptar_conexiones, args=(nodo_dato,))
    hilo_aceptar_conexiones.start()

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