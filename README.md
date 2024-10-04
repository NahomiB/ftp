# Sistema FTP distribuido

El Protocolo de Transferencia de Archivos (FTP), definido en el RFC 959, es un protocolo ampliamente utilizado para la transferencia de archivos entre sistemas en red. Sin embargo, la implementación tradicional de un servidor FTP se centra en un enfoque centralizado, lo que puede llevar a limitaciones en cuanto a escalabilidad, disponibilidad y tolerancia a fallos. En este contexto, surge la necesidad de explorar una arquitectura distribuida que permita superar estos retos.

El presente proyecto tiene como objetivo diseñar e implementar un sistema FTP distribuido que cumpla con las especificaciones del RFC 959 y garantice la disponibilidad y seguridad de los datos en un entorno distribuido. El sistema estará compuesto por múltiples nodos, cada uno con un rol específico que puede variar entre almacenamiento de datos, enrutamiento de solicitudes o consulta del estado del sistema, entre otros. Esta distribución de responsabilidades permite una mayor flexibilidad y robustez en la gestión del sistema.

Un aspecto clave del proyecto es asegurar la tolerancia a fallos. Si un nodo de almacenamiento falla, el sistema debe garantizar que los datos no se pierdan, y en caso de que el sistema se divida en varios subsistemas, debe ser capaz de reconectarse y funcionar de manera unificada cuando la comunicación entre los nodos se restablezca.

El sistema será evaluado utilizando Filezilla, lo que permitirá comprobar su compatibilidad con herramientas estándar y su correcto funcionamiento bajo diferentes condiciones de red.

En resumen, este proyecto busca implementar un sistema FTP distribuido que combine los beneficios del protocolo FTP tradicional con la robustez y flexibilidad de un sistema distribuido, asegurando la disponibilidad de datos, tolerancia a fallos y la recuperación de la partición del sistema.

## Arquitectura

El sistema se compone de nodos idénticos en cuanto a sus responsabilidades. Cada nodo actúa tanto como servidor de almacenamiento de archivos como encargado del enrutamiento de solicitudes y gestión de la replicación de datos. Esta organización de nodos homogéneos es un aspecto esencial del diseño, ya que elimina la necesidad de tener nodos dedicados a funciones específicas, lo que simplifica la estructura del sistema y facilita su mantenimiento.

Cada nodo del sistema es responsable de almacenar una porción de los archivos distribuidos en la red. Los archivos se almacenan utilizando un esquema de distribución de claves, en el que una función hash asigna cada archivo a un nodo en particular. Esta técnica asegura que los archivos estén distribuidos de manera equitativa entre los nodos, evitando la sobrecarga en un único nodo. Si un cliente envía una solicitud de archivo, el nodo que la recibe decide si ese archivo está almacenado localmente o si debe redirigir la solicitud a otro nodo que posea el archivo.

La tabla de rutas, implementada en el archivo de código correspondiente, permite que cada nodo tenga información sobre sus sucesores y predecesores. Con esta información, cada nodo es capaz de tomar decisiones eficientes sobre dónde redirigir las solicitudes, optimizando así el proceso de enrutamiento en la red. El enrutamiento de solicitudes dentro del sistema es un proceso distribuido, lo que permite balancear la carga y reducir los tiempos de respuesta, independientemente del número de nodos en la red.

## Replicación de Datos y Tolerancia a Fallos

La replicación de datos es un componente esencial del sistema para asegurar la disponibilidad y durabilidad de los archivos, incluso en caso de fallos de nodos. Cuando un archivo se almacena en un nodo, se genera automáticamente una serie de réplicas de ese archivo en varios nodos sucesores. Esta estrategia garantiza que, si un nodo falla o se desconecta temporalmente, las réplicas del archivo estarán disponibles en otros nodos, permitiendo que el archivo sea accesible para los clientes sin interrupciones.

El proceso de replicación está diseñado para ser robusto, con un mecanismo que se actualiza continuamente. Los nodos envían periódicamente los archivos que almacenan a sus sucesores para asegurar que siempre haya copias actualizadas en diferentes nodos. Esto es especialmente importante en redes donde los nodos pueden desconectarse inesperadamente o donde se espera una alta tolerancia a fallos. Si un nodo no responde, el sistema detecta la desconexión utilizando comandos de verificación, como el comando "PING". Este comando es utilizado por los nodos para monitorear el estado de otros nodos en la red, asegurando que, si un nodo falla, las réplicas se mantengan disponibles en otros lugares de la red.

