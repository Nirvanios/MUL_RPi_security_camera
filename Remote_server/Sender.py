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

    def send_zip(self, remote_ipv4, remote_port, zip_file: bytes):
        """
        Sends zip file to file server.
        After receiving file, its contents are unziped and copied into appropriate directory.

        :param remote_ipv4: File server ipv4 address.
        :param remote_port: FIle server port.
        :param zip_file: File to send.
        :return: None
        """
        self.socket.connect((remote_ipv4, remote_port))
        self.socket.settimeout(10.0)
        file_size = len(zip_file)
        self.socket.send(b"FILE/ZIP/" + str(file_size).encode() + b"/tmp.zip")
        response = self.socket.recv(512)
        self.__send_file(file_size, zip_file)
        self.socket.close()

    def send_standard_file(self, remote_ipv4, remote_port, file_name: str, file: bytes):
        """
        Sends simple file to file server. Server wont unpack just saves.

        :param remote_ipv4: File server ipv4 address.
        :param remote_port: FIle server port.
        :param file_name: Name of the file.
        :param file: File to send.
        :return: None
        """
        self.socket.connect((remote_ipv4, remote_port))
        self.socket.settimeout(10.0)
        file_size = len(file)
        self.socket.send(b"FILE/STD/" + str(file_size).encode() + b"/" + file_name.encode())
        response = self.socket.recv(512)
        self.__send_file(file_size, file)
        self.socket.close()

    def __send_file(self, file_size: int, file: bytes):
        """
        Private function for file sending

        :param file_size: Size of file in bytes
        :param file: Actual file
        :return: None
        """
        for index in range(0, file_size, 512):
            file_content = file[index:index + 512]
            self.socket.send(file_content)


""" TEST
sender = Sender()
with open("../large.zip", "rb") as file:
    sender.send_standard_file("192.168.0.3", 10000, "large.zip", file.read())
"""
