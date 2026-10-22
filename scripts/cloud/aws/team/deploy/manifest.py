"""Read-only helper for deploy/services.yaml, used by every shell script in
this folder so the manifest format only has to be understood in one place.

Deliberately has no AWS SDK dependency - this module only reads the YAML
file and prints plain text or JSON a shell script can consume. It never
calls AWS itself.
"""
import json
import sys
from pathlib import Path

import yaml

MANIFEST_PATH = Path(__file__).resolve().parent / "services.yaml"


def load():
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def ready_stacks(data):
    return [s for s in data["stacks"] if s.get("status") == "ready"]


def todo_stacks(data):
    return [s for s in data["stacks"] if s.get("status") != "ready"]


def find_stack(data, name):
    for stack in data["stacks"]:
        if stack["name"] == name:
            return stack
    raise KeyError(f"no stack named {name!r} in {MANIFEST_PATH}")


def main():
    if len(sys.argv) < 2:
        print("usage: manifest.py <ready-names|todo-names|stack-json> [stack-name]", file=sys.stderr)
        return 1

    command = sys.argv[1]
    data = load()

    if command == "ready-names":
        print("\n".join(s["name"] for s in ready_stacks(data)))
    elif command == "todo-names":
        print("\n".join(f"{s['name']}\t{s['owner']}" for s in todo_stacks(data)))
    elif command == "stack-json":
        if len(sys.argv) < 3:
            print("usage: manifest.py stack-json <stack-name>", file=sys.stderr)
            return 1
        print(json.dumps(find_stack(data, sys.argv[2])))
    elif command == "project-prefix-default":
        print(data["project_prefix_default"])
    elif command == "region-default":
        print(data["region_default"])
    else:
        print(f"unknown command {command!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
