#!/bin/bash
# One-time (but safe to re-run) environment setup: the ECS service-linked
# role, the default VPC's subnets, one shared internal security group, and
# a Cloud Map / ECS Service Connect namespace so stacks reach each other by
# friendly name (e.g. http://staff-backend:5001) instead of a hardcoded IP.
#
# Every step checks for an existing resource first - re-running this after
# a partial failure is safe. Saves its output to .env.team-deploy (gitignored)
# so build-and-push-images.sh / deploy.sh / deployment-test.sh / cleanup.sh
# can load it automatically - each is its own subshell, so exported
# variables don't otherwise survive between separate script invocations.
#
# Inputs: config.env (AWS_REGION, AWS_PROFILE, PROJECT_PREFIX) - see
# config.env.example.
#
# TODO(owner: team lead): this sets up ONE shared internal security group
# allowing traffic between the team's own tasks. It does NOT yet create the
# Application Load Balancer or its public-facing security group for
# unified-home - that depends on unified-home's own ingress design being
# finalised first (see deploy/services.yaml's unified-home TODO). Add that
# once the team has decided it.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/common.sh"

STATE_FILE="${SCRIPT_DIR}/.env.team-deploy"
CLUSTER_NAME="${PROJECT_PREFIX}-cluster"
SG_NAME="${PROJECT_PREFIX}-internal-sg"
NAMESPACE_NAME="${PROJECT_PREFIX}.local"
EXECUTION_ROLE_NAME="${PROJECT_PREFIX}-ecs-execution-role"

echo "=== Team AWS deployment: environment setup ==="
confirm_account

# Step 1: ECS service-linked role. A fresh AWS account doesn't have this,
# and the first ECS service create fails without it - the personal test
# hit this directly (InvalidParameterException: Unable to assume the
# service linked role). create-service-linked-role errors if the role
# already exists, which is the expected outcome on every run after the
# first, so that failure is intentionally swallowed.
if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY_RUN] Would ensure the ECS service-linked role exists."
else
  echo "--- Ensuring the ECS service-linked role exists ---"
  aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com >/dev/null 2>&1 \
    && echo "Created AWSServiceRoleForECS." \
    || echo "AWSServiceRoleForECS already exists (expected after the first run)."
fi

# Step 2: ECS task execution role (lets Fargate pull images from ECR and
# write to CloudWatch Logs on the team's behalf - distinct from the
# service-linked role above, which is AWS's own role for managing the
# service itself).
if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY_RUN] Would ensure IAM role ${EXECUTION_ROLE_NAME} exists with AmazonECSTaskExecutionRolePolicy attached."
  EXECUTION_ROLE_ARN="arn:aws:iam::<account-id>:role/${EXECUTION_ROLE_NAME}"
else
  echo "--- Ensuring ECS task execution role ${EXECUTION_ROLE_NAME} exists ---"
  if ! aws iam get-role --role-name "$EXECUTION_ROLE_NAME" >/dev/null 2>&1; then
    cat > /tmp/ecs-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF
    aws iam create-role --role-name "$EXECUTION_ROLE_NAME" \
      --assume-role-policy-document file:///tmp/ecs-trust-policy.json >/dev/null
    aws iam attach-role-policy --role-name "$EXECUTION_ROLE_NAME" \
      --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
    echo "Created ${EXECUTION_ROLE_NAME}."
  else
    echo "${EXECUTION_ROLE_NAME} already exists."
  fi
  EXECUTION_ROLE_ARN=$(aws iam get-role --role-name "$EXECUTION_ROLE_NAME" --query "Role.Arn" --output text)
fi

# Step 3: networking - the default VPC and its subnets, same approach the
# personal test used. A dedicated non-default VPC is a reasonable future
# improvement but out of scope for this skeleton.
if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY_RUN] Would look up the default VPC and its subnets."
  VPC_ID="vpc-<dry-run-placeholder>"
  SUBNET_IDS="subnet-<dry-run-placeholder-1>,subnet-<dry-run-placeholder-2>"
else
  echo "--- Looking up the default VPC ---"
  VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
    --query "Vpcs[0].VpcId" --output text --region "$AWS_REGION")
  SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" \
    --query "Subnets[].SubnetId" --output text --region "$AWS_REGION" | tr '\t' ',')
  echo "VPC: ${VPC_ID}"
  echo "Subnets: ${SUBNET_IDS}"
fi

# Step 4: one shared internal security group - every task can reach every
# other task on any port. Good enough for a student project behind no
# public ingress yet; tighten to per-port rules once the manifest is fully
# filled in, if the team wants to.
if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY_RUN] Would ensure security group ${SG_NAME} exists (self-referencing ingress, all traffic)."
  SECURITY_GROUP_ID="sg-<dry-run-placeholder>"
else
  echo "--- Ensuring security group ${SG_NAME} exists ---"
  EXISTING_SG=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
    --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION" 2>/dev/null || true)

  if [ -z "$EXISTING_SG" ] || [ "$EXISTING_SG" = "None" ]; then
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
      --group-name "$SG_NAME" \
      --description "${PROJECT_PREFIX} - internal traffic between the team's own tasks" \
      --vpc-id "$VPC_ID" --region "$AWS_REGION" --query "GroupId" --output text)
    aws ec2 authorize-security-group-ingress --group-id "$SECURITY_GROUP_ID" \
      --protocol -1 --source-group "$SECURITY_GROUP_ID" --region "$AWS_REGION" >/dev/null
    echo "Created ${SECURITY_GROUP_ID}."
  else
    SECURITY_GROUP_ID="$EXISTING_SG"
    echo "${SG_NAME} already exists (${SECURITY_GROUP_ID})."
  fi
fi

# Step 5: ECS cluster (created here, not in deploy.sh, since Service
# Connect namespace association happens at cluster-creation time).
if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY_RUN] Would ensure ECS cluster ${CLUSTER_NAME} exists, with Service Connect namespace ${NAMESPACE_NAME}."
else
  echo "--- Ensuring ECS cluster ${CLUSTER_NAME} exists ---"
  if ! aws ecs describe-clusters --clusters "$CLUSTER_NAME" --region "$AWS_REGION" \
      --query "clusters[0].status" --output text 2>/dev/null | grep -qx ACTIVE; then
    aws ecs create-cluster --cluster-name "$CLUSTER_NAME" \
      --service-connect-defaults "namespace=${NAMESPACE_NAME}" \
      --region "$AWS_REGION" >/dev/null
    echo "Created ${CLUSTER_NAME} with Service Connect namespace ${NAMESPACE_NAME}."
  else
    echo "${CLUSTER_NAME} already exists."
  fi
fi

if [ "$DRY_RUN" != "true" ]; then
  cat > "$STATE_FILE" <<EOF
AWS_REGION=${AWS_REGION}
PROJECT_PREFIX=${PROJECT_PREFIX}
VPC_ID=${VPC_ID}
SUBNET_IDS=${SUBNET_IDS}
SECURITY_GROUP_ID=${SECURITY_GROUP_ID}
EXECUTION_ROLE_ARN=${EXECUTION_ROLE_ARN}
CLUSTER_NAME=${CLUSTER_NAME}
NAMESPACE_NAME=${NAMESPACE_NAME}
EOF
  echo ""
  echo "=== Environment setup complete - state saved to ${STATE_FILE} ==="
else
  echo ""
  echo "=== DRY_RUN complete - no AWS calls were made, no state file written ==="
fi
