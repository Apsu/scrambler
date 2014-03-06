import json
import threading
import Queue
import time
import traceback
import zmq

from scrambler.auth import Auth
from scrambler.store import Store


class PubSub():
    """Provide PUB/SUB interface."""

    def __init__(self, config):
        # Store config items
        self._hostname = config["hostname"]
        self._group = config["connection"]["group"]
        self._port = config["connection"]["port"]
        self._interface = config["connection"]["interface"]
        self._protocol = config["connection"]["protocol"]
        self._cluster_key = config["auth"]["cluster_key"]

        # Build connection string
        self._connection = "{}://{}{}:{}".format(
            self._protocol,
            self._interface + ";" if self._interface else "",
            self._group,
            self._port
        )

        # Auth object
        self._auth = Auth(self._cluster_key, self._hostname)
        self._digest = self._auth.digest()

        # Create ZMQ context
        self._context = zmq.Context()

        # Create publisher socket
        self._pub = self._context.socket(zmq.PUB)
        self._pub.setsockopt(zmq.LINGER, 0)

        # Create and subscribe socket to publishers
        self._sub = self._context.socket(zmq.SUB)

        # If using ZMQ 2.x, set high watermarks to same default as 3.x+
        if zmq.zmq_version_info()[0] == 2:
            self._pub.setsockopt(zmq.HWM, 1000)
            self._sub.setsockopt(zmq.HWM, 1000)

        # ...and in the darkness bind them
        self._pub.connect(self._connection)
        self._sub.connect(self._connection)

        # pub/sub queues
        self._subscribers = Store()
        self._publisher = Queue.Queue()

        # Create and start daemon worker threads
        for target in [self.pub_worker, self.sub_worker]:
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()

    def subscribe(self, key):
        """Subscribe to key, create/return attached subscriber queue."""

        self._sub.setsockopt(zmq.SUBSCRIBE, key)
        self._subscribers[key] = Queue.Queue()
        return self._subscribers[key]

    def publish(self, key, data):
        """Publish message through publisher queue."""

        self._publisher.put([key, self._hostname, data])

    def pub_worker(self):
        """Publish queued messages."""

        while True:
            try:
                # Wait for message from queue
                key, node, data = self._publisher.get(timeout=1)

                # Let the queue know we got it
                self._publisher.task_done()

                # And publish it out
                self._pub.send_multipart(
                    [
                        key,
                        node,
                        self._digest,
                        json.dumps(data)
                    ]
                )
            # Queue.get timed out, carry on
            except Queue.Empty:
                continue
            # Print anything else and continue
            except:
                print("Exception in pubsub.pub_worker():")
                print(traceback.format_exc())

    def sub_worker(self):
        """Queue subscribed messages we receive."""

        # Register poller for incoming messages
        poller = zmq.Poller()
        poller.register(self._sub, zmq.POLLIN)

        while True:
            try:
                # Wait for message
                sockets = dict(poller.poll(1000))  # In ms

                # Got a message?
                if self._sub in sockets:
                    # Receive it
                    key, node, digest, data = self._sub.recv_multipart()

                    # Convert to object
                    data = json.loads(data)

                    # If we have a subscriber
                    if key in self._subscribers:
                        # If authenticated, queue it
                        if self._auth.verify(digest, node):
                            self._subscribers[key].put([key, node, data])
                        # Otherwise complain
                        else:
                            print(
                                "[{}] Unauthenticated message: {}".format(
                                    time.ctime(),
                                    [key, node, json.dumps(data, indent=4)]
                                )
                            )
            # Print anything else and continue
            except:
                print("Exception in pubsub.sub_worker():")
                print(traceback.format_exc())
