import docker


class Docker():
    def __init__(self):
        self.client = docker.Client()

    def containers_by_image(self):
        results = {}
        containers = self.client.containers()
        for container in containers:
            image = container["Image"]
            if image in results:
                results[image]["Count"] += 1
            else:
                results[image] = {"Count": 1}

            if "Containers" in results[image]:
                results[image]["Containers"].append(container)
            else:
                results[image]["Containers"] = [container]

        return results
