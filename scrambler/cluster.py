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
        fence=threading.Event(),  # Fence event object
        hostname="localhost",     # Our hostname
        address="127.0.0.1",      # Our unicast address
        interface="eth0",         # Physical interface to use
        announce_interval=1,      # How often to announce ourselves
        update_interval=5,        # How often to update our cluster state view
        zombie_interval=15        # How long after update to consider node dead
    ):
        # Store parameters
        self.fence = fence
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
            "policy": Store()
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

        # Add hook for "cluster" message to elect/depose master
        self.router.add_hook(
            "cluster",
            lambda key, node, data: data.update(
                {
                    "master":
                    min(self.stores[key].keys()) == node
                }
            )
        )

        # Add hook for "cluster" message to store data by node
        self.router.add_hook(
            "cluster",
            lambda key, node, data: self.stores[key].update({node: data})
        )

        self.router.add_hook(
            "policy",
            lambda key, node, data: self.stores[key].update(data)
        )

        # ZMQ PUB/SUB helper
        self.pubsub = PubSub(
            keys=self.stores.keys(),
            hostname=self.hostname,
            interface=self.interface
        )

        # Thread pool
        self.threads = []

        # Add threads to pool
        for target in [self.announce, self.listen, self.handle, self.update]:
            self.threads.append(threading.Thread(target=target))

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
            try:
                # Check for zombies and headshot them
                for node, state in self.stores["cluster"]:
                    if (
                        node != self.hostname  # We're never a zombie, honest
                        and (
                            time.time()
                            - state["timestamp"]
                            > self.zombie_interval
                        )
                    ):
                        del self.stores["cluster"][node]

                # Show cluster status
                print(
                    "[{}] Cluster State: {}".format(
                        time.ctime(),
                        json.dumps(
                            # Coerce for serializing
                            dict(self.stores["cluster"]),
                            indent=4
                        )
                    )
                )

                # Show cluster policy
                print(
                    "[{}] Cluster Policy: {}".format(
                        time.ctime(),
                        json.dumps(
                            # Coerce for serializing
                            dict(self.stores["policy"]),
                            indent=4
                        )
                    )
                )
            except KeyboardInterrupt:
                raise
            # Print anything else and continue
            except Exception as e:
                print("Exception in update(): {}".format(e))
            finally:
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
            except KeyboardInterrupt:
                raise
            # Print anything else and continue
            except Exception as e:
                print("Exception in handle(): {}".format(e))

    def announce(self):
        "Thread for announcing our state to the cluster"

        # Until signaled to exit
        while not self.fence.is_set():
            try:
                # Publish announcement with our state
                self.publish(
                    "cluster",
                    self.stores["cluster"][self.hostname]
                )
            except KeyboardInterrupt:
                raise
            # Print anything else and continue
            except Exception as e:
                print("Exception in announce(): {}".format(e))
            else:
                # Wait the interval
                time.sleep(self.announce_interval)

    def listen(self):
        "Thread for receiving messages from the cluster"

        # Get messages from subscriber generator
        for message in self.receive(self.announce_interval):
            try:
                # If we got one, queue it
                if message:
                    self.queue.put(message)
            except KeyboardInterrupt:
                raise
            # Print anything else and continue
            except Exception as e:
                print("Exception in listen(): {}".format(e))
            else:
                # If signaled to exit, bail
                if self.fence.is_set():
                    break
