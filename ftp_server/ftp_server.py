import random
import socket
import threading
import os

# Constantes de manejo del servidor

NUMERO_DE_ESCUCHAS = 5

transferencia_en_progreso = False
cierre_en_progreso = False

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
            elif comando.startswith('PASS'):
                gestionar_comando_contrasenha(socket_cliente, comando)
            elif comando.startswith('ACCT'):
                gestionar_comando_cuenta(socket_cliente)
            elif comando.startswith('REIN'):
                gestionar_comando_reiniciar_sesion(socket_cliente)
            elif comando.startswith('QUIT'):
                gestionar_comando_logout(socket_cliente)
                
            # Comandos de navegación del sistema de archivos
            elif comando.startswith('CWD'):
                directorio_actual = gestionar_comando_cambiar_directorio(comando, directorio_actual, socket_cliente)
            elif comando.startswith('CDUP'):
                directorio_actual = gestionar_comando_cambiar_directorio("CWD ..", directorio_actual, socket_cliente)
            elif comando.startswith('SMNT'):
                gestionar_comando_no_implementado()
            
            
            # Comandos relacionados con la transferencia de archivos
            elif comando.startswith('PORT'):
                socket_datos = gestionar_comando_port(comando, socket_cliente)
            elif comando.startswith('TYPE'):
                tipo_transferencia = gestionar_comando_tipo_transferencia(socket_cliente, comando)
            elif comando.startswith('PASV'):
                socket_datos = gestionar_comando_pasivo(socket_cliente)
            elif comando.startswith('STRU'):
                estructura = gestionar_comando_estructura_archivo(socket_cliente, comando)
            elif comando.startswith('MODE'):
                modo = gestionar_comando_modo_transferencia(socket_cliente, comando)
            
            # Comandos relacionados con servicios de FTP
            
            elif comando.startswith('RETR'):
                gestionar_comando_descargar_archivo(comando[5:].strip(), socket_cliente, socket_datos, directorio_actual)
                socket_datos = None  # Cerrar socket de datos después de descarga
            elif comando.startswith('STOR'):
                gestionar_comando_subir_archivo(comando[5:].strip(), socket_cliente, socket_datos, directorio_actual)
                socket_datos = None
                
            
            elif comando.startswith('NLST') or comando.startswith('LIST'):
                gestionar_comando_listado_directorio(socket_cliente, socket_datos, comando, directorio_actual)
                socket_datos = None  # Resetear socket de datos después de uso
                
            elif comando.startswith('SYST'):
                gestionar_comando_sistema(socket_cliente)

            

            # Comandos de manipulación de archivos y directorios
            elif comando.startswith('PWD'):
                gestionar_comando_pwd(socket_cliente, directorio_actual)
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
    # Esta implementación se puede cambiar si se necesita un usuario para acceder a los datos.
    socket_cliente.send(b'230 Usuario autenticado.\r\n')
    
def gestionar_comando_contrasenha(socket_cliente, comando):
    """
    Maneja el comando PASS, extrayendo la contraseña y realizando la autenticación.
    """
    partes_comando = comando.split(' ', 1)  # Dividir el comando en dos partes: el comando y el resto
    contrasenha = partes_comando[1] if len(partes_comando) > 1 else ''  # Extraer la contraseña

    if contrasenha:  # Comprobar si la contraseña no está vacía
        socket_cliente.send(b'230 Contrasenha aceptada.\r\n')
        # Aquí es donde se debe mejorar la lógica para validar la contraseña si se quiere algo más robusto.
    else:
        socket_cliente.send(b'530 La contrasenha no puede estar vacia.\r\n')  # Enviar error si la contraseña está vacía
           
def gestionar_comando_cuenta(socket_cliente):
    """
    Maneja el comando ACCT, que en algunos sistemas FTP se usa para proporcionar información adicional 
    de la cuenta del usuario. En este caso, no se requiere autenticación adicional y el comando se considera innecesario.

    Envía una respuesta indicando que el comando no es necesario en este servidor.
    """
    socket_cliente.send(b'202 Comando no implementado, innecesario en este sitio.\r\n')
    
def gestionar_comando_reiniciar_sesion(socket_cliente):
    """
    Maneja el comando REIN (Reinitialize), que termina la sesión actual del usuario,
    restablece todos los parámetros a sus valores predeterminados y mantiene abierta la conexión de control.
    """
    try:
        # Restablecer todos los parámetros de la sesión a sus valores predeterminados
        # Se limpia la información de la sesión, eliminando usuario, contraseñas, etc.
        
        # En este caso no se realiza ninguna acción porque no se guardan datos relacionados con la sesión.

        # Enviar mensaje indicando que la sesión ha sido reiniciada y se espera el comando USER
        socket_cliente.send(b'220 Sesion reiniciada. Envie el comando USER para comenzar una nueva sesion.\r\n')
    
    except Exception as e:
        # Manejo de errores
        socket_cliente.send(b'550 Error al reiniciar la sesion.\r\n')

