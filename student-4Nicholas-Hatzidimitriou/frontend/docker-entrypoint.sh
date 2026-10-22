#!/bin/sh
set -e

export STUDENT4_BACKEND_URL="${STUDENT4_BACKEND_URL:-http://student4-backend:5004}"
export STAFF_SERVICE_URL="${STAFF_SERVICE_URL:-http://staff-backend:5001}"

envsubst '${STUDENT4_BACKEND_URL} ${STAFF_SERVICE_URL}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

FLASK_RUN_PORT=8104 python app.py &

exec nginx -g 'daemon off;'
