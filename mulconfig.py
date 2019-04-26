import json


class Config:
    def __init__(self, path_to_file: str):
        """Load JSON config file into inner dictionary.
        """
        json_file = open(path_to_file)
        json_content = json_file.read()
        self.__config = json.load(json_content)[0]

    def get_value(self, key: str):
        """Get value from config.

        Divide nested keys via dot notation (key1.key2.key3)
        """
        divided_key = key.split('.')
        tmp = self.__config
        for partial_key in divided_key:
            if partial_key not in tmp:
                return None
            tmp = tmp[partial_key]
        return tmp
