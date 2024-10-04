# Utiliza la imagen base de Python 3.11
FROM python:3.11-slim

# Copia los archivos al contenedor
COPY distributed/data_node /app/distributed/data_node/ 
COPY ftp_server/ftp_server.py /app/ftp_server.py

# Define el directorio de trabajo
WORKDIR /app

ENV PYTHONPATH=/app/distributed

# Define un volumen para los datos
VOLUME /data

# Expone el puerto
EXPOSE 50

CMD ["python", "ftp_server.py"]