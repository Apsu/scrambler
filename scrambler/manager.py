import platform
import socket
import threading
import time
import traceback

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

            # While the scheduler is alive, join with timeout for non-busy wait
            while self.scheduler.is_alive():
                self.scheduler.join(1)
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
                continue
            # Print anything else and continue
            except Exception:
                print("Exception in schedule():")
                print(traceback.format_exc())
            finally:
                # Wait the interval
                time.sleep(self.schedule_interval)
