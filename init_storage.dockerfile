# Utiliza la imagen base de Python 3.11
FROM python:3.11-slim

# Copia los archivos al contenedor
COPY . /app

# Define el directorio de trabajo
WORKDIR /app

ENV PYTHONPATH=/app

# Define un volumen para los datos
VOLUME /data

# Expone el puerto
EXPOSE 50

CMD ["python", "init.py"]