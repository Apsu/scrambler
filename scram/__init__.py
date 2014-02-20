import sys

from scram.cluster import Cluster


# Entry point
def main(argv=sys.argv[1:]):
    # Start cluster agent
    Cluster(interface=argv[0])

# If called directly
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # Hope for the best
