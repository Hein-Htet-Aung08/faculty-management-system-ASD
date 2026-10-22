#!/bin/bash
# Checks that every "ready" stack's ECS task is actually RUNNING, and
# records each stack's AI-service flag values (should all be "false" -
# AI_MODE_ENABLED, MCP_ENABLED, RAG_ENABLED, MULTI_AGENT_ENABLED) into
# reports/cloud/deployment-results.md. Flag values are read straight from
# the manifest, not queried from AWS, since they're a static part of the
# deployed configuration either way.
#
# TODO(owner: team lead): this does NOT yet do an HTTP-level check (e.g.
# curl a frontend, or the CRUD check the brief asks for - at least one list
# endpoint per student through the deployed app). Every stack is
# internal-only until unified-home's ALB exists (see deploy.sh's final
# TODO) - add real HTTP checks here once there's a public entry point to
# test through.
#
# Inputs: config.env, .env.team-deploy (from env-setup.sh).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/common.sh"

STATE_FILE="${SCRIPT_DIR}/.env.team-deploy"
if [ -f "$STATE_FILE" ]; then
  # shellcheck disable=SC1090
  source "$STATE_FILE"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
REPORT_DIR="${REPO_ROOT}/reports/cloud"
REPORT_FILE="${REPORT_DIR}/deployment-results.md"
CLUSTER_NAME="${PROJECT_PREFIX}-cluster"

echo "=== Team AWS deployment: deployment test ==="
confirm_account

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
mkdir -p "$REPORT_DIR"

{
  echo "# Cloud Deployment Results"
  echo ""
  echo "- Date: ${TIMESTAMP}"
  echo "- Cluster: ${CLUSTER_NAME}"
  echo "- Region: ${AWS_REGION}"
  echo "- Prefix: ${PROJECT_PREFIX}"
  echo ""
} > "$REPORT_FILE"

for stack_name in $(manifest_py ready-names); do
  echo ""
  echo "=== Checking stack: ${stack_name} ==="
  service_name="${PROJECT_PREFIX}-${stack_name}-service"

  echo "## Stack: ${stack_name}" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"

  if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY_RUN] Would check ECS service ${service_name} for RUNNING tasks."
    echo "- Status: not checked (DRY_RUN=true)" >> "$REPORT_FILE"
  else
    task_arn=$(aws ecs list-tasks --cluster "$CLUSTER_NAME" --service-name "$service_name" \
      --region "$AWS_REGION" --query "taskArns[0]" --output text 2>/dev/null || true)

    if [ -z "$task_arn" ] || [ "$task_arn" = "None" ]; then
      echo "FAIL: no running task found for ${service_name}."
      echo "- Status: FAIL (no running task found)" >> "$REPORT_FILE"
    else
      task_status=$(aws ecs describe-tasks --cluster "$CLUSTER_NAME" --tasks "$task_arn" \
        --region "$AWS_REGION" --query "tasks[0].lastStatus" --output text)
      echo "Task status: ${task_status}"
      echo "- Task status: ${task_status}" >> "$REPORT_FILE"
    fi
  fi

  echo "- AI-service flags (from deploy/services.yaml, as deployed):" >> "$REPORT_FILE"
  manifest_py stack-json "$stack_name" | "$PYTHON_BIN" -c '
import json, sys
stack = json.load(sys.stdin)
flags = ("AI_MODE_ENABLED", "MCP_ENABLED", "RAG_ENABLED", "MULTI_AGENT_ENABLED")
for c in stack["containers"]:
    env = c.get("env") or {}
    present = {k: env[k] for k in flags if k in env}
    if present:
        name = c["container_name"]
        flag_text = ", ".join(f"{k}={v}" for k, v in present.items())
        print(f"  - {name}: {flag_text}")
' >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
done

echo "" >> "$REPORT_FILE"
echo "## Stacks not yet deployed" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
while IFS=$'\t' read -r stack_name owner; do
  [ -z "$stack_name" ] && continue
  echo "- ${stack_name} (owner: ${owner}) - status: todo in deploy/services.yaml" >> "$REPORT_FILE"
done < <(manifest_py todo-names)

echo "" >> "$REPORT_FILE"
echo "## Release decision" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "TODO(owner: team lead / human sign-off): READY or NOT READY, justification," >> "$REPORT_FILE"
echo "approver name, date. Not written automatically - this is a human decision." >> "$REPORT_FILE"

echo ""
echo "=== Deployment test complete - results written to ${REPORT_FILE} ==="
