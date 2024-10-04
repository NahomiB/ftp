# Utiliza la imagen base de Python 3.11
FROM python:3.11-slim

# Copia los archivos al contenedor
<<<<<<< HEAD:Distributed/data_node/init_storage.dockerfile
COPY run.py /run.py
COPY command.py /command.py
COPY control.py /control.py
COPY table.py /table.py
COPY utils.py /utils.py
=======
COPY . /app
>>>>>>> 613d42f4c424481a7854f053a828dc6542514817:init_storage.dockerfile

# Define el directorio de trabajo
WORKDIR /app

ENV PYTHONPATH=/app

# Define un volumen para los datos
VOLUME /data

# Expone el puerto
EXPOSE 50

<<<<<<< HEAD:Distributed/data_node/init_storage.dockerfile
# Cambia el CMD para ejecutar el __init__.py de my_package
CMD ["python", "../run.py"]

=======
CMD ["python", "init.py"]
>>>>>>> 613d42f4c424481a7854f053a828dc6542514817:init_storage.dockerfile
