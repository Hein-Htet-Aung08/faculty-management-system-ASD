#!/bin/bash
# Shared helpers sourced by every script in this folder. Not meant to be
# run directly - `source common.sh` at the top of each script.

set -euo pipefail

TEAM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${TEAM_DIR}/config.env"

if [ -f "$CONFIG_FILE" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
else
  echo "Missing $CONFIG_FILE - copy config.env.example to config.env and fill it in first." >&2
  exit 1
fi

: "${AWS_REGION:?AWS_REGION must be set in config.env}"
PROJECT_PREFIX="${PROJECT_PREFIX:-faculty-fms}"

# The AWS CLI opens a pager (less) for some commands by default, which hangs
# a non-interactive script forever waiting for a keypress it will never
# get. The personal test hit this directly - always disable it.
export AWS_PAGER=""

if [ -n "${AWS_PROFILE:-}" ]; then
  export AWS_PROFILE
fi

DRY_RUN="${DRY_RUN:-false}"

# Prints which account/region/prefix a script is about to act against, and
# requires typed confirmation before continuing - skipped automatically in
# CI (GitHub Actions sets CI itself) or if SKIP_CONFIRM is set. Never calls
# AWS at all when DRY_RUN=true, per this folder's "dry-run only" contract.
confirm_account() {
  local account_id
  if [ "$DRY_RUN" = "true" ]; then
    account_id="<not queried - DRY_RUN=true>"
  else
    account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "UNKNOWN (not authenticated)")
  fi

  echo "Account: ${account_id}, Region: ${AWS_REGION}, Prefix: ${PROJECT_PREFIX}"

  if [ "$DRY_RUN" = "true" ]; then
    echo "(DRY_RUN=true - no AWS calls will be made by this script.)"
    return 0
  fi

  if [ -n "${CI:-}" ] || [ -n "${SKIP_CONFIRM:-}" ]; then
    return 0
  fi

  read -r -p "Proceed against this account/region/prefix? Type 'yes' to continue: " CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    echo "Confirmation did not match. Aborting." >&2
    exit 1
  fi
}

# Usage: run_or_dry "description" -- command arg1 arg2 ...
# In DRY_RUN=true mode, prints what would run and returns success without
# executing it - no AWS call happens. Otherwise runs it for real.
run_or_dry() {
  local description="$1"
  shift
  if [ "$1" != "--" ]; then
    echo "run_or_dry: expected -- before the command" >&2
    exit 1
  fi
  shift

  if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY_RUN] Would: ${description}"
    echo "          Command: $*"
    return 0
  fi

  echo "--- ${description} ---"
  "$@"
}

manifest_py() {
  local python_bin="${PYTHON_BIN:-python3}"
  "$python_bin" "${TEAM_DIR}/deploy/manifest.py" "$@"
}
