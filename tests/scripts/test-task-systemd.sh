#!/bin/bash
# Systemd task lifecycle test for DDNS.
# Usage: test-task-systemd.sh [DDNS_COMMAND]

set -e

PYTHON_CMD=${PYTHON_CMD:-python3}
DDNS_CMD=${1:-"$PYTHON_CMD -m ddns"}
CREATED_TASK=0
TASK_DOMAIN="systemd-e2e.example.com"
TASK_IP="192.0.2.55"

if [[ "$DDNS_CMD" != *" "* && -f "$DDNS_CMD" ]]; then
    DDNS_CMD=$(realpath "$DDNS_CMD")
fi

run_ddns_task() {
    $DDNS_CMD task --scheduler systemd "$@"
}

run_ddns_task_as_root() {
    sudo $DDNS_CMD task --scheduler systemd "$@"
}

cleanup() {
    local status=$?
    trap - EXIT
    if [[ "$CREATED_TASK" == "1" ]]; then
        echo "Cleaning up DDNS systemd task..."
        run_ddns_task_as_root --uninstall >/dev/null 2>&1 || true
        sudo systemctl stop ddns.timer >/dev/null 2>&1 || true
        sudo systemctl disable ddns.timer >/dev/null 2>&1 || true
        sudo rm -f /etc/systemd/system/ddns.service /etc/systemd/system/ddns.timer
        sudo systemctl daemon-reload >/dev/null 2>&1 || true
    fi
    exit "$status"
}
trap cleanup EXIT

check_status() {
    local expected_installed=$1
    local expected_enabled=${2:-}
    local output
    output=$(run_ddns_task --status)
    echo "$output"

    if ! echo "$output" | grep -q "Installed: $expected_installed"; then
        echo "Expected Installed: $expected_installed"
        return 1
    fi
    if [[ -n "$expected_enabled" ]] && ! echo "$output" | grep -q "Enabled: $expected_enabled"; then
        echo "Expected Enabled: $expected_enabled"
        return 1
    fi
}

check_systemd_state() {
    local expected=$1
    local enabled
    local active
    enabled=$(systemctl is-enabled ddns.timer 2>/dev/null || true)
    active=$(systemctl is-active ddns.timer 2>/dev/null || true)
    echo "systemd state: enabled=$enabled active=$active"

    if [[ "$expected" == "enabled" ]]; then
        [[ "$enabled" == "enabled" ]]
        [[ "$active" == "active" ]]
    else
        [[ "$enabled" != "enabled" ]]
        [[ "$active" != "active" ]]
    fi
}

echo "=== DDNS systemd task lifecycle ==="
echo "DDNS command: $DDNS_CMD"

if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl is required"
    exit 1
fi
if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required"
    exit 1
fi
if ! sudo -n true >/dev/null 2>&1; then
    echo "Passwordless sudo is required"
    exit 1
fi
if ! systemctl list-units >/dev/null 2>&1; then
    echo "A running systemd instance is required"
    exit 1
fi

echo "=== Initial state ==="
run_ddns_task --help | grep -q "install"
check_status "No"
if [[ -e /etc/systemd/system/ddns.service || -e /etc/systemd/system/ddns.timer ]]; then
    echo "Refusing to replace an existing DDNS systemd task"
    exit 1
fi
if systemctl list-timers --all 2>/dev/null | grep -q "ddns.timer"; then
    echo "Refusing to replace an existing DDNS timer"
    exit 1
fi

echo "=== Install ==="
CREATED_TASK=1
run_ddns_task_as_root \
    --install 10 \
    --dns debug \
    --ipv4 "$TASK_DOMAIN" \
    --index4 "shell:printf $TASK_IP" \
    --no-cache
check_status "Yes" "True"
check_systemd_state "enabled"
systemctl cat ddns.service >/dev/null
systemctl cat ddns.timer >/dev/null
grep -q "OnUnitActiveSec=10m" /etc/systemd/system/ddns.timer
if [[ "$DDNS_CMD" == *"-m ddns"* ]]; then
    grep -q "ExecStart=.*-m ddns" /etc/systemd/system/ddns.service
else
    expected_executable=${DDNS_CMD%% *}
    grep -Fq "ExecStart=$expected_executable" /etc/systemd/system/ddns.service
fi

echo "=== Execute scheduled command ==="
sudo systemctl start ddns.service
[[ "$(systemctl show ddns.service --property=Result --value)" == "success" ]]
sudo journalctl -u ddns.service --no-pager -n 50 | grep -F "[IPv4] $TASK_IP"

echo "=== Disable ==="
run_ddns_task_as_root --disable
check_status "Yes" "False"
check_systemd_state "disabled"

echo "=== Enable ==="
run_ddns_task_as_root --enable
check_status "Yes" "True"
check_systemd_state "enabled"

echo "=== Uninstall ==="
run_ddns_task_as_root --uninstall
check_status "No"
check_systemd_state "disabled"
[[ ! -e /etc/systemd/system/ddns.service ]]
[[ ! -e /etc/systemd/system/ddns.timer ]]
if systemctl list-timers --all 2>/dev/null | grep -q "ddns.timer"; then
    echo "DDNS timer still exists after uninstall"
    exit 1
fi
CREATED_TASK=0

echo "=== DDNS systemd lifecycle passed ==="
