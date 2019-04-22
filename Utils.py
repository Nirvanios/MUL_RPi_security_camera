import zipfile
import io


class ZipFile:
    """
    Class for creating zip files in memory.
    """

    def __init__(self):
        """
        Creates new zip file in memory.
        """
        self.__memory_zip = io.BytesIO()

    def append_file(self, file_name: str, file_content: bytes):
        """
        Appends file to existing zip file.

        :param file_name: Name of the file in archive.
        :param file_content: Contents of file as bytes.
        :return: None
        """
        zip_file = zipfile.ZipFile(self.__memory_zip, "a", zipfile.ZIP_DEFLATED, False)

        zip_file.writestr(file_name, file_content)

        for zfile in zip_file.filelist:
            zfile.create_system = 0

    def read_file(self):
        """
        Reads created file.
        :return: Bytes representing zip file.
        """
        self.__memory_zip.seek(0)
        return self.__memory_zip.read()

    def save_file(self, file_name, path):
        """
        Saves file to disk.
        :param file_name: Name of zip archive.
        :param path: Directory where to write zip archive.
        :return: None
        """
        with open(path + file_name, "wb") as file:
            file.write(self.read_file())


