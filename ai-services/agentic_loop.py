import os
import sys


def _bootstrap():
    package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agentic_loop")
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)


def main():
    _bootstrap()
    from main import main as package_main

    package_main()


if __name__ == "__main__":
    main()
