import json


class Config():
    "JSON config file object"

    def __init__(self, path="/usr/local/etc/scrambler/scrambler.json"):
        # Store path to config and try to read it
        self.path = path
        self.read()

    def read(self):
        "Parse that sucker"

        with open(self.path, "r") as fd:
            self.config = json.load(fd)

    def write(self):
        "Write out our object"

        with open(self.path, "w") as fd:
            json.dump(self.config, fd)

    def __getitem__(self, key):
        "Get a copy of the requested key's value or None if not found"

        return self.config[key].copy() if key in self.config else None

    def __setitem__(self, key, value):
        "Push the new value in"

        self.config[key] = value
