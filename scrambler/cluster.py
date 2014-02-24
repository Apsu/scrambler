from __future__ import print_function

import json
import Queue
import threading
import time

from scrambler.store import Store


class Cluster():
    "Manage cluster discovery"

    def __init__(self, config, pubsub):
        # Initialize our super
        super(self, Cluster).__init__()

        # Initialize from config
        self.hostname = config["hostname"]
        self.address = config["address"]
        self.interface = config["interface"]
        self.announce_interval = config["announce_interval"]
        self.update_interval = config["update_interval"]
        self.zombie_interval = config["zombie_interval"]

        # Store pubsub object
        self.pubsub = pubsub

        # Cluster state
        self.state = Store(
            {
                self.hostname: {
                    "timestamp": time.time(),
                    "address": self.address,
                    "master": False
                }
            }
        )

        # Cluster message subscription queue
        self.queue = self.pubsub.subscribe("cluster")

        # Start daemon worker threads
        for target in [self.announce, self.listen, self.handle, self.update]:
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()

    def update(self):
        "Thread for periodically updating cluster state dict"

        while True:
            try:
                # Check for zombies and headshot them
                for node, state in self.state:
                    if (
                        node != self.hostname  # We're never a zombie, honest
                        and (
                            time.time()
                            - state["timestamp"]
                            > self.zombie_interval
                        )
                    ):
                        # STONITH!!
                        del self.state[node]

                # Show cluster status
                print(
                    "[{}] Cluster State: {}".format(
                        time.ctime(),
                        json.dumps(
                            # Coerce for serializing
                            dict(self.state),
                            indent=4
                        )
                    )
                )
            # Print anything else and continue
            except Exception as e:
                print("Exception in update(): {}".format(e))
            finally:
                # Wait interval before next check
                time.sleep(self.update_interval)

    def listen(self):
        "Thread for handling cluster state messages"

        while True:
            try:
                # Wait for cluster messages
                key, node, data = self.queue.get(timeout=1)

                # Timestamp message
                data.update({"timestamp": time.time()})

                # Update our master status based on least lexical hostname
                data.update(
                    {
                        "master":
                        min(self.state.keys()) == node
                    }
                )

                # Store node:data
                self.state.update({node: data})

            # Catch empty queue timeout
            except Queue.Empty:
                # TODO: Do something useful here?
                continue
            # Print anything else and continue
            except Exception as e:
                print("Exception in listen(): {}".format(e))
            finally:
                # Tell the queue we're done
                self.queue.task_done()

    def announce(self, fence):
        "Thread for announcing our state to the cluster"

        while True:
            try:
                # Publish announcement with our state
                self.pubsub.publish("cluster", self.state[self.hostname])
            # Print anything else and continue
            except Exception as e:
                print("Exception in announce(): {}".format(e))
            finally:
                # Wait the interval
                time.sleep(self.announce_interval)
