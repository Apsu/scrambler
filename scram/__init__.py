from scram.cluster import Cluster


# Entry point
def main(interface):
    # Start cluster agent
    Cluster(interface=interface)
