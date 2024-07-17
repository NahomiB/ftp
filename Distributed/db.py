from sqlalchemy import create_engine, Column, Integer, Text, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Crear el motor de base de datos
engine = create_engine('sqlite:///mi_base_de_datos.db')

# Crear una sesión
Session = sessionmaker(bind=engine)
session = Session()

# Crear la base declarativa
Base = declarative_base()

# Definir el modelo de la tabla
class MiTabla(Base):
    __tablename__ = 'mi_tabla'

    id = Column(Integer, primary_key=True)
    titule = Column(Text)
    document = Column(LargeBinary)
    nodo_id = Column(Integer)

# Crear la tabla si no existe
Base.metadata.create_all(engine)

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
nueva_fila = MiTabla(id=mi_documento.id, titule=mi_documento.titule, document=mi_documento.document, nodo_id=mi_documento.nodo_id)
session.add(nueva_fila)
session.commit()

# Cerrar la sesión
session.close()