import docker
import platform
import socket
import threading
import time

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

        # Thread fence
        self.fence = threading.Event()

        # Thread pool
        self.threads = []

        # Initialize cluster threads
        self.cluster = Cluster(
            fence=self.fence,
            hostname=self.hostname,
            address=self.address,
            interface=self.interface
        )

        # Add threads cluster setup
        self.threads.extend(self.cluster.threads)

        # Add scheduling thread
        self.threads.append(threading.Thread(target=self.schedule))

        # Start threads
        for thread in self.threads:
            thread.start()

        # Catch anything that bubbles up
        try:
            # While the threads are alive, join with timeout
            while any(map(lambda x: x.is_alive(), self.threads)):
                map(lambda x: x.join(1), self.threads)
        # Handle ^C
        except KeyboardInterrupt:
            print("Exiting on SIGINT.")
        # Anything else
        except Exception as e:
            print("Exiting due to: {}.".format(e))
        # Always do the needful
        finally:
            self.exit()

    def exit(self):
        "Signal threads to exit and wait on them"

        print("Waiting on threads...")

        # Signal fence so threads exit
        self.fence.set()

        # Wait on them
        map(lambda x: x.join(), self.threads)

    def schedule(self):
        "Policy scheduler"

        while not self.fence.is_set():
            time.sleep(1)
