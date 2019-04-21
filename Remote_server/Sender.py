import os
import socket


class Sender:
    """
    Class for sending information/files to remote file server implemented in Server.py
    """

    def __init__(self):
        """
        Initialize socket.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_zip(self, remote_ipv4, remote_port, zip_file: bytes = None):
        """
        Sends zip file to file server.
        After receiving file, its contents are unziped and copied into appropriate directory.

        :param remote_ipv4: File server ipv4 address.
        :param remote_port: FIle server port.
        :param zip_file: File to send.
        :return: None
        """
        self.socket.connect((remote_ipv4, remote_port))
        file_size = len(zip_file)
        self.socket.send(b"FILE/ZIP/" + str(file_size).encode())
        response = self.socket.recv(512)
        print(response)
        for index in range(0, file_size, 512):
            file_content = zip_file[index:index + 512]
            print(len(file_content))
            print(self.socket.send(file_content))


""" TEST
sender = Sender()
with open("../large.zip", "rb") as file:
    sender.send_zip("192.168.0.3", 10000, file.read())

"""
