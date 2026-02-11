#!/usr/bin/env bash
# set -euo pipefail

# ---- paths (EDIT THESE) ----
APP_NAME="human_identity_eval"                    # for process matching
NGX_ROOT="/data/vision/beery/scratch/julia/.config/nginx"
CONF="$NGX_ROOT/nginx.conf"
PID="$NGX_ROOT/nginx.pid"
GUNICORN_PORT="5001"                               # your gunicorn bind
NGINX_PORT="8080"                                  # your nginx listen
SESSION_DIR="/data/vision/beery/fgg_ai/finegrained_metric_intern/server/human_identity_eval/flask_session"        # set this in Flask config (see below)

# ---- stop nginx (user-space) ----
if [[ -f "$PID" ]]; then
  echo "[*] Stopping nginx via PID file"
  kill -QUIT "$(cat "$PID")" || true
  sleep 1
fi
# Fallback: any nginx owned by you
pkill -QUIT -u "$USER" nginx || true
sleep 1
pkill -TERM -u "$USER" nginx || true
sleep 1
pkill -KILL -u "$USER" nginx || true

# ---- stop gunicorn cleanly ----
echo "[*] Stopping gunicorn"
pkill -QUIT -f "gunicorn: master \[${APP_NAME}\]" || true
sleep 1
pkill -TERM -f "gunicorn.*${APP_NAME}" || true
sleep 1
pkill -KILL -f "gunicorn.*${APP_NAME}" || true

# ---- verify ports freed ----
echo "[*] Checking ports"
ss -ltnp "( sport = :${NGINX_PORT} )" | cat || true
ss -ltnp "( sport = :${GUNICORN_PORT} )" | cat || true

# ---- purge nginx temp/cache/logs ----
echo "[*] Purging nginx temp/cache/logs under $NGX_ROOT"
rm -f  "$PID"
rm -rf "$NGX_ROOT/var/tmp/nginx"/* || true
# If you configured a proxy_cache_path, also rm -rf that directory here.
: > "$NGX_ROOT/var/log/nginx/access.log" 2>/dev/null || true
: > "$NGX_ROOT/var/log/nginx/error.log"  2>/dev/null || true

# ---- purge Flask session store (optional but helpful during dev) ----
if [[ -d "$SESSION_DIR" ]]; then
  echo "[*] Clearing Flask-Session dir $SESSION_DIR"
  rm -rf "${SESSION_DIR:?}/"* || true
fi

echo "[*] Reset complete."
