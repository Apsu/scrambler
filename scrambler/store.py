from scrambler.synchronized import synchronized


class Store():
    """Provide thread-safe storage object."""

    def __init__(self, initialize={}):
        # Initialize state
        self._store = initialize

    @synchronized("write")  # Might write
    def __iter__(self):
        for item in self._store.items():
            yield item

    @synchronized("read")
    def __getitem__(self, key):
        return self._store[key]

    @synchronized("read")
    def __contains__(self, key):
        return key in self._store

    @synchronized("read")
    def get(self, key, default=None):
        return self._store[key] if key in self._store else default

    @synchronized("read")
    def keys(self):
        return self._store.keys()

    @synchronized("read")
    def items(self):
        return self._store.items()

    @synchronized("write")
    def __setitem__(self, key, value):
        self._store[key] = value

    @synchronized("write")
    def __delitem__(self, key):
        del self._store[key]

    @synchronized("write")
    def update(self, item):
        self._store.update(item)

    @synchronized("read")
    def __repr__(self):
        return repr(self._store)
