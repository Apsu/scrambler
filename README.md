Scrambler is a decentralized Docker cluster manager, and helps orchestrate cluster nodes and their resources.

The executive summary design goal is to provide a simple agent with minimal dependencies that can:

* Lightweight, agent-based process
* Detect, authenticate and cluster with other agents on other machines
* Do this automatically, as soon as those machines are plugged into the same network
* Handle failures, partitioning, or controlled removal of machines from the cluster

Once clustered, the agents will manage their colocated resources based on policy shared between them via the cluster mesh.

Docker
---
Primarily, resources are docker containers.

ZeroMQ
---
ZMQ is used to cluster Scrambler agents in a full-mesh so resource state and policy can be replicated, as well as cluster state itself.

Discovery
---
Discovery and heartbeating is accomplished by virtue of state update messages sent over the
multicast pub-sub ZMQ mesh mentioned above. Currently, ZMQ's EPGM protocol is being used for
robust, reliable dynamic discovery and state transfer.

How do?
---

To try it out, fire up `./setup.py install`, and you'll get a binary named `scramble` in `/usr/local/bin`.

> Note: The installer will use pip to build the resources it needs, so on Ubuntu you'll need these
> packages before installing Scrambler:
>     - python-pip
>     - python-dev
>     - build-essential
>     - libzmq-dev

Run `scramble $interface` for the interface you want to talk to other scramblers on.
