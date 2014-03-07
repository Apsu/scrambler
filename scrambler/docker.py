from __future__ import absolute_import  # When can 3.x be now?

import docker
import json
import Queue
import time
import traceback

from scrambler.store import Store
from scrambler.threads import Threads


class Docker():
    """Provide local docker management."""

    def __init__(self, config, pubsub):
        # Store args
        self._config = config
        self._pubsub = pubsub

        # Announce interval
        self._announce_interval = self._config["interval"]["announce"]

        # Store hostname
        self._hostname = self._config["hostname"]

        # Docker subscription
        self._docker_queue = self._pubsub.subscribe("docker")

        # Schedule subscription
        self._scheduled_queue = self._pubsub.subscribe("schedule")

        # Create client
        self._client = docker.Client()

        # Docker state object
        self._state = Store({self._hostname: self.containers_by_image()})

        # Start daemon worker threads
        Threads([self.scheduled, self.events, self.handler, self.announce])

    def get_state(self):
        """Just return state object."""

        return self._state

    def inspect_container(self, uuid):
        """Inspect and filter container by UUID."""

        # Get all container details
        container = self._client.inspect_container(uuid)

        # Return dictionary of just what we want
        return {
            "name": container["Name"],
            "state": container["State"]["Running"]
        }

    def containers_by_image(self):
        """Return containers indexed by image name, then uuid."""

        # Build container (image, id) list
        info = [
            (container["Image"], container["Id"])
            for container in self._client.containers()
        ]

        # Initialize container list to return
        containers = {}

        # For each (image, id) we found
        for image, uuid in info:
            # Initialize if first image
            if not image in containers:
                containers[image] = {uuid: {}}

            # Inspect and store container state we care about
            state = self.inspect_container(uuid)
            containers[image][uuid] = state

        # And return it
        return containers

    def scheduled(self):
        """Handle scheduled actions."""

        while True:
            try:
                # Get message from queue
                key, node, data = self._scheduled_queue.get(timeout=1)

                # Let the queue know we got it
                self._scheduled_queue.task_done()

                # TODO: Pass in self._cluster_state and check node["master"]?

                # Continue if no actions for us
                if self._hostname not in data:
                    continue

                # Get our actions
                actions = data[self._hostname]["actions"]

                # For each scheduled action
                for action in actions:
                    # If we're told to run a container
                    if action["do"] == "run":
                        # Pull out config item
                        config = action["config"]

                        # Create an appropriate container
                        container = self._client.create_container(
                            image=action["image"],
                            # TODO: Kill containers first to avoid collision?
                            #name=action["name"],
                            detach=True,
                            ports=config["ports"].values()
                        )

                        # And start it
                        self._client.start(
                            container,
                            port_bindings=config["ports"]
                        )
                    # Or if we're told to kill a container
                    elif action["do"] == "die":
                        # Nuke it
                        self._client.kill(action["uuid"])
                    # Any other actions
                    else:
                        print(
                            "[{}] Unimplemented scheduled action "
                            "from {}: {}".format(
                                time.ctime(),
                                node,
                                action
                            )
                        )
            # Continue on queue.get timeout
            except Queue.Empty:
                continue
            # Print anything else and continue
            except:
                print("Exception in docker.scheduled():")
                print(traceback.format_exc())

    def announce(self):
        """Periodically announce docker container state."""

        while True:
            try:
                # Publish our container state
                self._pubsub.publish("docker", self._state[self._hostname])
            # Print anything else and continue
            except:
                print("Exception in docker.announce():")
                print(traceback.format_exc())
            finally:
                # Wait the interval
                time.sleep(self._announce_interval)

    def events(self):
        """Push events from docker.events() to handler queue."""

        while True:
            try:
                # Get events from local docker daemon
                for event in self._client.events():
                    # And push to handler with "event" key
                    self._docker_queue.put(
                        [
                            "event",
                            self._hostname,
                            json.loads(event)
                        ]
                    )
            # Print anything else and continue
            except:
                print("Exception in docker.events():")
                print(traceback.format_exc())
                # Don't spam if we're continuously failing
                time.sleep(3)

    def handler(self):
        """Handle docker state messages and events."""

        while True:
            try:
                # Get message from queue
                key, node, data = self._docker_queue.get(timeout=1)

                # Let the queue know we got it
                self._docker_queue.task_done()

                # If message is state transfer from other nodes
                if key == "docker":
                    # Update state for node
                    self._state.update({node: data})

                # If message is event stream from our listener
                elif key == "event":
                    # Grab image and id from event
                    image = data["from"]
                    uuid = data["id"]

                    # If container has started
                    if data["status"] == "start":
                        # Inspect container and store it
                        state = self.inspect_container(uuid)
                        self._state[self._hostname][image][uuid] = state
                    # If container has died
                    elif data["status"] == "die":
                        # Delete it from storage
                        del self._state[self._hostname][image][uuid]
            # Continue on queue.get timeout
            except Queue.Empty:
                continue
            # Print anything else and continue
            except:
                print("Exception in docker.handler():")
                print(traceback.format_exc())
