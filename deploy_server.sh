#!/usr/bin/env bash
set -uo pipefail

# ============================================
# Deploy bumblebee eval server
# Usage: bash deploy_server.sh [start|stop|restart|status|switch-mode]
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
    sleep 1
    if [ -f "$GUNICORN_PID" ]; then
        echo "Gunicorn started (PID: $(cat "$GUNICORN_PID"))"
    else
        echo "Gunicorn started (PID file pending)"
    fi
}

stop_gunicorn() {
    if [ -f "$GUNICORN_PID" ]; then
        echo "Stopping Gunicorn..."
        kill "$(cat "$GUNICORN_PID")" 2>/dev/null || true
        rm -f "$GUNICORN_PID"
    fi
    # Also kill any orphaned gunicorn processes
    pkill -f "gunicorn.*wsgi:app" 2>/dev/null || true
    echo "Gunicorn stopped."
}

start_nginx() {
    if command -v nginx &>/dev/null; then
        echo "Starting Nginx..."
        nginx -s stop 2>/dev/null || true
        sleep 1
        nginx -c "$NGINX_CONF"
        echo "Nginx started on http://localhost:8080"
    else
        echo "Nginx not found, skipping (access Gunicorn directly on port 5050)"
    fi
}

stop_nginx() {
    if command -v nginx &>/dev/null; then
        echo "Stopping Nginx..."
        nginx -s stop 2>/dev/null || true
        echo "Nginx stopped."
    fi
}

show_status() {
    echo "=== Server Status ==="
    CURRENT_MODE=$(grep '^MODE' "$APP_DIR/constants.py" | head -1 | sed 's/[^"]*"\([^"]*\)".*/\1/')
    echo "Mode:     $CURRENT_MODE"
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
    switch-mode)
        # Switch between calibration and full mode
        CURRENT_MODE=$(grep '^MODE' "$APP_DIR/constants.py" | head -1 | sed 's/[^"]*"\([^"]*\)".*/\1/')
        if [ "$CURRENT_MODE" = "calibration" ]; then
            NEW_MODE="full"
        else
            NEW_MODE="calibration"
        fi
        echo "Switching mode: $CURRENT_MODE -> $NEW_MODE"
        # macOS uses sed -i '', Linux uses sed -i
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/^MODE = \"${CURRENT_MODE}\"/MODE = \"${NEW_MODE}\"/" "$APP_DIR/constants.py"
        else
            sed -i "s/^MODE = \"${CURRENT_MODE}\"/MODE = \"${NEW_MODE}\"/" "$APP_DIR/constants.py"
        fi
        echo "Using pre-generated metadata: assets/bumblebee_images_metadata_${NEW_MODE}.json"
        # Clear sessions (required — session stores subset/index from old mode)
        rm -rf "$APP_DIR/flask_session/"* 2>/dev/null || true
        echo "Sessions cleared."
        # Restart server
        stop_nginx
        stop_gunicorn
        sleep 1
        start_gunicorn
        start_nginx
        echo ""
        echo "Server restarted in $NEW_MODE mode at http://localhost:8080"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|switch-mode}"
        exit 1
        ;;
esac
