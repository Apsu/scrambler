from scrambler.synchronized import synchronized


class State():
    "Thread-safe cluster state store"

    def __init__(self, initialize={}):
        # Initialize state
        self._state = initialize

    @synchronized("write")  # Might write
    def __iter__(self):
        for item in self._state.items():
            yield item

    @synchronized("read")
    def __getitem__(self, key):
        return self._state[key]

    @synchronized("write")
    def __setitem__(self, key, value):
        self._state[key] = value

    @synchronized("write")
    def __delitem__(self, key):
        del self._state[key]

    @synchronized("write")
    def update(self, item):
        self._state.update(item)

    @synchronized("read")
    def __repr__(self):
        return repr(self._state)
