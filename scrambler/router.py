import json
import time


class Router():
    def route(self, key, node, data):
        # Convert to object
        data = json.loads(data)

        # If cluster message
        if key == "cluster":
            # Update timestamp
            data["timestamp"] = time.time()

        # Update store
        self.put(key, data, node)

    def get(self, key, node=None):
        return getattr(self, key)[node] if node else getattr(self, key)

    def put(self, key, data, node=None):
        if node:
            getattr(self, key)[node].update(data)
        else:
            getattr(self, key).update(data)
