# Utiliza la imagen base de Python 3.11
FROM python:3.11-slim

# Copia los archivos al contenedor
COPY run.py /run.py
COPY command.py /command.py
COPY control.py /control.py
COPY table.py /table.py
COPY utils.py /utils.py

# Define el directorio de trabajo
WORKDIR /app

# Define un volumen para los datos
VOLUME /data

# Expone el puerto
EXPOSE 50

# Cambia el CMD para ejecutar el __init__.py de my_package
CMD ["python", "../run.py"]

