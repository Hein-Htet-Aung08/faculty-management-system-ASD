#!/bin/sh
# Point the static pages at the backend for this deployment. nginx:alpine runs
# everything in /docker-entrypoint.d/ before starting the server.
set -e

: "${BACKEND_URL:=http://localhost:5301}"

cat > /usr/share/nginx/html/js/config.js <<CONFIG
window.BACKEND_URL = "${BACKEND_URL}";
CONFIG

echo "frontend-service: backend URL set to ${BACKEND_URL}"
