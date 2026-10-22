#!/bin/sh
# Run by the nginx image on startup. Lets one image point at any backend URL
# (local, or the cloud load balancer) without rebuilding.
set -e

if [ -n "$API_BASE" ]; then
    printf 'window.APP_CONFIG = { API_BASE: "%s" };\n' "$API_BASE" > /usr/share/nginx/html/js/config.js
    echo "Staff frontend: API_BASE set to $API_BASE"
fi
