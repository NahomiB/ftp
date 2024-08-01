import ftplib
import os

class FTPServer:
    def __init__(self, host, port, user, password, root_dir):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.root_dir = root_dir

    def start(self):
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.host, self.port)
        self.ftp.login(self.user, self.password)
        self.ftp.cwd(self.root_dir)
        print(f"FTP server started on {self.host}:{self.port}")

    def stop(self):
        self.ftp.quit()
        print("FTP server stopped")

    def handle_client(self, cmd, filename, file_data=None):
        if cmd == 'RETR':
            with open(os.path.join(self.root_dir, filename), 'rb') as f:
                self.ftp.retrbinary(f'RETR {filename}', f.read)
        elif cmd == 'STOR':
            with open(os.path.join(self.root_dir, filename), 'wb') as f:
                self.ftp.storbinary(f'STOR {filename}', file_data)
        else:
            self.ftp.sendcmd(cmd)