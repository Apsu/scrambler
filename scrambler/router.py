import json


class Router():
    "Router helper to plumb message keys to data stores"

    def __init__(self):
        # Hook dict
        self.hooks = {}

    def add_hook(self, key, f):
        "Add hook function to list of hooks, by key"

        if key not in self.hooks:
            self.hooks[key] = [f]
        elif f not in self.hooks[key]:
            self.hooks[key].append(f)

    def del_hook(self, key, f):
        "Delete hook from list of hooks, by key"

        if key in self.hooks:
            self.hooks[key].remove(f)

    def route(self, key, node, data):
        "Route data through appropriate hooks"

        # Convert to object
        data = json.loads(data)

        # Run hooks by key
        for hook in self.hooks[key]:
            hook(key, node, data)
