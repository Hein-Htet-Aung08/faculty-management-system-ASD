#!/bin/sh
set -e

export STUDENT4_BACKEND_URL="${STUDENT4_BACKEND_URL:-http://student4-backend:5004}"
export STAFF_SERVICE_URL="${STAFF_SERVICE_URL:-http://staff-backend:5001}"

# nginx needs this because proxy_pass uses a variable (not a literal host),
# which forces it to resolve through the configured `resolver` instead of
# falling back to /etc/hosts for "localhost". That resolver address differs
# by environment - Docker Compose's embedded DNS is always 127.0.0.11, but
# Fargate has no such address - so read the real one from /etc/resolv.conf
# instead of hardcoding either.
export RESOLVER_IP="$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf)"
export RESOLVER_IP="${RESOLVER_IP:-127.0.0.11}"

envsubst '${STUDENT4_BACKEND_URL} ${STAFF_SERVICE_URL} ${RESOLVER_IP}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

FLASK_RUN_PORT=8104 python app.py &

exec nginx -g 'daemon off;'
