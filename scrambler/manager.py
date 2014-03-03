import platform
import socket
import time
import traceback

from scrambler.cluster import Cluster
from scrambler.config import Config
from scrambler.docker import Docker
from scrambler.pubsub import PubSub
from scrambler.threads import Threads


class Manager():
    "Policy-based Docker container manager"

    def __init__(self, argv):
        # Catch anything that bubbles up
        try:
            # Config object
            self.config = Config()

            # Store interval
            self.schedule_interval = self.config["interval"]["schedule"]

            # Docker client object
            self.docker = Docker()

            # Get hostname and address
            self.config["host"]["hostname"] = platform.node()
            self.config["host"]["address"] = socket.gethostbyname(
                socket.getfqdn()
            )

            # ZMQ PUB/SUB helper
            self.pubsub = PubSub(self.config)

            # Initialize cluster
            self.cluster = Cluster(self.config, self.pubsub)

            # Start scheduler daemon thread and wait on it
            Threads([self.schedule], join=True)

        # Handle ^C
        except KeyboardInterrupt:
            print("Exiting on SIGINT.")
        # Anything else
        except Exception:
            print("Exiting due to exception:")
            print(traceback.format_exc())

    def schedule(self):
        "Policy scheduler"

        #algorithm = self.config["scheduler"]

        while True:
            try:
                containers = self.docker.containers_by_image()
                self.pubsub.publish("docker", containers)
            # Print anything else and continue
            except Exception:
                print("Exception in schedule():")
                print(traceback.format_exc())
            finally:
                # Wait the interval
                time.sleep(self.schedule_interval)
