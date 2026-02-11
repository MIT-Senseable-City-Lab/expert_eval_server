#!/usr/bin/env bash
set -euo pipefail

micromamba activate tools 

NGX_ROOT="/data/vision/beery/scratch/julia/.config/nginx"
CONF="$NGX_ROOT/nginx.conf"
PID="$NGX_ROOT/nginx.pid"

# Clean up stale pid file
rm -f "$PID"

# Ensure dirs exist
mkdir -p \
  "$NGX_ROOT/var/log/nginx" \
  "$NGX_ROOT/var/tmp/nginx/client_body" \
  "$NGX_ROOT/var/tmp/nginx/proxy" \
  "$NGX_ROOT/var/tmp/nginx/fastcgi" \
  "$NGX_ROOT/var/tmp/nginx/uwsgi" \
  "$NGX_ROOT/var/tmp/nginx/scgi"

# Start nginx fresh
nginx -p "$NGX_ROOT" -c "$CONF"

# Verify master is running
ps -ef | grep [n]ginx
cat "$PID"
ss -ltnp | grep nginx || true

# Test locally
curl -sS http://127.0.0.1:8080/ | head


# nginx -t -c /data/vision/beery/scratch/julia/.config/nginx/nginx.conf 
# nginx -s reload -c /data/vision/beery/scratch/julia/.config/nginx/nginx.conf