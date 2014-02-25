from __future__ import absolute_import  # When can 3.x be now?

import docker


class Docker():
    "Docker binding interface"

    def __init__(self):
        # Create client
        self.client = docker.Client()

    def containers_by_image(self):
        "Return containers indexed by image name, with count"

        # Dat declaration
        results = {}

        # Flat list of running container dicts
        containers = self.client.containers()

        # Walk the list
        for container in containers:
            # Snag container image
            image = container["Image"]

            # If we've seen this one already, +1 the count
            if image in results:
                results[image]["Count"] += 1
            # Otherwise add the first one
            else:
                results[image] = {
                    "Count": 1,
                    "Containers": []
                }

            # Add container to list
            results[image]["Containers"].append(container)

        # Pop 'em out
        return results
