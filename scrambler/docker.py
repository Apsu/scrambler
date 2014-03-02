from __future__ import absolute_import  # When can 3.x be now?

import docker
import Queue
import threading
import traceback

from scrambler.store import Store


class Docker():
    "Docker binding interface"

    def __init__(self, config, pubsub):
        # Store args
        self.config = config
        self.pubsub = pubsub

        # Subscription queue
        self.queue = self.pubsub.subscribe("docker")

        # Create client
        self.client = docker.Client()

        # Docker state object
        self.state = Store()

        # Create and start message daemon thread
        for target in [self.events, self.handler]:
            target = threading.Thread(target=self.handler)
            target.daemon = True
            target.start()

    def containers_by_image(self):
        "Return containers indexed by image name, with count"

        # Dat declaration
        results = {}

        # Flat list of running container dicts
        containers = self.client.containers()

        # Walk the list
        for container in containers:
            # Snag container image
            image = container["Image"]

            # If we've seen this one already, +1 the count
            if image in results:
                results[image]["Count"] += 1
            # Otherwise add the first one
            else:
                results[image] = {
                    "Count": 1,
                    "Containers": []
                }

            # Add container to list
            results[image]["Containers"].append(container)

        # Pop 'em out
        return results

    def events(self):
        "Push events from docker.events() to handler queue"

        while True:
            try:
                for event in self.client.events():
                    self.queue.put("event", self.config["hostname"], event)
            except:
                continue

    def handler(self):
        "Handle docker state messages and events"

        while True:
            try:
                key, node, data = self.queue.get(timeout=1)

                # If message is state transfer from other nodes
                if key == "docker":
                    pass
                # If message is event stream from our listener
                elif key == "event":
                    pass
            except Queue.Empty:
                continue
            # Print anything else and continue
            except Exception:
                print("Exception in schedule():")
                print(traceback.format_exc())
            else:
                self.queue.task_done()
