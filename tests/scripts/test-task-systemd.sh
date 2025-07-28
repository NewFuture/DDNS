#!/bin/bash
# Systemd Task Management Test Script
# Tests DDNS task functionality with systemd on Linux systems
# Exits with non-zero status on verification failure
# Usage: test-task-systemd.sh [DDNS_COMMAND]
# Examples:
#   test-task-systemd.sh                      (uses default: python3 -m ddns)
#   test-task-systemd.sh ddns                 (uses ddns command)
#   test-task-systemd.sh ./dist/ddns          (uses binary executable)
#   test-task-systemd.sh "python -m ddns"     (uses custom python command)

set -e  # Exit on any error
PYTHON_CMD=${PYTHON_CMD:-python3}

# Check if DDNS command is provided as argument
if [[ -z "$1" ]]; then
    DDNS_CMD="$PYTHON_CMD -m ddns"
else
    DDNS_CMD="$1"
fi

echo "=== DDNS Task Management Test for Linux/Systemd ==="
echo "DDNS Command: $DDNS_CMD"
echo ""

# Check if systemd is available
if ! command -v systemctl >/dev/null 2>&1; then
    echo "❌ systemctl not available - skipping systemd tests"
    exit 1
fi

# Function to check systemd timer and validate task existence
check_systemd_timer() {
    local expected_state=$1  # "exists" or "not_exists"
    
    echo "Checking systemd timer..."
    if systemctl list-timers --all 2>/dev/null | grep -q "ddns"; then
        echo "✅ DDNS systemd timer found"
        systemctl status ddns.timer 2>/dev/null | head -5 || true
        if [[ "$expected_state" == "not_exists" ]]; then
            echo "❌ VERIFICATION FAILED: Timer should not exist but was found"
            return 1
        fi
    else
        echo "ℹ️ No DDNS systemd timer found"
        if [[ "$expected_state" == "exists" ]]; then
            echo "❌ VERIFICATION FAILED: Timer should exist but was not found"
            return 1
        fi
    fi
    return 0
}

check_ddns_status() {
    local expected_status=$1  # "Yes" or "No"
    local status_output
    
    echo "Checking DDNS status..."
    status_output=$($DDNS_CMD task --status | grep "Installed:" | head -1 || echo "Installed: Unknown")
    echo "Status: $status_output"
    
    if echo "$status_output" | grep -q "Installed.*$expected_status"; then
        echo "✅ DDNS status verification passed (Expected: $expected_status)"
        return 0
    else
        echo "❌ VERIFICATION FAILED: Expected 'Installed: $expected_status', got '$status_output'"
        return 1
    fi
}

# Test Step 1: Initial state check
echo "=== Step 1: Initial state verification ==="
$DDNS_CMD task -h
$DDNS_CMD task --status
initial_status=$($DDNS_CMD task --status | grep "Installed:" | head -1 || echo "Installed: Unknown")
echo "Initial status: $initial_status"

# Check initial system state
echo ""
echo "=== Step 2: Initial systemd state verification ==="
check_systemd_timer "not_exists" || exit 1

# Test Step 3: Install task
echo ""
echo "=== Step 3: Installing DDNS task ==="
if echo "$initial_status" | grep -q "Installed.*No"; then
    echo "Installing task with 10-minute interval..."
    sudo $DDNS_CMD task --install 10 || {
        echo "❌ VERIFICATION FAILED: Task installation failed"
        exit 1
    }
    echo "✅ Task installation command completed"
else
    echo "Task already installed, proceeding with verification..."
fi

# Test Step 4: Verify installation
echo ""
echo "=== Step 4: Verifying installation ==="
check_ddns_status "Yes" || exit 1

# Check systemd state after installation
echo ""
echo "=== Step 5: Systemd verification after installation ==="
check_systemd_timer "exists" || exit 1

# Verify systemd service files exist
echo "Checking systemd service files..."
if systemctl cat ddns.service >/dev/null 2>&1; then
    echo "✅ DDNS systemd service found"
else
    echo "❌ VERIFICATION FAILED: DDNS systemd service not found"
    exit 1
fi

if systemctl cat ddns.timer >/dev/null 2>&1; then
    echo "✅ DDNS systemd timer found"
else
    echo "❌ VERIFICATION FAILED: DDNS systemd timer not found"
    exit 1
fi

# Test Step 6: Delete task
echo ""
echo "=== Step 6: Deleting DDNS task ==="
sudo $DDNS_CMD task --delete || {
    echo "❌ VERIFICATION FAILED: Task deletion failed"
    exit 1
}
echo "✅ Task deletion command completed"

# Test Step 7: Verify deletion
echo ""
echo "=== Step 7: Verifying deletion ==="
check_ddns_status "No" || exit 1

# Final systemd state verification
echo ""
echo "=== Step 8: Final systemd state verification ==="
check_systemd_timer "not_exists" || exit 1

# Verify systemd service files are removed
echo "Checking systemd service files removal..."
if systemctl cat ddns.service >/dev/null 2>&1; then
    echo "❌ VERIFICATION FAILED: DDNS systemd service still exists"
    exit 1
else
    echo "✅ DDNS systemd service properly removed"
fi

if systemctl cat ddns.timer >/dev/null 2>&1; then
    echo "❌ VERIFICATION FAILED: DDNS systemd timer still exists"
    exit 1
else
    echo "✅ DDNS systemd timer properly removed"
fi

# Test help commands availability
echo ""
echo "=== Step 9: Help commands verification ==="
if $DDNS_CMD task --help | head -10 | grep -q "install\|uninstall\|enable\|disable\|status"; then
    echo "✅ Task commands found in help"
else
    echo "❌ VERIFICATION FAILED: Task commands missing from help"
    exit 1
fi

echo ""
echo "🎉 ================================================="
echo "🎉 ALL TESTS PASSED - Systemd task management OK"
echo "🎉 ================================================="
echo ""

exit 0
