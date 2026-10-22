import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    os.chdir(PROJECT_ROOT)
    return subprocess.call([sys.executable, "-m", "pytest", *sys.argv[1:]])  # noqa: S603 - fixed pytest invocation, not untrusted input


if __name__ == "__main__":
    sys.exit(main())
