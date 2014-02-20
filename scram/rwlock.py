import threading


class RWLock():
    "Read/Write lock helper with writer prioritization"

    def __init__(self):
        self.rlock = threading.Lock()   # Reader lock
        self.wlock = threading.Lock()   # Writer lock
        self.fence = threading.Event()  # Reader fence to prioritize writers

        # Trap readers when cleared; set initially
        self.fence.set()

    def read_acquire(self):
        # Wait until the fence is open
        while not self.fence.is_set():
            self.fence.wait(1)  # Short timeout so our thread can still exit

        # Acquire reader
        self.rlock.acquire()

    def read_release(self):
        # Release to next reader
        self.rlock.release()

    def write_acquire(self):
        # Acquire writer
        self.wlock.acquire()

        # Shut the fence to trap new readers
        self.fence.clear()

        # Wait for current reader and acquire
        self.rlock.acquire()

    def write_release(self):
        # Release to readers
        self.rlock.release()

        # Open the fence for readers so at least one can get through
        self.fence.set()

        # Release to writers
        self.wlock.release()
