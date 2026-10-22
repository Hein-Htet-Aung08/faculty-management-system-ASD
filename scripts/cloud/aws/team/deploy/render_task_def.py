"""Renders an ECS task definition + Service Connect config for one manifest
stack. Pure rendering - makes no AWS calls itself, so this is safe to run
and inspect without any credentials at all.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import find_stack, load  # noqa: E402


def port_name(container_name, port):
    return f"{container_name}-{port}"


def render_task_def(stack, registry, project_prefix, execution_role_arn, log_group, region):
    container_defs = []
    for c in stack["containers"]:
        env = [{"name": k, "value": v} for k, v in (c.get("env") or {}).items()]
        repo_name = f"{project_prefix}-{c['container_name']}"
        container_def = {
            "name": c["container_name"],
            "image": f"{registry}/{repo_name}:latest",
            "essential": True,
            "portMappings": [{
                "containerPort": c["container_port"],
                "name": port_name(c["container_name"], c["container_port"]),
            }],
            "environment": env,
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": log_group,
                    "awslogs-region": region,
                    "awslogs-stream-prefix": c["container_name"],
                },
            },
        }
        if c.get("depends_on"):
            container_def["dependsOn"] = [
                {"containerName": dep, "condition": "START"} for dep in c["depends_on"]
            ]
        container_defs.append(container_def)

    return {
        "family": f"{project_prefix}-{stack['name']}-task",
        "requiresCompatibilities": ["FARGATE"],
        "networkMode": "awsvpc",
        "cpu": "1024",
        "memory": "3072",
        "executionRoleArn": execution_role_arn,
        "containerDefinitions": container_defs,
    }


def render_service_connect_config(stack, namespace):
    services = []
    for c in stack["containers"]:
        services.append({
            "portName": port_name(c["container_name"], c["container_port"]),
            "discoveryName": c["service_connect_name"],
            "clientAliases": [{"port": c["container_port"]}],
        })
    return {
        "enabled": True,
        "namespace": namespace,
        "services": services,
    }


def main():
    if len(sys.argv) < 3:
        print(
            "usage: render_task_def.py task-def <stack> <registry> <prefix> <role-arn> <log-group> <region>\n"
            "       render_task_def.py service-connect-config <stack> <namespace>",
            file=sys.stderr,
        )
        return 1

    command = sys.argv[1]
    stack_name = sys.argv[2]
    data = load()
    stack = find_stack(data, stack_name)

    if command == "task-def":
        _, _, _, registry, prefix, role_arn, log_group, region = sys.argv
        print(json.dumps(render_task_def(stack, registry, prefix, role_arn, log_group, region), indent=2))
    elif command == "service-connect-config":
        _, _, stack_name, namespace = sys.argv
        print(json.dumps(render_service_connect_config(stack, namespace), indent=2))
    else:
        print(f"unknown command {command!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
