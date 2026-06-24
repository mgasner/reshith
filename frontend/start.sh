#!/bin/sh
set -e

PORT="${PORT:-80}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

sed "s|__PORT__|${PORT}|g; s|__BACKEND_URL__|${BACKEND_URL}|g" \
    /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
