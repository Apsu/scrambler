from scrambler.synchronized import synchronized


class Store():
    "Thread-safe data store"

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
