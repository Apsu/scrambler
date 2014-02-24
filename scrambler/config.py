import json


class Config():
    def __init__(self, path="/usr/local/etc/scrambler/scrambler.json"):
        self.path = path
        self.read()

    def read(self):
        with open(self.path, "r") as fd:
            self.config = json.load(fd)

    def write(self):
        with open(self.path, "w") as fd:
            json.dump(self.config, fd)

    def __getitem__(self, key):
        return self.config[key].copy() if key in self.config else None

    def __setitem__(self, key, value):
        self.config[key] = value