def gestionar_comando_logout(socket_cliente):
    """
    Maneja el comando QUIT (Logout), cerrando la sesión del usuario.
    """
    try:
        if transferencia_en_progreso:
            # Si hay una transferencia en progreso, se mantiene abierta la conexión de control
            cierre_en_progreso = True
            socket_cliente.send(b'226 Transferencia en progreso, la conexion se cerrara al finalizar.\r\n')
        else:
            # No hay transferencias, se puede cerrar la conexión de control
            socket_cliente.send(b'221 Sesion terminada. Cerrando conexion.\r\n')
            socket_cliente.close()  # Cierra la conexión de control
        
    except Exception as e:
        # Manejo de errores
        socket_cliente.send(b'550 Error al cerrar la sesion.\r\n')
        
def gestionar_comando_no_implementado(socket_cliente, comando):
    """
    Maneja comandos no implementados en el servidor FTP.
    """
    # Enviar un mensaje de error 502 (Command not implemented)
    respuesta = f'502 Comando "{comando}" no implementado.\r\n'
    socket_cliente.send(respuesta.encode('utf-8'))  # Enviar respuesta al cliente

def gestionar_comando_cambiar_directorio(comando, directorio_actual, socket_cliente):
    """
    Maneja el comando CWD, cambiando el directorio de trabajo actual. Retorna el nuevo directorio de trabajo si el cambio es exitoso, o el directorio actual si hay un error.
    """
    try:
        nuevo_directorio = os.path.normpath(comando[4:].strip())  # Extrae y normaliza el nuevo directorio del comando
        
        # Maneja el caso de '..' (directorio padre)
        if nuevo_directorio == "..":
            directorio_actual = os.path.dirname(directorio_actual)  # Cambia al directorio padre
        else:
            # Intenta crear el nuevo camino combinado del directorio actual con el nuevo
            directorio_potencial = os.path.normpath(os.path.join(directorio_actual, nuevo_directorio))
            
            # Verifica si el nuevo directorio existe y es accesible
            if os.path.isdir(directorio_potencial):
                directorio_actual = directorio_potencial
                socket_cliente.send(b'250 Directorio cambiado con exito.\r\n')
            else:
                socket_cliente.send(b'550 El directorio no existe o no es accesible.\r\n')
        
    except Exception as e:
        # Enviar un mensaje de error en caso de un problema inesperado
        socket_cliente.send(b'550 Error al cambiar de directorio.\r\n')

    return directorio_actual

