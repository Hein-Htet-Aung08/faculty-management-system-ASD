#!/bin/bash
# Builds and pushes one ECR image per container, for every stack marked
# status: ready in deploy/services.yaml. Stacks still marked status: todo
# are skipped with a warning - or the whole script fails loudly if
# STRICT=true, instead of guessing at an incomplete stack's values.
#
# Inputs: config.env, .env.team-deploy (from env-setup.sh), and optionally
# STRICT=true.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/common.sh"

STATE_FILE="${SCRIPT_DIR}/.env.team-deploy"
if [ -f "$STATE_FILE" ]; then
  # shellcheck disable=SC1090
  source "$STATE_FILE"
fi

STRICT="${STRICT:-false}"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

echo "=== Team AWS deployment: build and push images ==="
confirm_account

if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY_RUN] Would log in to ECR."
  REGISTRY="<account-id>.dkr.ecr.${AWS_REGION}.amazonaws.com"
else
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
  aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRY"
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
  echo "=== Building stack: ${stack_name} ==="

  manifest_py stack-json "$stack_name" | "$(command -v python3)" -c '
import json, sys
stack = json.load(sys.stdin)
for c in stack["containers"]:
    print(c["container_name"], c["build"]["context"], c["build"]["dockerfile"], sep="\t")
' | while IFS=$'\t' read -r container_name build_context build_dockerfile; do
    repo_name="${PROJECT_PREFIX}-${container_name}"
    image_tag="${REGISTRY}/${repo_name}:latest"

    if [ "$DRY_RUN" = "true" ]; then
      echo "[DRY_RUN] Would ensure ECR repository ${repo_name} exists."
    else
      aws ecr describe-repositories --repository-names "$repo_name" --region "$AWS_REGION" >/dev/null 2>&1 \
        || aws ecr create-repository --repository-name "$repo_name" --region "$AWS_REGION" >/dev/null
    fi

    run_or_dry "build ${repo_name}" -- \
      docker build -t "$image_tag" -f "${REPO_ROOT}/${build_dockerfile}" "${REPO_ROOT}/${build_context}"
    run_or_dry "push ${repo_name}" -- docker push "$image_tag"
  done
done

echo ""
echo "=== Image build complete ==="
