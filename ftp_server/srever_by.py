import os

class MiServidorFTP:
    def __init__(self):
        # Define la ruta inicial
        self.current_dir = r'C:\blabla\ftp'  # Usar una raw string para evitar problemas con las barras invertidas
        self.current_dir = os.path.normpath(self.current_dir)  # Normaliza la ruta

    def listar_archivos(self):
        try:
            # Listar archivos en el directorio actual
            file_list = os.listdir(self.current_dir)
            print("Archivos en el directorio:", file_list)
        except FileNotFoundError:
            print("El directorio no existe.")

# Crear una instancia del servidor FTP y listar archivos
servidor = MiServidorFTP()
servidor.listar_archivos()