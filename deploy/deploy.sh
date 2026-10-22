
#!/usr/bin/env bash
set -Eeuo pipefail

# Faculty Management System - Release 2
# Reusable AWS EC2 deployment script
#
# Run from the repository:
#   ./deploy/deploy.sh
#
# Uses both the local Compose configuration and cloud override.
# Does not modify the local Docker Compose configuration.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE=(
    docker compose
    -f docker-compose.yml
    -f docker-compose.cloud.yml
)

echo "==========================================="
echo " Faculty Management System - AWS Deployment"
echo "==========================================="

echo "[1/6] Checking dependencies..."

command -v docker >/dev/null || {
    echo "ERROR: Docker is not installed."
    exit 1
}

docker compose version

echo "[2/6] Validating cloud configuration..."

"${COMPOSE[@]}" config --quiet

echo "[3/6] Validating gateway configuration..."

if [[ ! -s deploy/nginx.conf ]]; then
    echo "ERROR: deploy/nginx.conf is missing or empty."
    exit 1
fi

docker run --rm \
    --entrypoint nginx \
    -v "$ROOT_DIR/deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro" \
    nginx:1.27-alpine \
    -t

echo "[4/6] Building and deploying containers..."

"${COMPOSE[@]}" up \
    -d \
    --build \
    --remove-orphans \
    --wait

echo "[5/6] Checking container status..."

"${COMPOSE[@]}" ps

echo "[6/6] Recording deployment information..."

echo "Git commit: $(git rev-parse HEAD)"
echo "Deployment timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

echo
echo "==========================================="
echo " Deployment commands completed."
echo "==========================================="
echo
echo "IMPORTANT:"
echo "Verify all five frontends, backends, databases,"
echo "and CRUD operations before approving the release."
