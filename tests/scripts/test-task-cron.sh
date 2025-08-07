#!/bin/sh
# Cron Task Management Test Script
# Tests DDNS task functionality with cron on Linux systems
# Exits with non-zero status on verification failure
# Usage: test-task-cron.sh [DDNS_COMMAND]
# Examples:
#   test-task-cron.sh                      (uses default: python3 -m ddns)
#   test-task-cron.sh ddns                 (uses ddns command)
#   test-task-cron.sh ./dist/ddns          (uses binary executable)
#   test-task-cron.sh "python -m ddns"     (uses custom python command)

set -e  # Exit on any error
PYTHON_CMD=${PYTHON_CMD:-python3}

# Check if DDNS command is provided as argument
if [ -z "$1" ]; then
    DDNS_CMD="$PYTHON_CMD -m ddns"
else
    DDNS_CMD="$1"
fi

echo "=== DDNS Task Management Test for Linux/Cron ==="
echo "DDNS Command: $DDNS_CMD"
echo ""

# Check if cron is available
if ! command -v crontab >/dev/null 2>&1; then
    echo "❌ crontab not available - skipping cron tests"
    exit 1
fi

# Function to check crontab and validate task existence
check_crontab() {
    expected_state=$1  # "exists" or "not_exists"
    
    echo "Checking crontab..."
    if crontab -l 2>/dev/null | grep -q "ddns\|DDNS"; then
        echo "✅ DDNS crontab entry found"
        echo "Crontab entries:"
        crontab -l 2>/dev/null | grep -i ddns || true
        if [ "$expected_state" = "not_exists" ]; then
            echo "❌ VERIFICATION FAILED: Crontab entry should not exist but was found"
            return 1
        fi
    else
        echo "ℹ️ No DDNS crontab entry found"
        if [ "$expected_state" = "exists" ]; then
            echo "❌ VERIFICATION FAILED: Crontab entry should exist but was not found"
            return 1
        fi
    fi
    return 0
}

check_ddns_status() {
    expected_status=$1  # "Yes" or "No"
    
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

# Disable systemd if available to force cron usage
if command -v systemctl >/dev/null 2>&1; then
    echo "ℹ️ Systemd detected - this test will verify cron fallback behavior"
fi

# Test Step 1: Initial state check
echo "=== Step 1: Initial state verification ==="
$DDNS_CMD task -h
$DDNS_CMD task --status
initial_status=$($DDNS_CMD task --status | grep "Installed:" | head -1 || echo "Installed: Unknown")
echo "Initial status: $initial_status"

# Check initial cron state
echo ""
echo "=== Step 2: Initial cron state verification ==="
check_crontab "not_exists" || exit 1

# Test Step 3: Install task with cron
echo ""
echo "=== Step 3: Installing DDNS task ==="
if echo "$initial_status" | grep -q "Installed.*No"; then
    echo "Installing task with 10-minute interval..."
    # Set environment to prefer cron over systemd
    export DDNS_TASK_PREFER_CRON=1
    $DDNS_CMD task --install 10 || {
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

# Check cron state after installation
echo ""
echo "=== Step 5: Cron verification after installation ==="
check_crontab "exists" || exit 1

# Verify crontab entry format
echo "Verifying crontab entry format..."
cron_entry=$(crontab -l 2>/dev/null | grep -i ddns | head -1)
if [ -n "$cron_entry" ]; then
    echo "Cron entry: $cron_entry"
    if echo "$cron_entry" | grep -q "\*/10"; then
        echo "✅ Cron entry has correct 10-minute interval"
    else
        echo "⚠️ Warning: Cron entry interval may not match expected 10 minutes"
    fi
else
    echo "❌ VERIFICATION FAILED: No cron entry found after installation"
    exit 1
fi

# Test Step 6: uninstall task
echo ""
echo "=== Step 6: Uninstalling DDNS task ==="
$DDNS_CMD task --uninstall || {
    echo "❌ VERIFICATION FAILED: Task uninstallation failed"
    exit 1
}
echo "✅ Task uninstallation command completed"

# Test Step 7: Verify deletion
echo ""
echo "=== Step 7: Verifying deletion ==="
check_ddns_status "No" || exit 1

# Final cron state verification
echo ""
echo "=== Step 8: Final cron state verification ==="
check_crontab "not_exists" || exit 1

# Test help commands availability
echo ""
echo "=== Step 9: Help commands verification ==="
if $DDNS_CMD task --help | grep -q "install\|uninstall\|enable\|disable\|status"; then
    echo "✅ Task commands found in help"
else
    echo "❌ VERIFICATION FAILED: Task commands missing from help"
    exit 1
fi

echo ""
echo "🎉 ============================================"
echo "🎉 ALL TESTS PASSED - Cron task management OK"
echo "🎉 ============================================"
echo ""

exit 0
