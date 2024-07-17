import os
import sqlite3
import pickle
from sqlalchemy import create_engine, Column, Integer, Text, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

class Documento:
    def __init__(self, id, titule, document, nodo_id):
        self.id = id
        self.titule = titule
        self.document = document
        self.nodo_id = nodo_id

class GestorDB:
    def __init__(self):
        self.cache_file = 'cache.pkl'
        self.actual_file = 'actual.pkl'
        self.create_files_if_not_exist()

        # Cargar cache y actual desde disco
        self.cache = self.load_from_disk(self.cache_file, {})
        self.actual = self.load_from_disk(self.actual_file, {})

    def create_files_if_not_exist(self):
        if not os.path.exists(self.cache_file):
            self.create_cache_file()
        if not os.path.exists(self.actual_file):
            self.create_actual_file()

    def create_cache_file(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump({}, f)
        print(f"Archivo {self.cache_file} creado exitosamente.")

    def create_actual_file(self):
        with open(self.actual_file, 'wb') as f:
            pickle.dump({}, f)
        print(f"Archivo {self.actual_file} creado exitosamente.")

    def load_cache(self):
        with open(self.cache_file, 'rb') as f:
            cache = pickle.load(f)
        return cache

    def load_actual(self):
        with open(self.actual_file, 'rb') as f:
            actual = pickle.load(f)
        return actual

    def save_cache(self, cache):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(cache, f)

    def save_actual(self, actual):
        with open(self.actual_file, 'wb') as f:
            pickle.dump(actual, f)

    def agregar_documento(self, documento):
        """
        Agrega un nuevo documento a los datos actuales.
        
        Args:
            documento (Documento): El documento a agregar.
        """
        self.actual[documento.titule] = documento.__dict__
        self.save_actual(self.actual)

    def extraer_documento(self, titulo):
        """
        Extrae un documento de los datos actuales.
        
        Args:
            titulo (str): El título del documento a extraer.
        
        Returns:
            Documento: El documento extraído, o None si no se encuentra.
        """
        if titulo in self.actual:
            documento_dict = self.actual.pop(titulo)
            self.save_actual(self.actual)
            return Documento(**documento_dict)
        else:
            return None

    def buscar_documentos(self, query):
        resultados = []
        for documento in self.actual.values():
            if query.lower() in documento['titule'].lower():
                resultados.append(Documento(**documento))
        return resultados

    def mostrar_documento(self, documento):
        return documento.document

    def listar_archivos(self, directorio):
        archivos = os.listdir(directorio)
        return archivos

    def migrar_de_actual_a_cache(self):
        self.cache.update(self.actual)
        self.actual.clear()
        self.save_to_disk(self.cache, self.cache_file)
        self.save_to_disk(self.actual, self.actual_file)

    def limpiar_actual(self):
        self.actual.clear()
        self.save_to_disk(self.actual, self.actual_file)

    def load_from_disk(self, file_path, default=None):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        return default

    def save_to_disk(self, data, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)



gestor = GestorDB()
documento = Documento(1, 'Documento 1', 'Este es el contenido del documento 1.', 1)
gestor.agregar_documento(documento)
extraido = gestor.extraer_documento('Documento 1')
if extraido:
    print(gestor.mostrar_documento(extraido))
else:
    print('Documento no encontrado.')