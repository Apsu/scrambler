import json
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
    """Provide policy-based Docker container manager."""

    def __init__(self, argv):
        # Catch anything that bubbles up
        try:
            # Config object
            self._config = Config()

            # Store intervals
            self._schedule_interval = self._config["interval"]["schedule"]
            self._update_interval = self._config["interval"]["update"]
            self._zombie_interval = self._config["interval"]["zombie"]

            if "hostname" not in self._config:
                # Get hostname
                self._config["hostname"] = platform.node()

            if "address" not in self._config:
                # Get address
                self._config["address"] = socket.gethostbyname(
                    socket.getfqdn()
                )

            # Store hostname
            self._hostname = self._config["hostname"]

            # ZMQ PUB/SUB helper
            self._pubsub = PubSub(self._config)

            # Initialize docker client and get state
            self._docker = Docker(self._config, self._pubsub)
            self._docker_state = self._docker.get_state()

            # Initialize cluster and get state
            self._cluster = Cluster(self._config, self._pubsub)
            self._cluster_state = self._cluster.get_state()

            # Start update thread
            Threads([self.update])

            # Start scheduler thread and wait on it
            Threads([self.schedule], join=True)

        # Handle ^C
        except KeyboardInterrupt:
            print("Exiting on SIGINT.")
        # Anything else
        except Exception:
            print("Exiting due to exception:")
            print(traceback.format_exc())

    def update(self):
        """Update states."""

        while True:
            try:
                # Check for zombies and headshot them
                for node, state in self._cluster_state:
                    if (
                        node != self._hostname  # We're never a zombie, honest
                        and (
                            time.time()
                            - state["timestamp"]
                            > self._zombie_interval
                        )
                    ):
                        # STONITH!!
                        del self._cluster_state[node]
                        del self._docker_state[node]

                # Show cluster state
                print(
                    "[{}] Cluster State: {}".format(
                        time.ctime(),
                        json.dumps(dict(self._cluster_state), indent=4)
                    )
                )

                # Show docker state
                print(
                    "[{}] Docker State: {}".format(
                        time.ctime(),
                        json.dumps(dict(self._docker_state), indent=4)
                    )
                )
            # Print anything else
            except:
                print("Exception in manager.update()")
                print(traceback.format_exc())
            # Always wait the interval
            finally:
                time.sleep(self._update_interval)

    def schedule(self):
        """Schedule docker events based on policy."""

        #algorithm = self._config["scheduler"]
        scheduler = Distribution(
            self._config["policies"],
            self._cluster_state,
            self._docker_state
        )

        while True:
            try:
                # If we're the only master
                if self._cluster.is_master():
                    # Schedule actions in accordance with policies
                    actions = scheduler.schedule()

                    # If actions required
                    if actions:
                        # Publish actions to everyone including ourself
                        self._pubsub.publish(
                            "schedule",
                            actions,
                            loopback=True
                        )
            # Print anything else and continue
            except:
                print("Exception in manager.schedule():")
                print(traceback.format_exc())
            # Always wait the interval
            finally:
                time.sleep(self._schedule_interval)
