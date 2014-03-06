import threading


class RWLock():
    """Provide Read/Write lock helper with writer prioritization."""

    def __init__(self):
        self._rlock = threading.Lock()   # Reader lock
        self._wlock = threading.Lock()   # Writer lock
        self._fence = threading.Event()  # Reader fence to prioritize writers

        # Trap readers when cleared; set initially
        self._fence.set()

    def read_acquire(self):
        # Wait until the fence is open
        while not self._fence.is_set():
            self._fence.wait(1)  # Short timeout so our thread can still exit

        # Acquire reader
        self._rlock.acquire()

    def read_release(self):
        # Release to next reader
        self._rlock.release()

    def write_acquire(self):
        # Acquire writer
        self._wlock.acquire()

        # Shut the fence to trap new readers
        self._fence.clear()

        # Wait for current reader and acquire
        self._rlock.acquire()

    def write_release(self):
        # Release to readers
        self._rlock.release()

        # Open the fence for readers so at least one can get through
        self._fence.set()

        # Release to writers
        self._wlock.release()
