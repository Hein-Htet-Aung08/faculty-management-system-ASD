#!/bin/sh
set -eu

if [ -n "${API_BASE:-}" ]; then
    printf 'window.APP_CONFIG = { API_BASE: "%s" };\n' \
        "$API_BASE" > /usr/share/nginx/html/js/config.js
fi