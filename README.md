SCRAM Clusters Resources Appropriately. Mostly.
=====

wat?
---

SCRAM is a Simple Cluster Resource Availability Manager, and helps orchestrate cluster nodes and their resources. As fun as the acronym is, I'll probably just be calling it Scram for convenience.

The executive summary design goal is to provide a simple agent with minimal dependencies that can:

* Lightweight, agent-based process
* Detect, authenticate and cluster with other agents on other machines
* Do this automatically, as soon as those machines are plugged into the same network
* Handle failures, partitioning, or controlled removal of machines from the cluster

Once clustered, the agents will manage their colocated resources based on policy shared between via the cluster mesh.

Docker
---
Primarily, resources are docker containers.

Discovery
---
Discovery is currently happening by way of LLDP to identify nodes as they enter the network. Each Scram agent monitors LLDP-discovered nodes and attempts to connect and authenticate with new nodes as they become available.

ZeroMQ
---
ZMQ is used to cluster Scram agents in a full-mesh so cluster resource state and policy can be replicated, as well as cluster state itself.
