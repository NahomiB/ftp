import os
import ftplib
from chord import ChordNode

class FTPServer:
    def __init__(self, host, port, chord_nodes):
        self.host = host
        self.port = port
        self.ftp = ftplib.FTP()
        self.chord_nodes = chord_nodes

    def start(self):
        self.ftp.connect(self.host, self.port)
        self.ftp.login()
        self.ftp.cwd('/uploads')

    def upload(self, file_path):
        key = hash(file_path)
        successor = self.find_successor(key)
        with open(file_path, 'rb') as file:
            self.ftp.storbinary('STOR ' + os.path.basename(file_path), file)
            successor.upload(file_path)

    def download(self, file_path):
        key = hash(file_path)
        successor = self.find_successor(key)
        with open(file_path, 'wb') as file:
            self.ftp.retrbinary('RETR ' + os.path.basename(file_path), file.write)
            successor.download(file_path)

    def find_successor(self, key):
        for node in self.chord_nodes:
            if node.id >= key:
                return node
        return self.chord_nodes[0]

    def close(self):
        self.ftp.quit()



