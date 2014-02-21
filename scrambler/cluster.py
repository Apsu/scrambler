from __future__ import print_function

import json
import Queue
import threading
import time

from scrambler.pubsub import PubSub
from scrambler.router import Router
from scrambler.store import Store


class Cluster():
    "Manage cluster discovery and messaging"

    def __init__(
        self,
        hostname="localhost",  # Our hostname
        address="127.0.0.1",   # Our unicast address
        interface="eth0",     # Physical interface to use
        announce_interval=1,  # How often to announce ourselves
        update_interval=5,    # How often to update our cluster state view
        zombie_interval=15    # How long after update to consider node dead
    ):
        # Store parameters
        self.hostname = hostname
        self.address = address
        self.interface = interface
        self.announce_interval = announce_interval
        self.update_interval = update_interval
        self.zombie_interval = zombie_interval

        # Thread-safe data stores
        self.stores = {
            "cluster": Store(
                {
                    self.hostname: {
                        "address": self.address
                    }
                }
            ),
            "policy": Store(
                {
                    self.hostname: {
                        "policies": []
                    }
                }
            )
        }

        # Message queue
        self.queue = Queue.Queue()

        # Message router
        self.router = Router()

        # Add hook for "cluster" message to timestamp them
        self.router.add_hook(
            "cluster",
            lambda key, node, data: data.update({"timestamp": time.time()})
        )

        # Add default hooks to store data received for each key
        for store in self.stores.keys():
            self.router.add_hook(
                store,
                lambda key, node, data: self.stores[key].update({node: data})
            )

        # ZMQ PUB/SUB helper
        self.pubsub = PubSub(
            keys=self.stores.keys(),
            hostname=self.hostname,
            interface=self.interface
        )

        # Thread fence
        self.fence = threading.Event()

        # Thread pool
        self.threads = []

        # Add threads to pool
        for target in [self.announce, self.listen, self.handle, self.update]:
            self.threads.append(threading.Thread(target=target))

        # Start threads
        for thread in self.threads:
            thread.start()

        # Catch ^C
        try:
            # While the threads are alive, join with timeout
            while any(map(lambda x: x.is_alive(), self.threads)):
                map(lambda x: x.join(1), self.threads)
        # Handle it
        except KeyboardInterrupt:
            print("Interrupted. Waiting on threads...")

            # Signal fence so threads exit
            self.fence.set()

            # Wait on them
            map(lambda x: x.join(), self.threads)

            print("Exiting.")

    def publish(self, key, data):
        "Publish key:data from us"

        self.pubsub.publish(key, self.hostname, data)

    def receive(self, interval):
        "Receive a key:node:data message with interval timeout"

        return self.pubsub.receive(interval)

    def update(self):
        "Thread for periodically updating cluster state dict"

        # Until signaled to exit
        while not self.fence.is_set():
            # Check for zombies and headshot them
            for node, state in self.stores["cluster"]:
                if (
                    node != self.hostname  # We're never a zombie, honest
                    and time.time() - state["timestamp"] > self.zombie_interval
                ):
                    print("[{}] Pruning zombie: {}".format(time.ctime(), node))
                    del self.stores["cluster"][node]

            # Show cluster status
            print(
                "[{}] Cluster State: {}".format(
                    time.ctime(),
                    json.dumps(
                        dict(self.stores["cluster"]),  # Coerce for serializing
                        indent=4
                    )
                )
            )

            # Show cluster policy
            print(
                "[{}] Cluster Policy: {}".format(
                    time.ctime(),
                    json.dumps(
                        dict(self.stores["policy"]),  # Coerce for serializing
                        indent=4
                    )
                )
            )

            # Wait interval before next check
            self.fence.wait(self.update_interval)

    def handle(self):
        "Thread for handling cluster state messages"

        # Until signaled to exit
        while not self.fence.is_set():
            try:
                # Wait for updates and route them by key
                self.router.route(*self.queue.get(timeout=1))

                # Tell the queue we're done
                self.queue.task_done()
            # Catch empty queue timeout
            except Queue.Empty:
                # TODO: Do something useful here?
                continue
            # Don't die for anything else
            else:
                continue

    def announce(self):
        "Thread for announcing our state to the cluster"

        # Until signaled to exit
        while not self.fence.is_set():
            # Publish announcement with our state
            self.publish(
                "cluster",
                self.stores["cluster"][self.hostname]
            )

            # Wait the interval
            time.sleep(self.announce_interval)

    def listen(self):
        "Thread for receiving messages from the cluster"

        # Get messages from subscriber generator
        for message in self.receive(self.announce_interval):
            # If we got one, queue it
            if message:
                self.queue.put(message)

            # If signaled to exit, bail
            if self.fence.is_set():
                break
