import socket
import threading
import os

# Constantes de manejo del servidor

NUMERO_DE_ESCUCHAS = 5

# Constantes de respuesta del servidor
RESPUESTA_USUARIO_OK = b'230 Usuario autenticado.\r\n'
RESPUESTA_NO_IMPLEMENTADO = b'500 Comando no implementado.\r\n'
RESPUESTA_SISTEMA = b'215 UNIX Type: L8\r\n'
RESPUESTA_UTF8_OK = b'200 UTF8 habilitado.\r\n'
RESPUESTA_CAMBIO_DIRECTORIO_OK = b'250 Directorio cambiado con exito.\r\n'
RESPUESTA_ERROR_SINTAXIS = b'500 Error de sintaxis, comando no reconocido.\r\n'


def gestionar_conexion_cliente(socket_cliente):
    """
    Gestiona la conexión de un cliente FTP, recibiendo comandos, interpretándolos 
    y enviando respuestas según la funcionalidad del servidor.
    """
    directorio_actual = os.path.normpath("/app")  # Directorio de trabajo inicial
    socket_datos = None  # Inicializar socket de datos

    try:
        while True:
            comando = socket_cliente.recv(1024).decode().strip()  # Recibir comando del cliente
            print(f"Comando recibido: {comando}")
            
            # Procesar el comando recibido
            if comando.startswith('USER'):
                gestionar_comando_usuario(socket_cliente)
            elif comando.startswith('AUTH'):
                gestionar_comando_autenticacion(socket_cliente, comando)
            elif comando.startswith('SYST'):
                gestionar_comando_sistema(socket_cliente)
            elif comando.startswith('FEAT'):
                gestionar_comando_caracteristicas(socket_cliente)
            elif comando.startswith('OPTS UTF8 ON'):
                gestionar_comando_utf8(socket_cliente)
            
            # Comandos relacionados con la transferencia de archivos
            elif comando.startswith('TYPE'):
                gestionar_comando_tipo_transferencia(socket_cliente, comando)
            elif comando.startswith('PORT'):
                socket_datos = gestionar_comando_port(comando, socket_cliente)
            elif comando.startswith('PASV'):
                socket_datos = gestionar_comando_pasivo(socket_cliente)
            elif comando.startswith('RETR'):
                gestionar_comando_descargar_archivo(comando[5:].strip(), socket_cliente, socket_datos, directorio_actual)
                socket_datos = None  # Cerrar socket de datos después de descarga
            elif comando.startswith('STOR'):
                gestionar_comando_subir_archivo(comando[5:].strip(), socket_cliente, socket_datos, directorio_actual)
                socket_datos = None

            # Comandos de navegación del sistema de archivos
            elif comando.startswith('PWD'):
                gestionar_comando_pwd(socket_cliente, directorio_actual)
            elif comando.startswith('CWD'):
                directorio_actual = gestionar_comando_cambiar_directorio(comando, directorio_actual, socket_cliente)
            elif comando.startswith('NLST') or comando.startswith('LIST'):
                gestionar_comando_listado_directorio(socket_cliente, socket_datos, comando, directorio_actual)
                socket_datos = None  # Resetear socket de datos después de uso

            # Comandos de manipulación de archivos y directorios
            elif comando.startswith('DELE'):
                gestionar_comando_eliminar_archivo(comando[5:].strip(), socket_cliente, directorio_actual)
            elif comando.startswith('MKD'):
                gestionar_comando_crear_directorio(comando[4:].strip(), socket_cliente, directorio_actual)
            elif comando.startswith('RMD'):
                gestionar_comando_eliminar_directorio(comando[4:].strip(), socket_cliente, directorio_actual)
            elif comando.startswith('RNFR'):
                gestionar_comando_renombrar_archivo(comando[5:].strip(), socket_cliente, directorio_actual)

            # Si el comando no es reconocido
            else:
                socket_cliente.send(RESPUESTA_ERROR_SINTAXIS)
    except (ConnectionAbortedError, ConnectionResetError):
        print("Conexión perdida con el cliente.")
    finally:
        if socket_datos:
            socket_datos.close()
        socket_cliente.close()

# Funciones que gestionan comandos específicos del servidor FTP

def gestionar_comando_usuario(socket_cliente):
    """Responde al comando USER, autenticando al cliente sin requerir contraseña."""
    socket_cliente.send(RESPUESTA_USUARIO_OK)

def gestionar_comando_autenticacion(socket_cliente, comando):
    """Responde al comando AUTH, rechazando solicitudes de TLS/SSL."""
    socket_cliente.send(RESPUESTA_NO_IMPLEMENTADO)

def gestionar_comando_sistema(socket_cliente):
    """Responde al comando SYST, indicando el tipo de sistema operativo del servidor."""
    socket_cliente.send(RESPUESTA_SISTEMA)

def gestionar_comando_caracteristicas(socket_cliente):
    """Responde al comando FEAT, enviando las características compatibles con el servidor."""
    caracteristicas = "211-Características:\r\n PASV\r\n UTF8\r\n211 Fin\r\n"
    socket_cliente.send(caracteristicas.encode())

def gestionar_comando_pwd(socket_cliente, directorio_actual):
    """Responde al comando PWD, enviando el directorio de trabajo actual."""
    socket_cliente.send(f'257 "{directorio_actual}" es el directorio actual.\r\n'.encode())

def gestionar_comando_utf8(socket_cliente):
    """Responde al comando OPTS UTF8 ON, habilitando UTF-8 en el servidor."""
    socket_cliente.send(RESPUESTA_UTF8_OK)

