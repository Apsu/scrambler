import itertools


class Scheduler():
    """Provide scheduler base class."""

    def schedule(self, policies, cluster_state, docker_state):
        """Provide base schedule function template.
        policies is an object describing desired cluster state
        cluster_state is the cluster state object
        docker_state is the docker state object
        """
        pass


class Distribution(Scheduler):
    """ Implements naive equal-distribution scheduler.
    Ignore min/max and run exactly 1 copy of container on every active node
    """
    def schedule(self, policies, cluster_state, docker_state):
        for policy in policies:
            pass


class RoundRobin(Scheduler):
    """Implements naive round-robin scheduler."""

    pass
#    def schedule(self, policies, cluster_state, docker_state):
#        # For each policy
#        for policy in policies:
#            # Get list of targets not
#            targets = [
#                node for node in state
#                if policy not in node["policies"]
#            ]
#
#            #mapping = zip(
