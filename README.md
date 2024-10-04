# Sistema FTP distribuido

El Protocolo de Transferencia de Archivos (FTP), definido en el RFC 959, es un protocolo ampliamente utilizado para la transferencia de archivos entre sistemas en red. Sin embargo, la implementación tradicional de un servidor FTP se centra en un enfoque centralizado, lo que puede llevar a limitaciones en cuanto a escalabilidad, disponibilidad y tolerancia a fallos. En este contexto, surge la necesidad de explorar una arquitectura distribuida que permita superar estos retos.

El presente proyecto tiene como objetivo diseñar e implementar un sistema FTP distribuido que cumpla con las especificaciones del RFC 959 y garantice la disponibilidad y seguridad de los datos en un entorno distribuido. El sistema estará compuesto por múltiples nodos, cada uno con un rol específico que puede variar entre almacenamiento de datos, enrutamiento de solicitudes o consulta del estado del sistema, entre otros. Esta distribución de responsabilidades permite una mayor flexibilidad y robustez en la gestión del sistema.

Un aspecto clave del proyecto es asegurar la tolerancia a fallos. Si un nodo de almacenamiento falla, el sistema debe garantizar que los datos no se pierdan, y en caso de que el sistema se divida en varios subsistemas, debe ser capaz de reconectarse y funcionar de manera unificada cuando la comunicación entre los nodos se restablezca.

El sistema será evaluado utilizando Filezilla, lo que permitirá comprobar su compatibilidad con herramientas estándar y su correcto funcionamiento bajo diferentes condiciones de red.

En resumen, este proyecto busca implementar un sistema FTP distribuido que combine los beneficios del protocolo FTP tradicional con la robustez y flexibilidad de un sistema distribuido, asegurando la disponibilidad de datos, tolerancia a fallos y la recuperación de la partición del sistema.

## Arquitectura

## Instrucciones de utilización
