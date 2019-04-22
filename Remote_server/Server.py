import errno
import socketserver
import argparse
import re
import zipfile
import datetime
import os
import io


def init_arg_parse():
    """
    Initialize argument parser.
    :return: Parser
    """
    parser = argparse.ArgumentParser(description="MUL project")
    parser.add_argument("--ip", required=True, dest='ip', type=str)
    parser.add_argument("--port", required=True, dest='port', type=int)
    parser.add_argument("--dir", required=False, default="/home/pi/image_server/", dest='dir', type=str, )
    return parser


class TCPMessageHandler(socketserver.StreamRequestHandler):
    """
    Handler class for all incoming messages.
    Protocol:   FILE/ZIP/*file_length* - receives and unzip file into selected "out_dir/date_now" directory.
                # TODO single file received
                # TODO hellos from companion app
    """
    dir_path = ""

    def handle(self):
        """
        Reimplemented method that handles incoming messages.
        Right now accepts only zip files.

        :return: None
        """

        message_string = self.request.recv(1024).strip()
        print("Handling..." + str(message_string))
        if re.search(b"FILE/.+/", message_string):  # Handling file

            # find file size
            file_size = int(re.search(b"(?<=FILE/(STD|ZIP)/)[0-9]+(?=/)", message_string).group(0).decode())

            self.wfile.write(b"ACK")

            file_content_path = self.dir_path + str(datetime.datetime.now().strftime("%Y-%m-%d %H") + ":00")
            with io.BytesIO() as file:  # Receive file to buffer
                for _ in range(0, file_size, 512):
                    file_content = self.request.recv(file_size)
                    file.write(file_content)

                if not os.path.isdir(file_content_path):
                    os.makedirs(file_content_path)

                #  Saves file to disk
                file.seek(0)
                file_name = re.split(b"FILE/.+/.+/", message_string)[1].decode()
                with open(file_content_path + "/" + file_name, "wb") as physical_file:
                    physical_file.write(file.read())

            # if zip, deflate
            if re.search(b"FILE/ZIP/", message_string):
                with zipfile.ZipFile(file_content_path + "/" + file_name, "r") as zip_ref:
                    zip_ref.extractall(file_content_path)
                os.remove(file_content_path + "/" + file_name)

        if message_string == b"HELLO":
            # TODO Register desktop app
            pass


class Server:
    """
    Server class that listens on specified port and address.
    """

    def __init__(self, ipv4: str, port: int, dir_path: str):
        """
        Initialize server. Raise FileNotFound if output directory does not exist.
        :param ipv4: Server ipv4 address
        :param port: Server ipv4 port
        :param dir_path: Output dir. Here will be stored all incoming files.
        """
        if not os.path.isdir(dir_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dir_path)
        self.dir_path = dir_path
        TCPMessageHandler.dir_path = self.dir_path
        self.port = port
        self.ipv4 = ipv4
        self.server_socket = socketserver.ThreadingTCPServer((ipv4, port), TCPMessageHandler)

    def start_server(self):
        """
        Starts server.
        :return: None
        """
        self.server_socket.serve_forever()

    def stop_server(self):
        """
        Stops server.
        :return: None
        """
        self.server_socket.server_close()


def main(args):
    s = Server(args.ip, args.port, args.dir)
    s.start_server()


if __name__ == '__main__':
    main(init_arg_parse().parse_args())
