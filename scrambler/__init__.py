import sys

from scrambler.manager import Manager


# Entry point
def main(argv=sys.argv[1:]):
    # Start cluster manager
    Manager(interface=argv[0])

# If called directly
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # Hope for the best
