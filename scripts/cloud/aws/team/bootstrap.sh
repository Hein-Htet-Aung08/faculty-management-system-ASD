#!/bin/bash
# One-time, team-lead-only setup: deploys bootstrap/oidc-role.yaml (the
# GitHub OIDC provider + the role cloud-deployment.yml assumes). Prints the
# role ARN and the exact `gh variable set` commands to run afterward - does
# NOT run them itself. Setting GitHub repo variables needs a GitHub
# account with admin on the repo, which is a separate credential and a
# separate decision from the AWS credentials this script uses; this script
# only ever calls AWS, never gh.
#
# TODO(owner: team lead): read bootstrap/oidc-role.yaml's own TODOs and
# review the trust policy + permissions BEFORE running this for real - they
# are deliberately placeholders, not something to deploy blindly.
#
# Inputs: config.env, plus GITHUB_ORG and GITHUB_REPO environment variables
# (not stored in config.env - these identify the GitHub side, not AWS).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/common.sh"

: "${GITHUB_ORG:?Set GITHUB_ORG, e.g. GITHUB_ORG=Hein-Htet-Aung08}"
: "${GITHUB_REPO:?Set GITHUB_REPO, e.g. GITHUB_REPO=faculty-management-system-ASD}"

STACK_NAME="${PROJECT_PREFIX}-github-oidc"
TEMPLATE_FILE="${SCRIPT_DIR}/bootstrap/oidc-role.yaml"

echo "=== Team AWS deployment: bootstrap (team lead only) ==="
confirm_account

run_or_dry "deploy the OIDC provider + role CloudFormation stack ${STACK_NAME}" -- \
  aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --parameter-overrides "GitHubOrg=${GITHUB_ORG}" "GitHubRepo=${GITHUB_REPO}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION"

if [ "$DRY_RUN" = "true" ]; then
  ROLE_ARN="arn:aws:iam::<account-id>:role/${PROJECT_PREFIX}-github-actions-role"
else
  ROLE_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" --output text --region "$AWS_REGION")
fi

echo ""
echo "=== Bootstrap complete ==="
echo "Role ARN: ${ROLE_ARN}"
echo ""
echo "Run these yourself, as a GitHub user with admin on the repo (needs gh"
echo "auth login first; this script never touches GitHub, only AWS):"
echo ""
echo "  gh variable set AWS_ROLE_ARN --body \"${ROLE_ARN}\""
echo "  gh variable set AWS_REGION --body \"${AWS_REGION}\""
echo ""
echo "cloud-deployment.yml reads both of these as repository variables -"
echo "see .github/workflows/cloud-deployment.yml."
