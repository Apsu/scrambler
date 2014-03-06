class Scheduler():
    """Provide scheduler base class."""

    def __init__(self, policies, cluster_state, docker_state):
        """Provide base scheduler constructor.
        policies is an object describing desired cluster state
        cluster_state is the cluster state object
        docker_state is the docker state object
        """
        self._policies = policies
        self._cluster_state = cluster_state
        self._docker_state = docker_state


class Distribution(Scheduler):
    """ Implements naive equal-distribution scheduler.
    Ignore min/max and run exactly 1 copy of container on every active node
    """

    def schedule(self):
        for policy in self._policies:
            pass


class RoundRobin(Scheduler):
    """Implements naive round-robin scheduler."""

    pass
