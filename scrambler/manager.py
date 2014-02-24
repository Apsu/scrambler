import platform
import socket
import threading
import time

from scrambler.cluster import Cluster
from scrambler.config import Config
from scrambler.docker import Docker
from scrambler.pubsub import PubSub


class Manager():
    "Policy-based Docker container manager"

    def __init__(self, argv):
        # Catch anything that bubbles up
        try:
            # Config object
            self.config = Config()

            # Docker client object
            self.docker = Docker()

            # Get hostname and address
            self.config["hostname"] = platform.node()
            self.config["address"] = socket.gethostbyname(socket.getfqdn())

            # ZMQ PUB/SUB helper
            self.pubsub = PubSub(self.config)

            # Initialize cluster
            self.cluster = Cluster(self.config, self.pubsub)

            # Start scheduler thread
            self.scheduler = threading.Thread(target=self.schedule)
            self.scheduler.daemon = True
            self.scheduler.start()

            # While the threads are alive, join with timeout
            while self.scheduler.is_alive():
                self.scheduler.join(1)
        # Handle ^C
        except KeyboardInterrupt:
            print("Exiting on SIGINT.")
        # Anything else
        except Exception as e:
            print("Exiting due to: {}.".format(e))

    def schedule(self):
        "Policy scheduler"

        #algorithm = self.config["scheduler"]

        while True:
            try:
                continue
            # Print anything else and continue
            except Exception as e:
                print("Exception in schedule(): {}".format(e))
            finally:
                # Wait the interval
                time.sleep(self.schedule_interval)
