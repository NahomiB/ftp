import socket
import threading
import sys
import time
import hashlib
import traceback
import logging
from helper.protocol_codes import *
from helper.logguer import log_message
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import zmq
import pickle

#logger = logging.getLogger(__name__)

# Function to hash a string using SHA-1 and return its integer representation
#def getShaRepr(data: str):
#    return int(hashlib.sha1(data.encode()).hexdigest(), 16)
#

def getShaRepr(data: str, max_value: int = 16):
    # Genera el hash SHA-1 y obtén su representación en hexadecimal
    hash_hex = hashlib.sha1(data.encode()).hexdigest()
    
    # Convierte el hash hexadecimal a un entero
    hash_int = int(hash_hex, 16)
    
    # Define un arreglo o lista con los valores del 0 al 16
    values = list(range(max_value + 1))
    
    # Usa el hash como índice para seleccionar un valor del arreglo
    # Asegúrate de que el índice esté dentro del rango válido
    index = hash_int % len(values)
    
    # Devuelve el valor seleccionado
    return values[index]    