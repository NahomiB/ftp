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

import asyncio
# Class to reference a Chord node
class ChordNodeReference:
    def __init__(self, ip: str, port: int = 8001):
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = port

   
   
    def _send_data(self, op:int, data:str='')->'ChordNodeReference':
        if isinstance(data,ChordNodeReference):
            data={'op':op,'id':data.id,'ip':data.ip}
        if not (isinstance(data,tuple) or isinstance(data,dict) or isinstance(data,str)):
            log_message(f'El data {data} es de tipo {type(data)}',func=self._send_data)
        data =data if data is not None else '' 
        #log_message(f'Typo de op {type(op)}  tipo de data{type(data)}')
        data=(op,data)
        # Serializar el objeto
        data = pickle.dumps(data)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip, self.port))
                s.settimeout(20)# Decir que a lo sumo espera 20 segundos
                s.sendall(data)
                new_data=s.recv(1024)
                #log_message(f'La data es {new_data}',func=self._send_data)
                if len(new_data)<1:
                    log_message(f'Se quiso enviar al nodo {self.ip } una peticion de tipo {op} y el len de new_data es {len(new_data)}',func=self._send_data)
                data_format=pickle.loads(new_data)#Al tipo de dato de python
               
                if not isinstance(data_format,ChordNodeReference):
                    log_message(f'La respuesta recibida del nodo {self.id} es {data_format} de tipo {type(data_format)}',func=self._send_data)
               
               
                #log_message(f'A llegado un objeto {data_format} de tipo {type(data_format)}',func=self._send_data)
                return data_format
        except Exception as e:
            #print(f"ERROR sending data: {e} al nodo con id {self.id} e ip {self.ip}")
            log_message(f"ERROR sending data: {e} al nodo con id {self.id} en la opcion {op} e ip {self.ip} y tiene una dimension de data{len(new_data)} ,Error:{str(traceback.format_exc())}",level='ERROR')
            #logger.info()
            traceback.print_exc()
            raise Exception(f'Exception in node reference sendata')
        
        

          
    
    def find_successor(self, id: int) -> 'ChordNodeReference':
        """ Method to find the successor of a given id"""
        response=-1
        #try:
        #    response = self._send_data(FIND_SUCCESSOR, id)
        #    response.port=self.port
        #    return response
        #except Exception as e:
        #    log_message(f'Hubo un error en find_successor con response {response} de tipo {type(response)} con Error:{e}',func=self.find_successor)
        response=self._send_data(FIND_SUCCESSOR, id)
        return response
    
    # Method to find the predecessor of a given id
    def find_predecessor(self, id: int) -> 'ChordNodeReference':
        #try:
        #    response = self._send_data(FIND_PREDECESSOR, id)
        #    return response
        #except Exception as e:
        #    log_message(f'Hubo un error en find_successor con response {response} de tipo {type(response)} con Error:{e}',func=self.find_predecessor)
            
        response=self._send_data(FIND_PREDECESSOR,id)
        return response
    
    def find_key_owner(self,id:int)->'ChordNodeReference':
        response=self._send_data(FIND_KEY_OWNER,id)
        return response            
    
    # Property to get the successor of the current node
    @property
    def succ(self) -> 'ChordNodeReference':
        response = self._send_data(GET_SUCCESSOR)
        #log_message(f'EL sucesor del nodo {self.id} es el nodo {response.id}',)
        return response

    # Property to get the predecessor of the current node
    @property
    def pred(self) -> 'ChordNodeReference':
        response = self._send_data(GET_PREDECESSOR)
        return response

    # Method to notify the current node about another node
    def notify(self, node: 'ChordNodeReference'):
        self._send_data(NOTIFY, node)

    # Method to check if the predecessor is alive
    def check_predecessor(self)->bool:
        #log_message(f'Enviando menajse al predecesor',func=self.check_predecessor)
        response=None
        try:
            response=self._send_data(CHECK_PREDECESSOR)
        except:
            log_message(f'Error tratando de comunicar con el predecesor ',func=self.check_predecessor)
            return False
        #print(f'La respuesta de si esta vivo el nodo vivo o no es {response}')
        log_message(f'La respuesta de si esta vivo el nodo vivo o no es {response}',func=ChordNodeReference.check_predecessor,extra_data={'func':'check_predecesor from ChordReferenceNode'})
        if response in ['',' ', None,EMPTYBIT]:
            return   False
        try:
            node= response
            return node.id==self.id
        except:
            log_message(f'Hubo problemas al tratar de conocer la respuesta del nodo predecesor que el envio',level='ERROR',func=self.check_predecessor)
            return False

    # Method to find the closest preceding finger of a given id
    def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
        response = self._send_data(CLOSEST_PRECEDING_FINGER, id)
        return response

    # Method to store a key-value pair in the current node
    def store_key(self, key: str, value: str):
        response =self._send_data(STORE_KEY, (key,value))
        return response
    # Method to retrieve a value for a given key from the current node
    def retrieve_key(self, key: str) -> str:
        response = self._send_data(RETRIEVE_KEY, key)
        return response

    
    def __str__(self) -> str:
        return f'ChordNodeReference:{self.id},{self.ip},{self.port}'

    def __repr__(self) -> str:
        return str(self)

