import streamlit as st
import sqlite3
from sqlalchemy import create_engine, Column, Integer, Text, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

def buscar_documentos(query):
    pass

def mostrar_documento(documentos):
    pass

def listar_archivos(directorio):
    pass

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