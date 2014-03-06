import platform
import socket
import time
import traceback

from scrambler.cluster import Cluster
from scrambler.config import Config
from scrambler.docker import Docker
from scrambler.pubsub import PubSub
from scrambler.threads import Threads
from scrambler.scheduler import Distribution


class Manager():
    """Policy-based Docker container manager."""

    def __init__(self, argv):
        # Catch anything that bubbles up
        try:
            # Config object
            self._config = Config()

            # Store interval
            self._schedule_interval = self._config["interval"]["schedule"]

            if "hostname" not in self._config:
                # Get hostname
                self._config["hostname"] = platform.node()

            if "hostname" not in self._config:
                # Get address
                self._config["address"] = socket.gethostbyname(
                    socket.getfqdn()
                )

            # ZMQ PUB/SUB helper
            self._pubsub = PubSub(self._config)

            # Initialize docker client
            self._docker = Docker(self._config, self._pubsub)

            # Initialize cluster
            self._cluster = Cluster(self._config, self._pubsub)

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
        """Schedule docker events based on policy."""

        #algorithm = self._config["scheduler"]
        scheduler = Distribution()

        while True:
            try:
                # If we're the only master
                if self._cluster.is_master():
                    scheduler.schedule(
                        self._config["policy"],
                        self._cluster.state,
                        self._docker.state
                    )
            # Print anything else and continue
            except:
                print("Exception in manager.schedule():")
                print(traceback.format_exc())
            finally:
                # Wait the interval
                time.sleep(self._schedule_interval)
