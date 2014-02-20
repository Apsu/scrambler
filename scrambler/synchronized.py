from scrambler.rwlock import RWLock


def synchronized(access):
    "Thread-safe locking method decorator"

    def decorator(method):
        def synced(self, *args, **kwargs):
            if not hasattr(self, "_rwlock"):
                setattr(self, "_rwlock", RWLock())
            rwlock = getattr(self, "_rwlock")
            if access == "read":
                rwlock.read_acquire()
                result = method(self, *args, **kwargs)
                rwlock.read_release()
                return result
            elif access == "write":
                rwlock.write_acquire()
                result = method(self, *args, **kwargs)
                rwlock.write_release()
                return result
        return synced
    return decorator
