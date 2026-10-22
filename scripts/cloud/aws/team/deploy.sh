#!/bin/bash
# Deploys one ECS Fargate task per stack marked status: ready in
# deploy/services.yaml, with ECS Service Connect enabled so other stacks'
# cross-stack env vars (e.g. http://staff-backend:5001) resolve correctly -
# this replaces the personal test's two-phase "register with a placeholder
# public IP, read the real one back, re-register" approach entirely, which
# was only ever needed because that test had no service discovery and no
# reverse proxy. Internal stacks get no public IP at all here
# (assignPublicIp=DISABLED) - only unified-home, once its own entry is
# ready, should need one (or sit behind the ALB instead).
#
# Stacks still marked status: todo are skipped with a warning, or the whole
# run fails immediately with STRICT=true.
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

STRICT="${STRICT:-false}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RENDER_PY="${SCRIPT_DIR}/deploy/render_task_def.py"
LOG_GROUP="/ecs/${PROJECT_PREFIX}"
CLUSTER_NAME="${PROJECT_PREFIX}-cluster"

echo "=== Team AWS deployment: deploy ==="
confirm_account

if [ "$DRY_RUN" = "true" ]; then
  REGISTRY="<account-id>.dkr.ecr.${AWS_REGION}.amazonaws.com"
  EXECUTION_ROLE_ARN="${EXECUTION_ROLE_ARN:-arn:aws:iam::<account-id>:role/${PROJECT_PREFIX}-ecs-execution-role}"
  SUBNET_IDS="${SUBNET_IDS:-subnet-<dry-run-placeholder>}"
  SECURITY_GROUP_ID="${SECURITY_GROUP_ID:-sg-<dry-run-placeholder>}"
  NAMESPACE_NAME="${NAMESPACE_NAME:-${PROJECT_PREFIX}.local}"
else
  : "${EXECUTION_ROLE_ARN:?Run env-setup.sh first (its output is saved to .env.team-deploy and loaded automatically)}"
  : "${SUBNET_IDS:?Run env-setup.sh first}"
  : "${SECURITY_GROUP_ID:?Run env-setup.sh first}"
  : "${NAMESPACE_NAME:?Run env-setup.sh first}"
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
fi

echo ""
while IFS=$'\t' read -r stack_name owner; do
  [ -z "$stack_name" ] && continue
  echo "SKIPPING stack '${stack_name}' (owner: ${owner}) - still status: todo in deploy/services.yaml."
  if [ "$STRICT" = "true" ]; then
    echo "STRICT=true: refusing to continue with an incomplete manifest." >&2
    exit 1
  fi
done < <(manifest_py todo-names)

for stack_name in $(manifest_py ready-names); do
  echo ""
  echo "=== Deploying stack: ${stack_name} ==="
  service_name="${PROJECT_PREFIX}-${stack_name}-service"
  task_family="${PROJECT_PREFIX}-${stack_name}-task"

  if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY_RUN] Would render task definition ${task_family} (see render_task_def.py task-def ${stack_name} ...)."
    echo "[DRY_RUN] Would create/update ECS service ${service_name} with Service Connect enabled, no public IP."
    continue
  fi

  "$PYTHON_BIN" "$RENDER_PY" task-def "$stack_name" "$REGISTRY" "$PROJECT_PREFIX" "$EXECUTION_ROLE_ARN" "$LOG_GROUP" "$AWS_REGION" \
    > "/tmp/${PROJECT_PREFIX}-${stack_name}-task-def.json"
  REVISION=$(aws ecs register-task-definition \
    --cli-input-json "file:///tmp/${PROJECT_PREFIX}-${stack_name}-task-def.json" \
    --region "$AWS_REGION" --query "taskDefinition.revision" --output text)
  echo "Registered ${task_family}:${REVISION}."

  "$PYTHON_BIN" "$RENDER_PY" service-connect-config "$stack_name" "$NAMESPACE_NAME" \
    > "/tmp/${PROJECT_PREFIX}-${stack_name}-service-connect.json"

  network_config="awsvpcConfiguration={subnets=[${SUBNET_IDS}],securityGroups=[${SECURITY_GROUP_ID}],assignPublicIp=DISABLED}"

  if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$service_name" --region "$AWS_REGION" \
      --query "services[0].status" --output text 2>/dev/null | grep -qx ACTIVE; then
    aws ecs update-service --cluster "$CLUSTER_NAME" --service "$service_name" \
      --task-definition "${task_family}:${REVISION}" \
      --service-connect-configuration "file:///tmp/${PROJECT_PREFIX}-${stack_name}-service-connect.json" \
      --force-new-deployment --desired-count 1 --region "$AWS_REGION" >/dev/null
  else
    aws ecs create-service --cluster "$CLUSTER_NAME" --service-name "$service_name" \
      --task-definition "${task_family}:${REVISION}" --desired-count 1 --launch-type FARGATE \
      --network-configuration "$network_config" \
      --service-connect-configuration "file:///tmp/${PROJECT_PREFIX}-${stack_name}-service-connect.json" \
      --region "$AWS_REGION" >/dev/null
  fi

  echo "Waiting for ${service_name} to stabilise..."
  aws ecs wait services-stable --cluster "$CLUSTER_NAME" --services "$service_name" --region "$AWS_REGION"
  echo "${stack_name} deployed."
done

echo ""
echo "=== Deploy complete ==="
echo "TODO(owner: team lead): no public Application Load Balancer exists yet."
echo "Every stack deployed above is internal-only (no public IP) - nothing is"
echo "reachable from outside the VPC until unified-home's own stack entry in"
echo "deploy/services.yaml is filled in and an ALB is added pointed at it."
