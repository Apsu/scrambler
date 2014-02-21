import json
import zmq


class PubSub():
    "PUB/SUB interface class"

    def __init__(
        self,
        keys=["message"],      # List of keys to subscribe to
        hostname="localhost",  # Our hostname
        group="224.0.0.127",   # Multicast address; default is link-local
        port=4999,             # Multicast port
        interface=None,        # Physical interface to use
        protocol="epgm"        # Unprivileged reliable multicast protocol
    ):
        # Store parameters
        self.keys = keys
        self.hostname = hostname
        self.group = group
        self.port = port
        self.interface = interface
        self.protocol = protocol

        # Build connection string
        self.connection = "{}://{}{}:{}".format(
            protocol,
            interface + ";" if interface else "",
            group,
            port
        )

        # Create ZMQ context
        self.context = zmq.Context()

        # Create publisher socket
        self.pub = self.context.socket(zmq.PUB)
        self.pub.setsockopt(zmq.LINGER, 0)

        # Create and subscribe socket to publishers
        self.sub = self.context.socket(zmq.SUB)
        for key in self.keys:
            self.sub.setsockopt(zmq.SUBSCRIBE, key)

        # If using ZMQ 2.x, set high watermark
        if zmq.zmq_version_info()[0] == 2:
            self.pub.setsockopt(zmq.HWM, 1000)
            self.sub.setsockopt(zmq.HWM, 1000)

        # ...and in the darkness bind them
        self.pub.bind(self.connection)
        self.sub.connect(self.connection)

    def publish(self, key, node, data):
        # Send message with subscription key
        self.pub.send_multipart([key, node, json.dumps(data)])

    def receive(self, interval):
        # Register poller for incoming messages
        poller = zmq.Poller()
        poller.register(self.sub, zmq.POLLIN)

        while True:
            # Wait for message
            sockets = dict(poller.poll(interval * 1000))  # In ms

            # If we got one
            if self.sub in sockets:
                # Get message pieces
                key, host, data = self.sub.recv_multipart()

                # If not our own reflection, yield message
                if host != self.hostname:
                    yield key, host, data
            # Timed out, yield None
            else:
                yield None
