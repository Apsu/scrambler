import itertools


class Scheduler():
    "Scheduler base class"

    def schedule(self, policies, state):
        pass


class RoundRobin(Scheduler):
    "Naive round-robin scheduler"

    def schedule(self, policies, state):
        """
        policies is a dict of dicts as follows:
            # Name of image for container
            "name": {
                # Number of containers
                "count": 3,
                # Allow node affinity or require node anti-affinity
                "affinity": True
                # Run 0 containers if count/affinity isn't met, or not
                "strict": False
            }

        state is the cluster state object
        """
        # For each policy
        for policy in policies:
            # Get list of targets not
            targets = [
                node for node in state
                if policy not in node["policies"]
            ]

            #mapping = zip(
