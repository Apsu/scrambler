#!/usr/bin/env python

from scram.cluster import Cluster

# Entry point
if __name__ == "__main__":
    # Join and track cluster
    Cluster(interface="eth2")