Además, en caso de un fallo, los nodos sucesores del nodo caído asumen de inmediato las responsabilidades de los archivos que estaban replicados en dicho nodo. Esto asegura que el sistema siga funcionando sin interrupciones y sin pérdida de datos, lo que es crucial para mantener la integridad y confiabilidad del sistema. Cuando un nodo que había fallado vuelve a estar en línea, puede reintegrarse a la red y recuperar su lugar original, manteniendo nuevamente las réplicas actualizadas y participando activamente en la gestión del sistema.

## Comunicación entre Nodos

La comunicación entre los nodos del sistema se realiza utilizando sockets TCP, lo que garantiza una transmisión confiable de datos entre los diferentes nodos. Este tipo de conexión asegura que los paquetes de datos lleguen a su destino sin pérdidas ni errores, lo que es fundamental para el correcto funcionamiento de un sistema distribuido. Los nodos intercambian información mediante el uso de comandos personalizados que permiten gestionar la replicación de archivos, la verificación del estado de los nodos y la resolución de las solicitudes de los clientes.

Algunos de los comandos más importantes incluyen el comando "PING", que se utiliza para verificar si un nodo sigue activo y disponible en la red. Otro comando clave es el "Get Successor", que permite a los nodos encontrar cuál es el sucesor de una clave en la red, para poder enrutar adecuadamente las solicitudes de los clientes. El sistema también utiliza comandos para la replicación de archivos, asegurando que los datos se mantengan distribuidos y disponibles en múltiples nodos en todo momento.

El sistema de comunicación también incluye la funcionalidad de redistribución de tareas en caso de fallo. Si un nodo no responde al comando de verificación, los nodos restantes asumen inmediatamente sus responsabilidades y redistribuyen los archivos y solicitudes de clientes entre los nodos activos. Este proceso garantiza que el sistema sea resistente y continúe funcionando sin interrupciones, incluso en escenarios de fallo.

## Evaluación del Sistema

El sistema será evaluado utilizando el cliente FTP estándar Filezilla para garantizar que cumple con las expectativas de un sistema FTP compatible y funcional. Las pruebas se enfocan en verificar que los archivos puedan ser transferidos de manera eficiente y confiable entre los nodos y que los clientes puedan interactuar con el sistema sin complicaciones. Además, se realizaron pruebas de tolerancia a fallos, simulando la caída de uno o varios nodos y comprobando que los archivos siguen estando disponibles para los clientes, gracias a las réplicas almacenadas en los nodos sucesores.

Otra área importante de evaluación es la escalabilidad del sistema. Se añadieron y eliminaron nodos dinámicamente para verificar que el sistema puede adaptarse a cambios en la topología sin interrumpir el servicio o perder datos. El proceso de enrutamiento y replicación fue monitoreado para asegurar que el sistema distribuye las cargas de manera eficiente y mantiene un alto rendimiento, independientemente del número de nodos en la red.

## Comandos FTP Disponibles

En el sistema FTP distribuido se emplean varios comandos que permiten la interacción entre el cliente y los nodos. Estos comandos se utilizan para gestionar la transferencia de archivos, verificar el estado del sistema, navegar por el directorio y realizar diversas operaciones que permiten una correcta operación del sistema. A continuación, se detallan los comandos más comunes, explicando su función dentro del sistema:

**Comando USER:** Este comando se utiliza al inicio de una sesión FTP para que el cliente envíe su nombre de usuario al servidor. Es el primer paso en el proceso de autenticación. El sistema recibe el nombre de usuario y lo utiliza para verificar si existe una cuenta asociada. Si el usuario es válido, el servidor solicitará la contraseña con el comando correspondiente.

**Comando PASS:** Una vez que el servidor ha recibido el nombre de usuario, solicita la contraseña a través del comando PASS. El cliente envía su contraseña en texto claro, por lo que el uso de FTP estándar no se considera seguro para transferencias sensibles. Sin embargo, este sistema FTP distribuido puede complementarse con medidas adicionales de seguridad, como la encriptación de la conexión mediante TLS, para proteger las credenciales.

