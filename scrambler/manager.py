import docker
import platform
import socket

from scrambler.cluster import Cluster
from scrambler.scheduler import RoundRobin


class Manager():
    "Policy-based Docker container manager"

    def __init__(self, interface):
        # Docker client object
        self.client = docker.Client()

        # Scheduler algorithm
        self.scheduler = RoundRobin()

        # Store specified interface
        self.interface = interface

        # Get hostname and address
        self.hostname = platform.node()
        self.address = socket.gethostbyname(socket.getfqdn())

        # Start cluster
        self.cluster = Cluster(
            hostname=self.hostname,
            address=self.address,
            interface=self.interface
        )

    def reschedule(self):
        pass
