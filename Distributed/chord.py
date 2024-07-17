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

# Class representing a Chord node
class ChordNode:
    def __init__(self, ip: str, port: int = 8001, m: int = 160): #m=160
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = port
        self.ref:ChordNodeReference = ChordNodeReference(self.ip, self.port)
        self.succ:ChordNodeReference = self.ref  # Initial successor is itself
        self.pred:ChordNodeReference = None  # Initially no predecessor
        self.m = m  # Number of bits in the hash/key space
        self.finger = [self.ref] * self.m  # Finger table
        self.index_in_fingers:dict[int,set[int]]={} # Diccionario que a cada id le asigna que indices ocupa en la finger table
        self.next = 0  # Finger table index to fix next
        self.data = {}  # Dictionary to store key-value pairs
        self.fingers_ok:bool=False  # Dice si los fingers estan ok o no
        self._key_range=(-1,self.ip) # the key_range [a,b) if a =-1 because no have predecesor
        self.cache:dict[int,str]={} #diccionario con la cache de todos los nodos de la red
        self._broadcast_lock:threading.Lock = threading.Lock()
        self.Is_Search_Succ_:bool=False #
        # Start background threads for stabilization, fixing fingers, and checking predecessor
        threading.Thread(target=self.stabilize, daemon=True).start()  # Start stabilize thread
        threading.Thread(target=self.fix_fingers, daemon=True).start()  # Start fix fingers thread
        threading.Thread(target=self.check_predecessor, daemon=True).start()  # Start check predecessor thread
        threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
        threading.Thread(target=self.show,daemon=True).start() # Start funcion que se esta printeando todo el tipo cada n segundos
        threading.Thread(target=self._search_successor,daemon=True,args=(JOIN,self.ref,)).start() # Enviar broadcast cuando no tengo sucesor
        threading.Thread(target=self._recive_broadcastt,daemon=True).start() # Recibir continuamente broadcast
        threading.Thread(target=self.stabilize_finger,daemon=True).start()
        #threading.Thread(target=self.search_test,daemon=True).start()

    @property
    def key_range(self):
        """ 
        The key range of the chrod node [a,b) b is the id of this node
        
        """
        return self._key_range
    
    @property
    def Is_Search_Succ(self):
        with self._broadcast_lock:
            return self.Is_Search_Succ_
    @Is_Search_Succ.setter
    def Is_Search_Succ(self,value):
        if not isinstance(value,bool):
            raise Exception(f'Value debe ser bool no de tipo {type(value)} con valor {value}')
        with self._broadcast_lock:
            self.Is_Search_Succ_ = value
    
    def search_test(self):
       
            while True:
                try:
                    time.sleep(3)
                    log_message('%'*20,level='INFO')
                    #with ThreadPoolExecutor(max_workers=3) as executor:
                    #    for i in range(0,20):
                    #        future=executor.submit(self.find_succ,i) # Meterlo en el pool de hilos
                    #        node=future.result(timeout=10)
                    #        
                    #        log_message(f'El nodo que le pertenece el id {i} es el nodo con id {node.id}')
                    for i in range(0,20):
                        node=self.find_succ(i)
                        log_message(f'El nodo que le pertenece el id {i} es el nodo con id {node.id}')
                        
                    log_message('+'*20,level='INFO')
                except Exception as e:
                    log_message(f'Error buscando informacion {e}',self.search_test)
        
            
    def show(self):
        """
        Show my ip and id and mi predecessor and succesors ips and ids
        """
        print(f'ENtro en print')
        """Printea quien soy yo"""
        while True:
            log_message('-'*20,level='INFO')
            log_message(f'Mi predecesor es {self.pred.id if self.pred else None} con ip {self.pred.ip if self.pred else None} ',level='INFO')
            log_message(f'Yo soy id:{self.id},con ip:{self.ip} ',level='INFO')
            if self.succ.id == self.id:
                if self.succ.ip !=self.ip:
                    log_message('El sucesor tiene igual ID pero no tiene igual ip',level='INFO')
                log_message(f'Todavia no tengo sucesor',level='INFO'),
            else:
                log_message(f'Mi sucesor es {self.succ.id if self.succ else None} con ip {self.succ.ip  if self.succ else None}',level='INFO')
            log_message('*'*20,level='INFO')
            
            
            time.sleep(3) # Se presenta cada 10 segundos
            
    def _search_successor(self, op: int, data: str = None) -> bytes:
        """Busca un sucesor si no tengo o si mi pred es None

        Args:
            op (int): _description_
            data (str, optional): _description_. Defaults to None.

        Returns:
            bytes: _description_
        """
       # Enviar broadcast cada vez que sienta que mi sucesor no existe
        while True:
            log_message(f'Tratando de hacer broadcast',func=self._search_successor)
        #Enviar broadcast para descubrir mi nuevo sucesor 
            if self.succ.id==self.id or (self.succ.id!=self.id and self.pred is None) :
                #with self._broadcast_lock:
                    log_message(f'Voy a enviar un broadcast para buscar un sucesor ',func=self._search_successor)
                    try:
                        self._send_broadcast(op,data)
                        log_message(f'Enviado el broadcas para buscar succ',func=self._search_successor)
                        self.Is_Search_Succ=True
                        log_message(f'Se actualizo el Is_Search_Succ ahora es {self.Is_Search_Succ}',func=self._search_successor)
                    except Exception as e:
                        log_message(f'Ocurrio un problema enviando el broadcast: {e}',level='ERROR',func=self._search_successor)
            time.sleep(3)
            
            
    def _send_broadcast(self,op:int,data:ChordNodeReference):
        log_message(f'Voy a enviar un broadcast con op {op} y data {data}',func=self._send_broadcast)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        to_send=pickle.dumps((op,data))# Serializar el objeto para poder enviarlo 
        #s.sendto(f'{op}-{str(data)}'.encode(), (str(socket.INADDR_BROADCAST), self.port))
        s.sendto(to_send,(str(socket.INADDR_BROADCAST), self.port)) # ENviar el broadcast
        log_message(f'Enviado el broadcast',func=self._search_successor) 
        s.close()
        log_message(f'Acabo de enviar un broadcast con op: {op} y data {data}',func=self._send_broadcast)
       
    def _recive_broadcastt(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.bind(('', self.port))  # Escucha en todas las interfaces en el puerto 8001
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Habilitar el uso compartido del puerto
            #client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Configurar un tiempo de espera
            #client_socket.settimeout(0.2)  # Tiempo de espera de 200 ms
            
            while True:
                try:
                #with self._broadcast_lock:
                    log_message('Esperando Broadcast',func=self._recive_broadcastt)
                    message, address = client_socket.recvfrom(1024)
                    log_message(f'El tipo de lo recibido en broadcast es {type(message)} ,  {type(address)}')
                    message=pickle.loads(message)
                    log_message(f'El tipo de lo recibido deserializado en broadcast es {type(message)} ,  {type(address)}')
                    log_message(f"Mensaje recibido desde {address}: {message}",func=self._recive_broadcastt)
                    if address[0]!=socket.gethostbyname(socket.gethostname()):
                        log_message('Se recibio desde otro nodo',func=self._recive_broadcastt)
                        #message=str(message.decode())
                        log_message(f'Este ahora es el mensaje {message} que tiene un tipo {type(message)}',func=self._recive_broadcastt)
                        #op,node=message.split('-')
                        op,node=message
                        op=int(op)
                        log_message(f'LLego la respuesta con opcion {op} de tipo {type(op)}')
                        if int(op)==JOIN:
                            log_message(f'El mensaje recibido al broadcast era para join desde el ip {address[0]} de tipo {type(address[0])}')
                            #self.join(ChordNodeReference(address[0],self.port))
                            self.join(node)
                    time.sleep(3)
                except:
                    log_message(f'Error en el while True del recv broadcast Error: {traceback.format_exc()}',self._recive_broadcastt)
        except Exception as e:
            log_message(f'Error recibiendo broadcast {e}, Error: {traceback.format_exc()}',func=self._recive_broadcastt,level='ERROR')
        
        
    # Helper method to check if a value is in the range (start, end]
    def _inbetween(self, k: int, start: int, end: int) -> bool:
        """Helper method to check if a value is in the range (start, end]

        Args:
            k (int): _description_
            start (int): _description_
            end (int): _description_

        Returns:
            bool: _description_
        """
        if start < end:
            return start < k <= end
        else:  # The interval wraps around 0
            return start < k or k <= end

      # Method to find the successor of a given id
    def find_succ(self, id: int) -> 'ChordNodeReference':
        """Method to find the successor of a given id

        Args:
            id (int): _description_

        Returns:
            ChordNodeReference: _description_
        """
        if id==9:log_message(f'Me estan llamando para ver quien es el dieño de {id}',func=self.find_succ)
        node = self.find_pred(id)  # Find predecessor of id
        if id==9:log_message(f'El nodo dueño del id 9 es {node.id}',func=self.find_succ)
        if node.id!= self.id:
            return node.succ
        else:
            return self.succ
        
            
           

    # Method to find the predecessor of a given id
    def find_pred(self, id: int) -> 'ChordNodeReference':
        """Method to find the predecessor of a given id

        Args:
            id (int): _description_

        Returns:
            ChordNodeReference: _description_
        """
        node:ChordNodeReference = self
        # Comprobar que el sucesor esta vivo, sino se comprueba por 
        while not self._inbetween(id, node.id, node.succ.id):
            
            if node.id==self.id:
                node=self.closest_preceding_finger(id)
            else:
                node = node.closest_preceding_finger(id)
            
        
        return node

    # Method to find the closest preceding finger of a given id
    def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
        """Method to find the closest preceding finger of a given id

        Args:
            id (int): _description_

        Returns:
            ChordNodeReference: _description_
        """
        
        for i in range(self.m - 1, -1, -1):
            if self.finger[i] and self._inbetween(self.finger[i].id, self.id, id):
                return self.finger[i]
        #log_message('El más cercano soy yo',func=ChordNode.closest_preceding_finger)
        return self.ref

    # Method to join a Chord network using 'node' as an entry point
    def join(self, node: 'ChordNodeReference'):
        """
            Method to join a Chord network using 'node' as an entry point 
            Siempre se busca un sucesor por lo tanto tengo que chequear si el nodo puede ser predecesor mio
        Args:
            node (ChordNodeReference): _description_
        """
        log_message(f'El nodo {node.id} mando solicitud de unirse como predecesor',func=ChordNode.join )
        # Si 
        
        if node:
            if self.succ.id==self.id:# Es pq no tengo sucesor entonces acepto a cualquiera
                # Acepto y le digo que me haga su predecesor
                # Mi succ nuevo será el sucesor en el nuevo nodo
                self.succ=node  #node.find_successor(self.id) # Si da bateo solo quedarme con el nodo
                log_message(f'Acabo de actualizar mi sucesor al nodo {self.succ.id}',func=self.join)
                self.succ.notify(self.ref)
                log_message(f'Mande a notificar a mi nuevo sucesor :{self.succ.id} para que me haga su predecesor ',func=self.join)
            else: # Caso que ya tengo un sucesor
                # Le pido al nodo el sucesor mio en su anillo
                log_message(f'Entro aca la peticion del nodo {node.id}',func=self.join)
                node_succ=node  #.find_successor(self.id) # Despues añado que busque al sucesor
                if self._inbetween(node_succ.id,self.id,self.succ.id) or self.pred is None: # Es que se puede insertar pq debe estar entre yo y mi sucesor
                   self.succ=node_succ if node_succ.id<self.id else node # Actualizo mi sucesor
                   log_message(f'Acabo de actualizar mi sucesor al nodo {self.succ.id}',func=self.join)
                   self.succ.notify(self.ref)# Notifico para que me haga su predecesor
                   log_message(f'Mande a notificar a mi nuevo sucesor :{self.succ.id} para que me haga su predecesor ',func=self.join)
                
          
        else: # Despues eliminar esto
            self.succ = self.ref
            self.pred = None
        # Si no puedo le respondo por mis ips
    
    
    def stabilize_finger(self,time_=5):
        """Comprueba si los fingers estan estables

        Args:
            time_ (int, optional): _description_. Defaults to 5.
        """
        while True:
            time.sleep(time_)
            try:
                log_message(f'Chequeando estabilidad de los fingues',func=self.stabilize_finger)
                antes=self.fingers_ok
                succ_id=self.succ.id
                succ_check=(succ_id==self.find_succ(succ_id).id)
                check_pred=True
                if self.pred:
                    pred_id=self.pred.id
                    check_pred=(pred_id==self.find_succ(pred_id).id)
                my_check=self.id==(self.find_succ(self.id).id)
                self.fingers_ok=(succ_check and check_pred and my_check)
                
                if antes!=self.fingers_ok:log_message(f' Los finges ahora estan en {self.fingers_ok} antes estaban {antes}',func=self.stabilize_finger)
                
            except Exception as e:
                log_message(f'Error chequeando que los finguers estan bien {e}',func=self.stabilize_finger)
            

    # Stabilize method to periodically verify and update the successor and predecessor
    def stabilize(self):
        """Stabilize method to periodically verify and update the successor and predecessor
        """
        Is=False
        node=None
        count_failed=0 # Cant de veces que se a tratado de establecer conexion  sin exito con el predecesor del sucesor
        x=None
        while True:
            try:
                Is=False
                if self.succ.id != self.id: # Es pq tengo sucesor
                    log_message('stabilize',func=ChordNode.stabilize)
                    if self.succ is None: self.succ=self.ref
                    try: 
                        x = self.succ.pred # Aca seria preguntar por quien es el sucesor de mi id
                        if not isinstance(x,ChordNodeReference):
                            log_message(f'El sucesor debe ser un chordnode reference x:{x} es de tipo {type(x)}')
                    except: # Esto es que no responde el sucesor 
                        count_failed+=1
                        
                        if count_failed>3:
                            # Trata de contactar con el succ y preguntarle por el predecesor si pasa algun problema en la peticion
                            # Mi sucesor soy yo
                            #Si mi sucesor era mi antecesor entonces hago el antecesor null
                            #if self.succ.id==self.pred.id: self.pred=None
                            time.sleep(20)
                            log_message('Seleccionando_Nuevo_Sucesor',func=ChordNode.stabilize)
                            nearest_node=self.find_succ(self.id+1)
                            log_message(f'EL nodo que tiene {nearest_node.id} el mas cercano',func=ChordNode.stabilize)
                            self.succ=nearest_node if nearest_node.id!=self.succ.id else self.ref
                            continue
                       
                    log_message(f' Este es X {x}',func=ChordNode.stabilize)
                    if x and x.id != self.id:
                        log_message(f'Otra vez x {x}',func=ChordNode.stabilize)
                        if x and self._inbetween(x.id, self.id, self.succ.id):
                            self.succ = x
                        log_message('A Notificar',func=ChordNode.stabilize)
                        try:
                            self.succ.notify(self.ref)
                        except Exception as e: # Si no se puede conumicar con el nuevo sucesor caso que sea que era sucesor y predecesor
                            # y se desconecto pues poner al sucesor como yo mismo
                            log_message(f' Fallo comunicarse con el nuevo sucesor {e}',func=ChordNode.stabilize,level='ERROR')
                            self.succ=self.ref
        
                    
            except Exception as e:
                
                
                log_message(f"  Is_True:{Is}_  node:{node}_  _::: ERROR in stabilize: {e}",func=ChordNode.stabilize,level='ERROR')
                traceback.print_exc() 

            log_message(f"successor : {self.succ} predecessor {self.pred}",func=ChordNode.stabilize)
            time.sleep(5) #Poner en produccion en 1 segundo

    # Notify method to INFOrm the node about another node
    def notify(self, node: 'ChordNodeReference'):
        """ Notify method to INFOrm the node about another node"""
        if node.id == self.id:
            pass
        if not self.pred or self._inbetween(node.id, self.pred.id, self.id):
            self.pred = node
        else:
            pass # Enviar mensaje que de no puede y le paso al que tengo como como predecesor de ese id
    def _delete_from_all_ocurrencies(self,id_node:int,new_node:ChordNodeReference):
        """_summary_

        Args:
            id_node (int): ID del nodo a eliminar
            new_node (ChordNodeReference): NOdo a insertar

        Raises:
            Exception: _description_
        """
        log_message(f'La finger table antes {self.finger}',func=self._delete_from_all_ocurrencies)
        lis_to_change=self.index_in_fingers[id_node] # cambiar pir mi todas las  apararicones d ela finger table
        log_message(f'La lista de ocurrencias es {lis_to_change}',func=self._delete_from_all_ocurrencies)
        for index in lis_to_change:
            temp= self.finger[index]
            if temp.id!=id_node:
               raise Exception(f'Para poder quitar de la finger table tiene que coincidir el que esta en la table {temp.id} en el index {index} con {new_node.id}')
            self.finger[index]=new_node
                            # ELiminar la llave del diccionario
        del self.index_in_fingers[id_node]
        log_message(f'Se elimino de la lista de fungers_index el nodo {id_node} por el nodo {new_node.id}',func=self._delete_from_all_ocurrencies)
        log_message(f'la nueva finger table {self.finger}',func=self._delete_from_all_ocurrencies)
    # Fix fingers method to periodically update the finger table
    def fix_fingers(self):
        """Fix fingers method to periodically update the finger table
        """
        while True:
            log_message(f'La finger table {self.finger}',func=self.fix_fingers)
            try:
                self.next += 1
                if self.next >= self.m:
                    self.next = 0
                a=self.find_succ((self.id + 2 ** self.next) % 2 ** self.m)
                ok=False
                for _ in range(3):
                    if a.check_predecessor(): # Chequear que el nodo esta vivo
                        ok=True
                        break
                    else: 
                        log_message(f'El nodo {a.id} no se encuentra en fix fingers',func=ChordNode.fix_fingers)
                    time.sleep(0.5)
               # a=a.succ if not ok else a
                if not ok:
                    log_message(f'El nodo {a.id} se desconecto de la red',func=ChordNode.fix_fingers)
                    try:
                        i=self.next+1
                        k=i if self.next<self.m else 0
                        change=False
                        while i!=self.next:
                            q=self.closest_preceding_finger(i) # Buscar por los antecesores 
                            log_message(f'El nodo q ahora es {q.id} con i = {i}',func=self.fix_fingers)
                            if q.id!=a.id: # Encontrar el primero que sea distinto
                                self._delete_from_all_ocurrencies(a.id,q) #ELiminar todas las ocurriencias de id y poner las de q
                                a=q
                                log_message(f'Se va a parar aca el while con q ={q.id}',func=self.fix_fingers)
                                change=True
                                break
                            i= i+1 if i<self.m else 0
                
                        
                        if not change  :# Entonces lo cambio por mi en la finger table
                           
                            log_message(f'No se pudo encontrar un nuevo sucesor para el nodo {a.id} por lo tanto yo sere el sucesor',func=ChordNode.fix_fingers)
                            self._delete_from_all_ocurrencies(a.id,self.ref) #Eliminar las referencias de la finger table y ponerme a mi como sucesor de ese id
                            
                            a=self.ref # Despues ver si se puede llamar al nodo '0' para que sea el
                            
                        log_message(f'El nodo a ahora es {a}',func=ChordNode.fix_fingers)
                    except:
                        log_message(f'Fallo buscar el sucesor del prececesor del nodo {a.id+1} Error:{traceback.format_exc()} ',func=self.fix_fingers)
                

                self.finger[self.next] = a
                # Añadir al diccionario 
                self.index_in_fingers.setdefault(a.id,set([self.next]))
                self.index_in_fingers[a.id].add(self.next)
                
            except Exception as e:
                log_message(f"ERROR in fix_fingers: {e} Error:{traceback.format_exc()}",func=ChordNode.fix_fingers,level='ERROR')
            time.sleep(5) # 10

    # Check predecessor method to periodically verify if the predecessor is alive
    def check_predecessor(self):
        """Check predecessor method to periodically verify if the predecessor is alive
        """
        counter=0
        while True:
            try:
                log_message(f'Chequeando predecesor',func=self.check_predecessor)
                if self.pred:
                    if not  self.pred.check_predecessor() or self.pred.succ.id!=self.id:# Saber si esta vivo y su sucesor soy yo
                        counter+=1
                        if counter>3:
                            log_message(f'No se restablecio conexion con el predecesor {self.pred} ',func=ChordNode.check_predecessor,level='ERROR')
                            raise Exception(f'No se restablecio conexion con el predecesor {self.pred} ')
                    else:
                        counter=0
                        log_message(f'El predecesor de mi sucesor es { self.pred.succ.id}',func=self.check_predecessor)
                                          
                    log_message(f'Chequeando predecesor ...',func=ChordNode.check_predecessor)
            except Exception as e:
                log_message(f'Se desconecto el predecesor con id {self.pred.id} e ip {self.pred.ip},error:{e}',func=ChordNode.check_predecessor,level='ERROR')
                traceback.print_exc()
                self.pred=None # Hago mi predecesor en None
                
            time.sleep(5)
            
    def find_key_owner(self,key:int)->ChordNodeReference:
        """ Localiza al dueño de una llave

        Args:
            key (int): _description_

        Returns:
            ChordNodeReference: _description_
        """
        log_message(f'Me han llamado para buscar el nodo dueño de la llave {key}',func=self.find_key_owner)
        
        if   (self.succ.id==self.id and self.pred is None) or self._inbetween(key,self.pred.id,self.id):# Si está entre mi predecesor y yo me devuelvo
            # Si esta entre yo y mi sucesor o si soy el unico nodo en la red
            log_message(f'Yo soy el dueño de la llave {key}',func=self.find_key_owner)
            return self.ref
    
        
        if self.succ.id!=self.id and self.pred is None:
            log_message(f'Anillo inestable',func=self.find_key_owner)
            raise Exception('Anillo Inestable')
        
        
        log_message(f'Enviando a mi sucesor a que se encargue de la llave {key}',func=self.find_key_owner)
        return self.succ.find_key_owner(key)
        
        
        

    def store_key(self,key:int,value)->ChordNodeReference:
        log_message(f'Me han llamado a guardar la llave {key}, con el value {value} de tipo {type(value)}',func=self.store_key)
       
       
        node_to_store=self.find_key_owner(key)# Buscar quien debe tener la llave
        if self.id==node_to_store.id: # Yo debo guardar la llave
            self.data.setdefault(key,value)
            return self.ref
        
        
       
        log_message(f'Enviando al nodo {node_to_store.id} la llave {key} y valor {value} para que la guarden',func=self.store_key)
        return node_to_store.store_key(key,value)
            
    def retrieve_key(self,key:int)->tuple[ChordNodeReference,int,object]:
        """Intenta devuelve la llave si el nodo la contiene None si no está

        Args:
            key (int): _description_

        Returns:
            tuple[ChordNodeReference,int,object]: _description_
        """
        try:
            log_message(f'Se ha mandado a buscar el valor de la llave {key}',func=self.retrieve_key)
            node_to_retrieve=self.find_key_owner(key)
            log_message(f'El nodo que le pertenece esa llave {key} es {node_to_retrieve.id}',func=self.retrieve_key)
            if self.id==node_to_retrieve.id:# Entonces debo Hacer retrieve yo
                log_message(f'Yo soy el dueño de la llave {key}',func=self.retrieve_key)
                value=self.data.get(key,None)# Si no esta la llave que devuelva None
                response=(self.ref,key,value)
                log_message(f'Como resultado del retrieval de la key {key} es {response}',func=self.retrieve_key)
                return response
            response=node_to_retrieve.retrieve_key(key)
            log_message(f'La respuesta de retrieval al nodo con id{node_to_retrieve.id} es {response}',func=self.retrieve_key)
            return response
        except Exception as e :
            log_message(f'Hubo un error en el retrieve key: {e} \n {traceback.format_exc()} ',func=self.retrieve_key)
    
    def client_store_key(self,key:int,value)->tuple[int,int]:
        """Es paraa que el cliente temporal de chord meta una llave

        Args:
            key (int): _description_
            value (_type_): _description_

        Returns:
            tuple(int,int): (id nodo que lo guardo , llave guardada)
        """
        node=self.store_key(key,value)
        log_message(f'El nodo encargado de guardar la llace {key } es {node.id}',func=self.client_store_key)
        return (node.id,key)
    
    def client_retrieve_key(self,key:int):
        """_summary_

        Args:
            key (int): _description_
            
        Returns:
            tuple(int,int,obj): Id nodo que la tenia, llave a buscar, valor guardado
        """
        log_message(f'El cliente ha mandado a tomar lo que guarda la llave {key}',func=self.client_retrieve_key)
        node,key,value=self.retrieve_key(key)
        log_message(f'El nodo que tenia la llave:{key}, tiene id:{node.id}, el valor es {value} de tipo{type(value)}',func=self.client_retrieve_key)
        return (node.id,key,value)        
        
    
        
#
    def server_handle(self,conn,addr):
        #log_message(f'new connection from {addr}',func=ChordNode.start_server)

                    data = conn.recv(1024)
                    data=pickle.loads(data)
                    option = int(data[0])
                    a=data[1]
                    if isinstance(a,dict):
                        data=(data[0],ChordNodeReference(a['ip']))

                    data_resp = None

                    if option == FIND_SUCCESSOR:
                        id = int(data[1])
                        data_resp = self.find_succ(id)
                    elif option == FIND_PREDECESSOR:
                    
                        id = int(data[1])
                        #log_message(f'Me llego una peticion de buscar el predecesor de {id}',func=ChordNode.start_server)
                       # log_message(f'Me llego una peticion de buscar el predecesor de {id}',func=self.start_server)
                        data_resp = self.find_pred(id)
                    elif option == GET_SUCCESSOR:
                        data_resp = self.succ if self.succ else self.ref
                    elif option == GET_PREDECESSOR:
                        data_resp = self.pred if self.pred else self.ref
                    elif option == NOTIFY:
                    
                        #log_message(f'Llego una notificacion del ip:{ip}',func=ChordNode.start_server)

                        node:ChordNodeReference=data[1]
                        #log_message(f'LLegado al notify {node}',func=self.start_server)
                        id=node.id
                        ip=node.ip
                        #log_message(f'Llego una notificacion del ip:{ip}',func=self.start_server)
                        self.notify(ChordNodeReference(ip, self.port))
                    elif option == CHECK_PREDECESSOR:
                    
                        data_resp=self.ref
                        data_resp = self.ref
                    elif option == CLOSEST_PRECEDING_FINGER:
                        id = int(data[1])
                        data_resp = self.closest_preceding_finger(id)
                    elif option == JOIN:
                        ip = data[2]
                        #log_message(f'Recibido la peticion de JOIN desde ip {ip} con id: {getShaRepr(ip)} ')
                        self.join(ChordNodeReference(ip, self.port))


                        node:ChordNodeReference=data[1]
                        ip = node.ip
                        #log_message(f'Recibido la peticion de JOIN desde ip {ip} con id: {getShaRepr(ip)} ',func=self.start_server)
                        self.join(node)
                    elif option == STORE_KEY:
                         # Trae una tupla (key,value)
                         log_message(f'A llegado una peticion de guardar la llave {a[0] } de  tipo {type(a[0])} y el valor {a[1]} de tipo {type(a[1])}',func=self.start_server)
                         data_resp=self.store_key(a[0],a[1])
                         log_message(f'El nodo que guardo la llave es {data_resp.id}',func=self.server_handle)
                    elif option ==STORE_KEY_CLIENT:
                         key=a[0]
                         value=a[1]
                         log_message(f'Ha llegado una peticion de un cliente de meter una llave y valor key{key} valor {value}',func=self.server_handle)     
                         data_resp=self.client_store_key(key,value) 
                         log_message(f'La respues al cliente de guardar la llava {key} y el value {value} es {data_resp} de tipo {type(data_resp)}',func=self.server_handle)
                    elif option ==RETRIEVE_KEY:
                        search_key=int(a)
                        log_message(f'Se ha enviado hacer Retrieve a la llave {search_key}',func=self.server_handle)
                        response=self.retrieve_key(search_key)
                        node,key,value=response
                        log_message(f'El resultado de retrieve la llave {search_key} es  {node}, llave encontrada:{key},valor:{value} de tipo {type(value)}',func=self.server_handle)
                        data_resp=response
                    elif option==RETRIEVE_KEY_CLIENT:
                        key=int(a)
                        log_message(f'A llegado desde un cliente la peticion de tomar el valor que guarda la llave {key}',func=self.server_handle)
                        data_resp=self.client_retrieve_key(key)
                        node_id,key_to_search,value=data_resp
                        log_message(f'El nodo con id {node_id}, guardaba el valor {value} de tipo {type(value)} de la llave {key_to_search}',func=self.server_handle)
                    
                    elif option==FIND_KEY_OWNER:#Buscando a quien le toca esa id
                         log_message(f'Ha llegado una peticion de saber si yo debo ser el dueño de esa llave {a}, {type(a)}',func=self.server_handle)
                         data_resp=self.find_key_owner(a)#Busca el nodo que puede tener esa llave ojo no significa que la tenga
                         log_message(f'El que debe tener la llave {a}, {type(a)} es {data_resp.id} de tipo {type(data_resp)}',func=self.server_handle)
                    
                    if data_resp:
                        
                    
                        response = pickle.dumps(data_resp)
                        if len(response)<1 or len(response)>1020:
                            log_message(f'El len de la respuesta a enviar es de {len(response) } que era un {data_resp.id}',func=self.server_handle)
                        
                        conn.sendall(response)
                        #socket.send(response)
                    else:
                        #socket.send(pickle.dumps(' '))
                        response=pickle.dumps('Errrorrrrrr ')
                       
                        log_message(f'El len de la respuesta a enviar es de {len(response) } que era un Enviando el string error  buscando la opcion {option}',func=self.server_handle)
                        
                        conn.sendall(response)
                    conn.close()
    def start_server(self):
    
        #context = zmq.Context()
        #socket = context.socket(zmq.REP)
        #socket.bind(f"tcp://{self.ip}:{self.port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.port))
            s.listen(10)
            pool = ThreadPoolExecutor(max_workers=40)
            while True:
                
                try:
                    
                    conn, addr = s.accept()
                    #pool.submit(self.server_handle,conn,addr)
                    threading.Thread(target=self.server_handle,args=(conn,addr,)).start()
                   
                    
                   
                except Exception as e:
                    log_message(f'Error en start server {traceback.format_exc()}',func=self.start_server)

     

if __name__ == "__main__":
    print("Hello dht")
    #time.sleep(10)
    ip = socket.gethostbyname(socket.gethostname())
    node = ChordNode(ip,m=3)

    if len(sys.argv) >= 2:
        other_ip = sys.argv[1]
        #node.join(ChordNodeReference(other_ip, node.port))
    
    while True:
        pass
