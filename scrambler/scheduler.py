class Scheduler():
    """Provide scheduler base class."""

    def __init__(self, policies, cluster_state, docker_state):
        """Provide base scheduler constructor.
        policies is an object describing desired cluster state
        cluster_state is the cluster state object
        docker_state is the docker state object
        """

        # Store parameters
        self._policies = policies
        self._cluster_state = cluster_state
        self._docker_state = docker_state

        # Action dict for building schedules
        self._actions = {}

    def _prep(self, node):
        """Prepare self._actions common code."""

        # Initialize if needed
        if node not in self._actions:
            self._actions[node] = {}

        # Initialize if needed
        if "actions" not in self._actions[node]:
            self._actions[node]["actions"] = []

    def _run(self, node, image, policy):
        """Add run actions for containers."""

        # Prep
        self._prep(node)

        # Add run action
        self._actions[node]["actions"].append(
            {
                "do": "run",
                "image": image,
                "name": policy["name"],
                "config": {
                    "ports": policy["ports"]
                }
            }
        )

    def _die(self, node, image, containers):
        """Add die actions for containers."""

        # Prep
        self._prep(node)

        # For each container UUID
        for uuid, _ in containers:
            self._actions[node]["actions"].append(
                {
                    "do": "die",
                    "uuid": uuid
                }
            )

    def schedule(self):
        """Schedule actions based on policies and docker states.

        Base-class "virtual" function to be overridden by specific scheduler

        Returns:
        "somenode": {
            "actions": [
                {
                    "do": "run",
                    "config": {
                        "image": "someimage",
                        "name": "somename",
                        "ports": {
                            "2222": "22"
                        }
                    }
                },
                {
                    "do": "die",
                    "uuid": "someuuid"
                }
            ]
        }
        """

        pass


class Distribution(Scheduler):
    """ Implements naive equal-distribution scheduler.
    Ignore min/max and run exactly 1 copy of container on every active node.
    """

    def schedule(self):
        """Schedule actions based on policies and docker states."""

        # Clear actions before scheduling
        self._actions = {}

        # For each image policy
        for image, policy in self._policies.items():
            # For each node state
            for node, state in self._docker_state.items():
                # If node has containers
                if image in state:
                    # Get list of running containers
                    containers = [
                        (uuid, container)
                        for uuid, container in state[image].items()
                        if container["state"]
                    ]

                    # If more than one container is running on this node
                    if len(containers) > 1:
                        # Add die actions for all but first one
                        self._die(node, image, containers[1:])
                # Or if no containers are running on this node
                else:
                    # Add run action
                    self._run(node, image, policy)


class RoundRobin(Scheduler):
    """Implements naive round-robin scheduler."""

    pass
