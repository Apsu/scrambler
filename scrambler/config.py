import json

from scrambler.synchronized import synchronized


class Config():
    """Provide JSON config file object."""

    def __init__(self, path="/usr/local/etc/scrambler/scrambler.json"):
        # Store path to config and try to read it
        self._path = path
        self.read()

    @synchronized("write")
    def read(self):
        """Parse that sucker."""

        with open(self._path, "r") as fd:
            self._config = json.load(fd)

    @synchronized("read")
    def write(self):
        """Write out our object."""

        with open(self._path, "w") as fd:
            json.dump(self._config, fd)

    @synchronized("read")
    def __getitem__(self, key):
        """Get a copy of the requested key's value or None if not found."""

        return self._config[key] if key in self._config else None

    @synchronized("write")
    def __setitem__(self, key, value):
        """Push the new value in."""

        self._config[key] = value
