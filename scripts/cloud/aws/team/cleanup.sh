#!/bin/bash
# Deletes everything env-setup.sh / build-and-push-images.sh / deploy.sh
# created, to stop billing. Loops over every stack in the manifest
# (ready or todo - a stack could have been deployed once, then marked
# todo again after a regression, so cleanup always tries every name).
#
# Does NOT delete the ECS service-linked role (AWSServiceRoleForECS) -
# that's an account-wide, one-time AWS resource other projects in the same
# account may also depend on; deleting it is a much bigger decision than
# this script should make.
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

CLUSTER_NAME="${PROJECT_PREFIX}-cluster"
SG_NAME="${PROJECT_PREFIX}-internal-sg"
EXECUTION_ROLE_NAME="${PROJECT_PREFIX}-ecs-execution-role"
LOG_GROUP="/ecs/${PROJECT_PREFIX}"

echo "=== Team AWS deployment: cleanup ==="
confirm_account

echo "This will delete, for every stack in deploy/services.yaml:"
echo "  - Its ECS service and all task definition revisions"
echo "  - Its containers' ECR repositories"
echo "Plus the shared resources: cluster ${CLUSTER_NAME}, security group"
echo "${SG_NAME}, execution role ${EXECUTION_ROLE_NAME}, log group ${LOG_GROUP}."
echo "(The account-wide ECS service-linked role is left alone - see this"
echo "script's header comment.)"

if [ "$DRY_RUN" != "true" ] && [ -z "${CI:-}" ] && [ -z "${SKIP_CONFIRM:-}" ]; then
  read -r -p "Type 'delete' to confirm: " CONFIRM
  if [ "$CONFIRM" != "delete" ]; then
    echo "Confirmation did not match. Aborting." >&2
    exit 1
  fi
fi

all_stack_names() {
  manifest_py ready-names
  manifest_py todo-names | cut -f1
}

for stack_name in $(all_stack_names); do
  echo ""
  echo "--- Cleaning up stack: ${stack_name} ---"
  service_name="${PROJECT_PREFIX}-${stack_name}-service"
  task_family="${PROJECT_PREFIX}-${stack_name}-task"

  run_or_dry "scale ${service_name} to 0 and delete it" -- \
    aws ecs update-service --cluster "$CLUSTER_NAME" --service "$service_name" --desired-count 0 --region "$AWS_REGION" || true
  run_or_dry "delete service ${service_name}" -- \
    aws ecs delete-service --cluster "$CLUSTER_NAME" --service "$service_name" --force --region "$AWS_REGION" || true

  if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY_RUN] Would deregister every revision of task definition ${task_family}."
  else
    for revision in $(aws ecs list-task-definitions --family-prefix "$task_family" --region "$AWS_REGION" --query "taskDefinitionArns[]" --output text 2>/dev/null || true); do
      aws ecs deregister-task-definition --task-definition "$revision" --region "$AWS_REGION" >/dev/null 2>&1 || true
    done
  fi

  manifest_py stack-json "$stack_name" | "${PYTHON_BIN:-python3}" -c '
import json, sys
stack = json.load(sys.stdin)
for c in stack["containers"]:
    print(c["container_name"])
' | while read -r container_name; do
    repo_name="${PROJECT_PREFIX}-${container_name}"
    run_or_dry "delete ECR repository ${repo_name}" -- \
      aws ecr delete-repository --repository-name "$repo_name" --force --region "$AWS_REGION" || true
  done
done

echo ""
echo "--- Cleaning up shared resources ---"

run_or_dry "delete ECS cluster ${CLUSTER_NAME}" -- \
  aws ecs delete-cluster --cluster "$CLUSTER_NAME" --region "$AWS_REGION" || true

if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY_RUN] Would delete security group ${SG_NAME} (if found)."
else
  SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${SG_NAME}" \
    --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION" 2>/dev/null || true)
  if [ -n "$SG_ID" ] && [ "$SG_ID" != "None" ]; then
    aws ec2 delete-security-group --group-id "$SG_ID" --region "$AWS_REGION" >/dev/null 2>&1 || true
    echo "Deleted security group ${SG_ID}."
  else
    echo "Security group ${SG_NAME} not found - nothing to delete."
  fi
fi

run_or_dry "detach the task execution policy from ${EXECUTION_ROLE_NAME}" -- \
  aws iam detach-role-policy --role-name "$EXECUTION_ROLE_NAME" \
  --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" || true
run_or_dry "delete IAM role ${EXECUTION_ROLE_NAME}" -- \
  aws iam delete-role --role-name "$EXECUTION_ROLE_NAME" || true

run_or_dry "delete log group ${LOG_GROUP}" -- \
  aws logs delete-log-group --log-group-name "$LOG_GROUP" --region "$AWS_REGION" || true

if [ "$DRY_RUN" != "true" ]; then
  rm -f "$STATE_FILE"
fi

echo ""
echo "=== Cleanup complete ==="
