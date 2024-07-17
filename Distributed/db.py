import sqlite3

# Crear la conexión a la base de datos
conn = sqlite3.connect('mi_base_de_datos.db')
cursor = conn.cursor()

# Crear la tabla (si aún no existe)
cursor.execute("""
CREATE TABLE IF NOT EXISTS mi_tabla (
  id INTEGER,
  titule TEXT,
  document BLOB,
  nodo_id INTEGER,
  PRIMARY KEY (id)
)
""")

# Definir un objeto de Python
class Documento:
    def __init__(self, id, titule, document, nodo_id):
        self.id = id
        self.titule = titule
        self.document = document
        self.nodo_id = nodo_id

# Crear un objeto Documento
mi_documento = Documento(1, "Mi título", b'\x01\x23\x45\x67\x89\xAB\xCD\xEF', 456)

# Insertar el objeto en la tabla
cursor.execute("INSERT INTO mi_tabla (id, titule, document, nodo_id) VALUES (?, ?, ?, ?)", 
               (mi_documento.id, mi_documento.titule, mi_documento.document, mi_documento.nodo_id))

# Guardar los cambios
conn.commit()

# Cerrar la conexión
conn.close()