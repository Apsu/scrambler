from __future__ import absolute_import  # When can 3.x be now?

import docker
import json
import Queue
import time
import traceback

from scrambler.store import Store
from scrambler.threads import Threads


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

        # Start event generator and queue handler threads
        Threads([self.events, self.handler])

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
                    self.queue.put(
                        "event",
                        self.config["host"]["hostname"],
                        json.dumps(event)
                    )
            except:
                print("Exception in docker.events():")
                print(traceback.format_exc())

    def handler(self):
        "Handle docker state messages and events"

        while True:
            try:
                key, node, data = self.queue.get(timeout=1)

                print(
                    "[{}] Docker message: {}".format(
                        time.ctime(),
                        (key, node, data)
                    )
                )

                # If message is state transfer from other nodes
                if key == "docker":
                    pass
                # If message is event stream from our listener
                elif key == "event":
                    pass
            except Queue.Empty:
                continue
            # Print anything else and continue
            except:
                print("Exception in docker.handler():")
                print(traceback.format_exc())
            else:
                self.queue.task_done()
