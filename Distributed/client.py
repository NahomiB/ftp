import streamlit as st
import sqlite3
from sqlalchemy import create_engine, Column, Integer, Text, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Crear el motor de base de datos
engine = create_engine('sqlite:///mi_base_de_datos.db')

# Crear una sesión
Session = sessionmaker(bind=engine)
session = Session()

# Crear la base declarativa
Base = declarative_base()

# Definir el modelo de la tabla
class MiTabla(Base):
    __tablename__ = 'mi_tabla'

    id = Column(Integer, primary_key=True)
    titulo = Column(Text)
    documento = Column(LargeBinary)
    nodo_id = Column(Integer)

# Crear la tabla si no existe
Base.metadata.create_all(engine)

# Función para buscar documentos relevantes
def buscar_documentos(query):
    resultados = session.query(MiTabla).filter(MiTabla.titulo.contains(query)).all()
    return resultados

# Función para mostrar el contenido del documento
def mostrar_documento(documento):
    st.write(documento.decode('utf-8'))

# Función para listar los archivos del servidor
def listar_archivos(directorio):
    archivos = os.listdir(directorio)
    return archivos

# Crear la interfaz de usuario
st.title("Mi Cliente")

# Crear las pestañas
tabs = st.tabs(["Buscar Documentos", "Gestor de Archivos"])

with tabs[0]:
    st.subheader("Buscar Documentos")
    query = st.text_input("Ingresa una consulta:")
    if st.button("Buscar"):
        resultados = buscar_documentos(query)
        for resultado in resultados:
            if st.button(resultado.titulo, key=resultado.id):
                mostrar_documento(resultado.documento)

with tabs[1]:
    st.subheader("Gestor de Archivos")
    directorio = st.text_input("Ingresa la ruta del directorio:")
    if st.button("Listar Archivos"):
        archivos = listar_archivos(directorio)
        for archivo in archivos:
            st.write(archivo)