def gestionar_comando_listado_directorio(socket_cliente, socket_datos, comando, directorio_actual):
    """
    Responde a los comandos NLST y LIST, enviando la lista de archivos en el directorio actual.
    Si se proporciona un socket de datos, se envía el listado a través de él.
    """
    if socket_datos:
        argumentos = comando.split()
        directorio = directorio_actual if len(argumentos) == 1 else os.path.normpath(argumentos[1])
        enviar_listado_directorio(socket_cliente, socket_datos, directorio)
        socket_datos.close()

def gestionar_comando_tipo_transferencia(socket_cliente, comando):
    """
    Responde al comando TYPE, cambiando el tipo de transferencia entre modo binario (I) y ASCII (A).
    """
    if comando.startswith('TYPE I'):
        socket_cliente.send(b'200 Tipo de transferencia: binario.\r\n')
    elif comando.startswith('TYPE A'):
        socket_cliente.send(b'200 Tipo de transferencia: ASCII.\r\n')

def gestionar_comando_cambiar_directorio(comando, directorio_actual, socket_cliente):
    """
    Responde al comando CWD, cambiando el directorio de trabajo actual.
    """
    nuevo_directorio = os.path.normpath(comando[4:].strip())  # Extrae el nuevo directorio del comando
    if directorio_actual != os.path.normpath("/app") or nuevo_directorio != "..":
        directorio_actual = os.path.normpath(os.path.join(directorio_actual, nuevo_directorio))
    socket_cliente.send(RESPUESTA_CAMBIO_DIRECTORIO_OK)
    return directorio_actual

def gestionar_comando_port(comando, cliente_socket):
    """
    Maneja el comando PORT, estableciendo una conexión entre el cliente y el servidor.
    
    Parámetros:
    comando -- El comando PORT recibido del cliente (incluye la dirección IP y puerto).
    cliente_socket -- El socket del cliente que envió el comando.
    
    Retorna:
    data_socket -- El socket de datos que se ha establecido con el cliente.
    """
    # Dividir el comando para obtener los componentes
    partes_direccion = comando.split()[1].split(',')
    
    direccion_ip = '.'.join(partes_direccion[:4])
    
    # Calcular el puerto a partir de las dos últimas partes del comando
    puerto_datos = int(partes_direccion[4]) * 256 + int(partes_direccion[5])

    try:
    # Crear un socket de datos para conectarse al cliente
        socket_datos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_datos.connect((direccion_ip, puerto_datos))
        
        # Enviar un mensaje 200 si la conexión fue exitosa
        cliente_socket.send(b'200 Comando PORT ejecutado con exito.\r\n')
        
    except socket.error:
        # Enviar un mensaje 425 si la conexión falla
        cliente_socket.send(b'425 No se pudo abrir la conexion de datos.\r\n')
        socket_datos = None  # Asegurarse de que el socket de datos no se use en caso de error

    return socket_datos
    

def manejar_conexiones_entrantes(servidor_socket):
    """
    Espera conexiones entrantes de los clientes FTP y lanza un nuevo hilo para cada cliente.
    """
    print("Servidor FTP en espera de conexiones...")
    while True:
        # Acepta una nueva conexión
        cliente_socket, direccion_cliente = servidor_socket.accept()
        print(f"Nueva conexión aceptada desde: {direccion_cliente}")
        
        # Envía mensaje de bienvenida al cliente
        cliente_socket.send(b"220 Bienvenido al servidor FTP.\r\n")
        
        # Crea un nuevo hilo para manejar la conexión del cliente
        hilo_cliente = threading.Thread(target=gestionar_conexion_cliente, args=(cliente_socket,))
        hilo_cliente.daemon = True  # Permite que el hilo se cierre cuando el programa principal termina
        hilo_cliente.start()
        
def configurar_socket_servidor(host='0.0.0.0', puerto=21):
    """
    Configura el socket de control del servidor FTP para aceptar conexiones de clientes.
    
    Parámetros:
    host -- Dirección IP en la que el servidor escucha (por defecto '0.0.0.0', todas las interfaces)
    puerto -- Puerto en el que el servidor escucha (por defecto 21, puerto FTP estándar)
    
    Retorna:
    server_socket -- El socket configurado para aceptar conexiones de clientes
    """
    try:
        # Crear un socket TCP/IP
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Vincular el socket a la dirección y puerto proporcionados
        servidor.bind((host, puerto))
    except OSError:
        # Si el puerto no está disponible, asignar uno dinámicamente
        print("El puerto especificado no está disponible, asignando un puerto dinámico.")
        servidor.bind((host, 0))

    # Escuchar hasta 5 conexiones entrantes
    servidor.listen(NUMERO_DE_ESCUCHAS)
    
    # Obtener el puerto final en el que está escuchando el servidor
    puerto_final = servidor.getsockname()[1]
    print(f"Servidor escuchando en {host}:{puerto_final}")
    
    return servidor
    

def iniciar_servidor_ftp():
    """
    Configura el servidor FTP y comienza a aceptar conexiones entrantes.
    """
    # Inicializa el socket de control para manejar las conexiones de los clientes
    servidor_socket = configurar_socket_servidor()
    
    # Lanza un hilo separado para mantener la lista de nodos de almacenamiento actualizada
    hilo_nodos_almacenamiento = threading.Thread(target=actualizar_nodos_almacenamiento)
    hilo_nodos_almacenamiento.daemon = True  # Hace que el hilo termine cuando el programa termina
    hilo_nodos_almacenamiento.start()
    
    # Comienza a aceptar conexiones de clientes
    manejar_conexiones_entrantes(servidor_socket)

if __name__ == "__main__":
    iniciar_servidor_ftp()
