#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Deploy bumblebee eval server (local Mac)
# Usage: bash deploy_server.sh [start|stop|restart|status]
# ============================================

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
NGINX_CONF="$APP_DIR/nginx.conf"
GUNICORN_PID="$APP_DIR/logs/gunicorn.pid"

# Ensure logs directory exists
mkdir -p "$APP_DIR/logs"

start_gunicorn() {
    echo "Starting Gunicorn..."
    cd "$APP_DIR"

    # Activate venv if it exists
    if [ -f "$APP_DIR/venv/bin/activate" ]; then
        source "$APP_DIR/venv/bin/activate"
    fi

    gunicorn -c gunicorn_config.py wsgi:app \
        --pid "$GUNICORN_PID" \
        --daemon
    echo "Gunicorn started (PID: $(cat "$GUNICORN_PID"))"
}

stop_gunicorn() {
    if [ -f "$GUNICORN_PID" ]; then
        echo "Stopping Gunicorn..."
        kill "$(cat "$GUNICORN_PID")" 2>/dev/null || true
        rm -f "$GUNICORN_PID"
        echo "Gunicorn stopped."
    else
        echo "Gunicorn not running (no PID file)."
    fi
}

start_nginx() {
    echo "Starting Nginx..."
    # Stop any existing nginx first
    nginx -s stop 2>/dev/null || true
    sleep 1
    nginx -c "$NGINX_CONF"
    echo "Nginx started on http://localhost:8080"
}

stop_nginx() {
    echo "Stopping Nginx..."
    nginx -s stop 2>/dev/null || true
    echo "Nginx stopped."
}

show_status() {
    echo "=== Server Status ==="
    if [ -f "$GUNICORN_PID" ] && kill -0 "$(cat "$GUNICORN_PID")" 2>/dev/null; then
        echo "Gunicorn: RUNNING (PID: $(cat "$GUNICORN_PID"))"
    else
        echo "Gunicorn: STOPPED"
    fi
    if pgrep -x nginx > /dev/null 2>&1; then
        echo "Nginx:    RUNNING"
    else
        echo "Nginx:    STOPPED"
    fi
    echo ""
    echo "App URL: http://localhost:8080"
}

case "${1:-start}" in
    start)
        start_gunicorn
        start_nginx
        echo ""
        echo "Server is running at http://localhost:8080"
        ;;
    stop)
        stop_nginx
        stop_gunicorn
        ;;
    restart)
        stop_nginx
        stop_gunicorn
        sleep 1
        start_gunicorn
        start_nginx
        echo ""
        echo "Server restarted at http://localhost:8080"
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