**Comando RETR:** Este comando es utilizado para descargar un archivo desde el servidor hacia el cliente. Cuando el cliente envía el comando RETR junto con el nombre del archivo, el nodo responsable de almacenar el archivo lo envía de vuelta al cliente. En el sistema distribuido, si el nodo que recibe la solicitud no tiene el archivo, redirige la solicitud al nodo correcto, asegurando así la disponibilidad del archivo.

**Comando STOR:** El comando STOR permite al cliente subir un archivo desde su máquina local al servidor. El archivo es recibido por el nodo que gestionará su almacenamiento y se replicará automáticamente en varios nodos sucesores para garantizar su disponibilidad. La replicación asegura que, incluso si el nodo original falla, las copias del archivo estén accesibles desde otros nodos en la red.

**Comando LIST:** Este comando devuelve al cliente una lista de los archivos y directorios disponibles en el servidor. El cliente puede enviar el comando LIST para obtener un listado del contenido de un directorio específico, o de todo el sistema de archivos si no se especifica un directorio en particular. La respuesta incluye información básica sobre cada archivo, como su nombre, tamaño y fecha de modificación.

**Comando PWD:** El comando PWD es utilizado para mostrar el directorio de trabajo actual del cliente en el servidor. El cliente puede enviar este comando en cualquier momento para conocer su posición dentro de la jerarquía de directorios del servidor. En respuesta, el servidor envía la ruta completa del directorio actual.

**Comando CWD:** Con el comando CWD, el cliente puede cambiar el directorio de trabajo en el servidor. El cliente debe especificar la ruta del nuevo directorio al que desea acceder. Una vez recibido el comando, el nodo verifica la existencia del directorio y, si es válido, cambia la ruta de trabajo a la solicitada, permitiendo al cliente realizar operaciones en el nuevo directorio.

**Comando QUIT:** Este comando finaliza la sesión FTP entre el cliente y el servidor. Cuando el cliente ya no necesita interactuar con el sistema, envía el comando QUIT para cerrar la conexión de manera ordenada. El nodo que recibe el comando libera los recursos asociados a la sesión y confirma la finalización de la misma.

**Comando MKD:** El comando MKD permite al cliente crear un nuevo directorio en el servidor. El cliente envía el nombre del nuevo directorio y el servidor verifica que no exista un directorio con el mismo nombre en la ruta especificada. Si todo es correcto, el directorio es creado, permitiendo al cliente organizar sus archivos de manera estructurada.

**Comando DELE:** Este comando es utilizado para eliminar un archivo del servidor. El cliente debe proporcionar el nombre del archivo que desea eliminar. El nodo que almacena el archivo verifica si el cliente tiene los permisos necesarios y, si es así, elimina el archivo y todas sus réplicas en los nodos sucesores.

**Comando RMD:** El comando RMD es similar al comando DELE, pero está destinado a la eliminación de directorios. Si el cliente quiere eliminar un directorio, puede usar este comando, siempre que el directorio esté vacío. Si el directorio contiene archivos o subdirectorios, primero deberán ser eliminados antes de poder eliminar el directorio.

**Comando RNFR:** Estos comandos se utilizan en conjunto para renombrar un archivo o directorio en el servidor. El cliente primero envía el comando RNFR para especificar el nombre del archivo o directorio actual. A continuación, el cliente envía el comando RNTO con el nuevo nombre deseado. Si todo es correcto, el servidor realiza el cambio de nombre.

**Comando SYST**: Este comando devuelve información sobre el sistema operativo en el que se ejecuta el servidor FTP. Aunque no es esencial para la mayoría de las operaciones, algunos clientes utilizan esta información para adaptar su comportamiento según las características del sistema subyacente.

**Comando NOOP**: El comando NOOP no realiza ninguna operación en particular, pero es útil para mantener viva la conexión entre el cliente y el servidor en casos de inactividad prolongada. El cliente puede enviar este comando periódicamente para evitar que el servidor cierre la conexión por inactividad.

## Instrucciones de utilización
