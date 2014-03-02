import threading


class Threads():
    "Thread pool helper"

    def __init__(self, funcs, join=False):
        # Initialize thread pool
        self._threads = [
            threading.Thread(target=func)
            for func in funcs
        ]

        # Set threads to daemon and start them
        for thread in self._threads:
            thread.daemon = True
            thread.start()

        # If asked to join
        if join:
            # While any threads are alive, rotate joins through them
            while any(lambda t: t.is_alive(), self._threads):
                map(lambda t: t.join(1), self._threads)
