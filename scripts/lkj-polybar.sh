#!/bin/bash
# Polybar module script for LKJ daemon status and control
# Usage: lkj-polybar.sh [check|stop]

LKJ_SERVICE="lkj-daemon.service"
ICON_RUNNING=""  # Microphone icon
ICON_STOPPED=""  # Muted microphone icon

check_status() {
    if systemctl --user is-active "$LKJ_SERVICE" &>/dev/null; then
        echo "$ICON_RUNNING"
        exit 0
    else
        echo "$ICON_STOPPED"
        exit 0
    fi
}

stop_daemon() {
    systemctl --user stop "$LKJ_SERVICE" &>/dev/null
    # Notify user
    notify-send "LKJ" "Daemon stopped" &>/dev/null || true
}

case "${1:-check}" in
    check)
        check_status
        ;;
    stop)
        stop_daemon
        ;;
    *)
        check_status
        ;;
esac
