from __future__ import print_function

import Queue
import time
import traceback

from scrambler.store import Store
from scrambler.threads import Threads


class Cluster():
    """Manage cluster discovery."""

    def __init__(self, config, pubsub):
        # Initialize from config
        self._hostname = config["hostname"]
        self._address = config["address"]
        self._announce_interval = config["interval"]["announce"]

        # Store pubsub object
        self._pubsub = pubsub

        # Cluster state
        self._state = Store(
            {
                self._hostname: {
                    "timestamp": time.time(),
                    "address": self._address,
                    "master": False
                }
            }
        )

        # Cluster message subscription queue
        self._queue = self._pubsub.subscribe("cluster")

        # Start daemon worker threads
        Threads([self.announce, self.listen])

    def get_state(self):
        return self._state

    def is_master(self):
        """Return true if there's only one master and we're it."""

        masters = [
            key
            for key in self._state.keys()
            if self._state[key]["master"]
        ]

        return len(masters) == 1 and masters[0] == self._hostname

    def listen(self):
        """Handle cluster state messages."""

        while True:
            try:
                # Wait for cluster messages
                key, node, data = self._queue.get(timeout=1)

                # Tell the queue we're done
                self._queue.task_done()

                # Timestamp message
                data.update({"timestamp": time.time()})

                # Update our master status based on least lexical hostname
                data.update(
                    {
                        "master":
                        min(self._state.keys()) == node
                    }
                )

                # Store node:data
                self._state.update({node: data})

            # Catch empty queue timeout
            except Queue.Empty:
                # TODO: Do something useful here?
                continue
            # Print anything else and continue
            except:
                print("Exception in cluster.listen():")
                print(traceback.format_exc())

    def announce(self):
        """Announce our state to the cluster."""

        while True:
            try:
                # Publish announcement with our state
                self._pubsub.publish("cluster", self._state[self._hostname])
            # Print anything else and continue
            except:
                print("Exception in cluster.announce():")
                print(traceback.format_exc())
            finally:
                # Wait the interval
                time.sleep(self._announce_interval)
