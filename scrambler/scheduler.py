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
            "name": {             # Name of image for container
                "count": 3,       # Number of containers
                "affinity": True  # Requires node-affinity or not
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
