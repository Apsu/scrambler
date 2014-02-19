#!/usr/bin/env python

from __future__ import print_function

import json
import platform
import Queue
import socket
import threading
import time
import zmq


class Cluster():
    "Participate in cluster discovery and state"

    def __init__(
        self,
        address="224.0.0.127",
        port=4999,
        interface=None,
        protocol="epgm",
        interval=1
    ):
        # Store parameters
        self.address = address
        self.port = port
        self.interface = interface
        self.protocol = protocol
        self.interval = interval

        # Build connection string
        self.connection = "{}://{}{}:{}".format(
            protocol,
            interface + ";" if interface else "",
            address,
            port
        )

        # Store hostname
        self.hostname = platform.node()

        # Preload our info
        self.cluster_state = {
            self.hostname: {
                "address": socket.gethostbyname(socket.getfqdn())
            }
        }

        # Cluster state queue
        self.cluster_queue = Queue.Queue()

        # Thread fence
        self.fence = threading.Event()

        # Thread pair
        self.threads = []

        # Add threads to pool
        for target in [self.publish, self.subscribe, self.update]:
            self.threads.append(threading.Thread(target=target))

        # Daemonize and start threads
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
            for thread in self.threads:
                thread.join()

            print("Exiting.")

    def update(self):
        "Thread for updating cluster state information"

        # Until signaled to exit
        while not self.fence.isSet():
            try:
                # Wait for updates received from other nodes
                key, value = self.cluster_queue.get(timeout=1)

                # Convert to object
                value = json.loads(value)

                # Add or update our state dict entry
                if key in self.cluster_state:
                    self.cluster_state[key].update(value)
                else:
                    self.cluster_state[key] = value

                # Tell the queue we're done
                self.cluster_queue.task_done()

                # Show eet
                print(
                    "Cluster State: {}".format(
                        json.dumps(
                            self.cluster_state,
                            indent=True
                        )
                    )
                )
            # Catch empty queue timeout
            except Queue.Empty:
                # TODO: Do something useful here?
                continue
            # Don't die for anything else
            else:
                continue

    def publish(self):
        "Thread for pushing our state to the cluster"

        # Create and bind publisher socket
        context = zmq.Context()
        pub = context.socket(zmq.PUB)
        pub.setsockopt(zmq.LINGER, 0)
        pub.setsockopt(zmq.HWM, 1000)  # ZMQ 2.x high watermark
        pub.bind(self.connection)

        # Until signaled to exit
        while not self.fence.is_set():
            # Update our timestamp
            self.cluster_state[self.hostname]["timestamp"] = time.time()

            # Publish announcement with our state
            pub.send_multipart(
                [
                    "cluster",
                    self.hostname,
                    json.dumps(self.cluster_state[self.hostname])
                ]
            )

            # Wait the interval
            time.sleep(self.interval)

    def subscribe(self):
        "Thread for receiving state from the cluster"

        # Create and subscribe socket to discovery publishers
        context = zmq.Context()
        sub = context.socket(zmq.SUB)
        sub.setsockopt(zmq.SUBSCRIBE, "cluster")
        sub.setsockopt(zmq.HWM, 1000)  # ZMQ 2.x high watermark
        sub.connect(self.connection)

        # Message ready poller
        poller = zmq.Poller()
        poller.register(sub, zmq.POLLIN)

        # Until signaled to exit
        while not self.fence.is_set():
            # Wait for message
            sockets = dict(poller.poll(self.interval * 1000))  # ms

            # If we got one
            if sub in sockets:
                # Get message pieces
                key, host, msg = sub.recv_multipart()

                # If not our own reflection
                if host != self.hostname:
                    # Show it
                    print("{} => {}".format(host, msg))

                    # Handoff to update thread
                    self.cluster_queue.put([host, msg])
            # Timed out, carry on
            else:
                continue


# Entry point
if __name__ == "__main__":
    # Join and track cluster
    Cluster(interface="eth2")