def gestionar_comando_port(comando, cliente_socket):
    """
    Maneja el comando PORT, estableciendo una conexión entre el cliente y el servidor.
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
   
def gestionar_comando_pasivo(socket_cliente, rango_puertos=(40500, 40600)):
    """
    Maneja el comando PASV, creando un socket en un puerto dentro de un rango especificado
    y enviando al cliente la información sobre el modo pasivo.
    """

    # Intenta encontrar un puerto disponible dentro del rango especificado
    for puerto in random.sample(range(*rango_puertos), rango_puertos[1] - rango_puertos[0]):
        try:
            # Crear un socket para la conexión de datos
            socket_datos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_datos.bind(('0.0.0.0', puerto))  # Asigna el puerto disponible
            socket_datos.listen(1)  # Escucha conexiones entrantes
            break
        except OSError:
            continue  # Intenta con el siguiente puerto en caso de error
    else:
        # Si no se encontró un puerto disponible, lanza un error
        raise IOError("No hay puertos disponibles en el rango especificado")

    # Obtiene el número de puerto en el que está escuchando
    puerto = socket_datos.getsockname()[1]
    print(f"Escuchando en el puerto: {puerto}")

    # Prepara la dirección IP y la respuesta para el cliente
    ip = socket_cliente.getsockname()[0]  # Obtiene la dirección IP del servidor
    p1, p2 = divmod(puerto, 256)  # Calcula los bytes del puerto
    respuesta = f"227 Entrando en Modo Pasivo ({ip.replace('.', ',')},{p1},{p2}).\r\n"
    socket_cliente.send(respuesta.encode('utf-8'))  # Envía la respuesta al cliente

    # Acepta la conexión de datos del cliente
    socket_datos_cliente, addr = socket_datos.accept()
    print(f"Conexión de datos aceptada desde: {addr}")

    return socket_datos_cliente

def gestionar_comando_tipo_transferencia(socket_cliente, comando):
    """
    Maneja el comando TYPE, cambiando el tipo de transferencia según lo especificado en la sección de Representación y Almacenamiento de Datos.
    """

    # Definición de tipos de transferencia y su valor por defecto
    tipo_predeterminado = 'A N'  # ASCII No imprimible por defecto
    tipo_transferencia = tipo_predeterminado  # Inicializa con el tipo predeterminado

    # Procesa el comando TYPE
    partes_comando = comando.split()
    
    if len(partes_comando) == 2:  # Solo un parámetro (tipo)
        tipo_transferencia = partes_comando[1]
        
        if tipo_transferencia == 'I':
            socket_cliente.send(b'200 Tipo de transferencia: imagen.\r\n')
        elif tipo_transferencia == 'A':
            socket_cliente.send(b'200 Tipo de transferencia: ASCII.\r\n')
        elif tipo_transferencia == 'N':
            socket_cliente.send(b'200 Tipo de transferencia: no imprimible.\r\n')
        elif tipo_transferencia == 'E':
            socket_cliente.send(b'200 Tipo de transferencia: EBCDIC.\r\n')
        elif tipo_transferencia == 'L':
            socket_cliente.send(b'200 Tipo de transferencia: byte local.\r\n')
        else:
            socket_cliente.send(b'504 Comando no implementado.\r\n')
    
    elif len(partes_comando) == 3:  # Dos parámetros (tipo y segundo parámetro)
        tipo_transferencia = partes_comando[1]
        segundo_parametro = partes_comando[2]

        if tipo_transferencia == 'A':
            # Maneja ASCII con el segundo parámetro
            if segundo_parametro == 'T':
                socket_cliente.send(b'200 Tipo de transferencia: ASCII, efectores de formato Telnet.\r\n')
            else:
                socket_cliente.send(b'504 Comando no implementado.\r\n')
        elif tipo_transferencia == 'I':
            # Maneja el modo imagen
            socket_cliente.send(b'200 Tipo de transferencia: imagen.\r\n')
        elif tipo_transferencia == 'L':
            # Maneja el byte local y espera un tamaño
            try:
                tamaño_byte = int(segundo_parametro)
                socket_cliente.send(b'200 Tipo de transferencia: byte local de tamanho {}.\r\n'.format(tamaño_byte).encode('utf-8'))
            except ValueError:
                socket_cliente.send(b'501 Error en el tamanho del byte local.\r\n')
        else:
            socket_cliente.send(b'504 Comando no implementado.\r\n')

    else:
        socket_cliente.send(b'501 Sintaxis de comando invalida.\r\n')

    # Si se cambia solo el primer argumento a algo diferente a 'A', el formato vuelve al predeterminado
    if len(partes_comando) == 2 and partes_comando[1] != 'A':
        tipo_transferencia = tipo_predeterminado
        
    return tipo_transferencia

def gestionar_comando_estructura_archivo(socket_cliente, comando):
    """
    Responde al comando STRU, cambiando la estructura del archivo.
    La estructura predeterminada es File.
    """
    estructuras_permitidas = {
        'F': 'Archivo (sin estructura de registros)',
        'R': 'Estructura de registros',
        'P': 'Estructura de página'
    }
    
    # Estructura predeterminada
    estructura_actual = 'F'  # File

    # Procesa el comando STRU
    partes_comando = comando.split()

    if len(partes_comando) == 2:  # Un argumento
        estructura = partes_comando[1]
        
        if estructura in estructuras_permitidas:
            estructura_actual = estructura
            respuesta = f'200 Estructura del archivo cambiada a: {estructuras_permitidas[estructura]}.\r\n'
            socket_cliente.send(respuesta.encode('utf-8'))
        else:
            socket_cliente.send(b'504 Comando no implementado. Estructura no valida.\r\n')
    else:
        socket_cliente.send(b'501 Sintaxis de comando invalida.\r\n')
        
    return estructura_actual

def gestionar_comando_modo_transferencia(socket_cliente, comando):
    """
    Responde al comando MODE, cambiando el modo de transferencia de datos.
    El modo predeterminado es Stream.
    """
    modos_permitidos = {
        'S': 'Transmisión en flujo',
        'B': 'Bloque',
        'C': 'Comprimido'
    }
    
    # Modo predeterminado
    modo_actual = 'S'  # Stream

    # Procesa el comando MODE
    partes_comando = comando.split()

    if len(partes_comando) == 2:  # Un argumento
        modo = partes_comando[1]
        
        if modo in modos_permitidos:
            modo_actual = modo
            respuesta = f'200 Modo de transferencia cambiado a: {modos_permitidos[modo]}.\r\n'
            socket_cliente.send(respuesta.encode('utf-8'))
        else:
            socket_cliente.send(b'504 Comando no implementado. Modo no valido.\r\n')
    else:
        socket_cliente.send(b'501 Sintaxis de comando invalida.\r\n')

    return modo_actual

def gestionar_comando_sistema(socket_cliente):
    """Responde al comando SYST, indicando el tipo de sistema operativo del servidor."""
    socket_cliente.send(b'215 UNIX Type: L8\r\n')

def gestionar_comando_pwd(socket_cliente, directorio_actual):
    """Responde al comando PWD, enviando el directorio de trabajo actual."""
    socket_cliente.send(f'257 "{directorio_actual}" es el directorio actual.\r\n'.encode())

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
