import json
import threading
import Queue
import time
import zmq

from scrambler.auth import Auth
from scrambler.store import Store


class PubSub():
    "PUB/SUB interface"

    def __init__(self, config):
        # Store config items
        self.hostname = config["connection"]["hostname"]
        self.group = config["connection"]["group"]
        self.port = config["connection"]["port"]
        self.interface = config["connection"]["interface"]
        self.protocol = config["connection"]["protocol"]
        self.cluster_key = config["auth"]["cluster_key"]

        # Build connection string
        self.connection = "{}://{}{}:{}".format(
            self.protocol,
            self.interface + ";" if self.interface else "",
            self.group,
            self.port
        )

        # Auth object
        self.auth = Auth(self.cluster_key, self.hostname)
        self.digest = self.auth.digest()

        # Create ZMQ context
        self.context = zmq.Context()

        # Create publisher socket
        self.pub = self.context.socket(zmq.PUB)
        self.pub.setsockopt(zmq.LINGER, 0)

        # Create and subscribe socket to publishers
        self.sub = self.context.socket(zmq.SUB)

        # If using ZMQ 2.x, set high watermarks to same default as 3.x+
        if zmq.zmq_version_info()[0] == 2:
            self.pub.setsockopt(zmq.HWM, 1000)
            self.sub.setsockopt(zmq.HWM, 1000)

        # ...and in the darkness bind them
        self.pub.bind(self.connection)
        self.sub.connect(self.connection)

        # pub/sub queues
        self.subscribers = Store()
        self.publisher = Queue.Queue()

        # Create and start daemon worker threads
        for target in [self.pub_worker, self.sub_worker]:
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()

    def subscribe(self, key):
        "Subscribe to key, create/return attached subscriber queue"

        self.sub.setsockopt(zmq.SUBSCRIBE, key)
        self.subscribers[key] = Queue.Queue()
        return self.subscribers[key]

    def publish(self, key, node, data):
        "Publish message through publisher queue"

        self.publisher.put([key, node, data])

    def pub_worker(self):
        "Worker thread to publish queued messages"

        while True:
            try:
                # Wait for message from queue
                key, node, data = self.publisher.get(timeout=1)

                # And publish it out
                self.pub.send_multipart(
                    [
                        key,
                        node,
                        self.digest,
                        json.dumps(data)
                    ]
                )
            # Queue.get timed out, carry on
            except Queue.Empty:
                continue

    def sub_worker(self):
        "Worker thread to queue subscribed messages we receive"

        # Register poller for incoming messages
        poller = zmq.Poller()
        poller.register(self.sub, zmq.POLLIN)

        while True:
            # Wait for message
            sockets = dict(poller.poll(1000))  # In ms

            # Got a message?
            if self.sub in sockets:
                # Receive it
                key, node, digest, data = self.sub.recv_multipart()

                # If we have a subscriber
                if key in self.subscribers:
                    # If authenticated, queue it
                    if self.auth.verify(digest, node):
                        self.subscribers[key].put([key, node, data])
                    # Otherwise complain
                    else:
                        print(
                            "[{}] Unauthenticated message: {}".format(
                                time.ctime(),
                                [key, node, json.dumps(data, indent=4)]
                            )
                        )
