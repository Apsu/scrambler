from __future__ import print_function

import json
import platform
import Queue
import socket
import threading
import time
import zmq

from scram.state import State


class Cluster():
    "Participate in cluster discovery and state"

    def __init__(
        self,
        bind="224.0.0.127",   # Multicast address; default is link-local
        port=4999,            # Multicast port
        interface=None,       # Physical interface to use
        protocol="epgm",      # Unprivileged reliable multicast protocol
        announce_interval=1,  # How often to announce ourselves
        update_interval=5,    # How often to update our cluster state view
        zombie_interval=15    # How long after update to consider node dead
    ):
        # Store parameters
        self.bind = bind
        self.port = port
        self.interface = interface
        self.protocol = protocol
        self.announce_interval = announce_interval
        self.update_interval = update_interval
        self.zombie_interval = zombie_interval

        # Build connection string
        self.connection = "{}://{}{}:{}".format(
            protocol,
            interface + ";" if interface else "",
            bind,
            port
        )

        # Store hostname and address
        self.hostname = platform.node()
        self.address = socket.gethostbyname(socket.getfqdn())

        # Thread-safe state object; initialize ourself
        self.cluster_state = State(
            {
                self.hostname: {
                    "address": self.address
                }
            }
        )

        # Cluster state queue
        self.cluster_queue = Queue.Queue()

        # Thread fence
        self.fence = threading.Event()

        # Thread pair
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

    def update(self):
        "Thread for periodically updating cluster state dict"

        # Until signaled to exit
        while not self.fence.is_set():
            # Check for zombies and headshot them
            for node, state in self.cluster_state:
                if time.time() - state["timestamp"] > self.zombie_interval:
                    print("[{}] Pruning zombie: {}".format(time.ctime(), node))
                    del self.cluster_state[node]

            # Show cluster status
            print(
                "[{}] Cluster State: {}".format(
                    time.ctime(),
                    json.dumps(
                        dict(self.cluster_state),  # Coerce for serializing
                        indent=True
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
                # Wait for updates received from other nodes
                key, value = self.cluster_queue.get(timeout=1)

                # Convert to object
                value = json.loads(value)

                # Add to cluster state dict
                self.cluster_state[key] = value

                # Tell the queue we're done
                self.cluster_queue.task_done()
            # Catch empty queue timeout
            except Queue.Empty:
                # TODO: Do something useful here?
                continue
            # Don't die for anything else
            else:
                continue

    def announce(self):
        "Thread for announcing our state to the cluster"

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
            time.sleep(self.announce_interval)

    def listen(self):
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
            sockets = dict(poller.poll(self.announce_interval * 1000))  # In ms

            # If we got one
            if sub in sockets:
                # Get message pieces
                key, host, msg = sub.recv_multipart()

                # If not our own reflection
                if host != self.hostname:
                    # Handoff to update thread
                    self.cluster_queue.put([host, msg])
            # Timed out, carry on
            else:
                continue