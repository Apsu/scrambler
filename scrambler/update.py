from scrambler.threads import Threads


class Update():
    """Provide update thread with callback handlers."""

    def __init__(self, states, update_interval):
        # Store parameters
        self._states = states
        self._update_interval = update_interval

        # Callbacks
        self._callbacks = []

        # Start update thread
        Threads([self.update])

    def add_callback(self, cb, *args, **kwargs):
        """Add callback and args to callback list."""

        self._callbacks.append((cb, args, kwargs))

    def update(self):
        """Run callbacks on states."""

        # For each callback with args
        for cb, args, kwargs in self._callbacks:
            # For each state
            for state in self._states:
                # Run callback on state with args
                cb(state, *args, **kwargs)
