#!/usr/bin/env bash
# Hard reset: kill all processes, clear sessions/logs
# Usage: bash reset_server.sh

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
GUNICORN_PID="$APP_DIR/logs/gunicorn.pid"
SESSION_DIR="$APP_DIR/flask_session"

# ---- stop nginx ----
echo "[*] Stopping nginx"
nginx -s stop 2>/dev/null || true
pkill -QUIT -u "$USER" nginx 2>/dev/null || true
sleep 1
pkill -KILL -u "$USER" nginx 2>/dev/null || true

# ---- stop gunicorn ----
echo "[*] Stopping gunicorn"
if [[ -f "$GUNICORN_PID" ]]; then
    kill "$(cat "$GUNICORN_PID")" 2>/dev/null || true
    rm -f "$GUNICORN_PID"
fi
pkill -f "gunicorn.*wsgi:app" 2>/dev/null || true
sleep 1
pkill -KILL -f "gunicorn.*wsgi:app" 2>/dev/null || true

# ---- verify ports freed ----
echo "[*] Checking ports 5001 and 8080"
lsof -i :5001 2>/dev/null || echo "  Port 5001: free"
lsof -i :8080 2>/dev/null || echo "  Port 8080: free"

# ---- clear logs ----
echo "[*] Clearing logs"
: > "$APP_DIR/logs/access.log" 2>/dev/null || true
: > "$APP_DIR/logs/error.log" 2>/dev/null || true
: > "$APP_DIR/logs/nginx_access.log" 2>/dev/null || true
: > "$APP_DIR/logs/nginx_error.log" 2>/dev/null || true

# ---- purge Flask sessions ----
if [[ -d "$SESSION_DIR" ]]; then
    echo "[*] Clearing Flask sessions in $SESSION_DIR"
    rm -rf "${SESSION_DIR:?}/"* 2>/dev/null || true
fi

echo "[*] Reset complete."
