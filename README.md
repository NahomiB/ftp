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

## Instrucciones de utilización
