#!/bin/bash
# macOS Task Management Test Script
# Tests DDNS task functionality on macOS systems
# Exits with non-zero status on verification failure
# Usage: test-task-macos.sh [DDNS_COMMAND]
# Examples:
#   test-task-macos.sh                       (uses default: python3 -m ddns)
#   test-task-macos.sh ddns                  (uses ddns command)
#   test-task-macos.sh ./dist/ddns           (uses binary executable)
#   test-task-macos.sh "python -m ddns"      (uses custom python command)

set -e  # Exit on any error
PYTHON_CMD=${PYTHON_CMD:-python3}

# Check if DDNS command is provided as argument
if [[ -z "$1" ]]; then
    DDNS_CMD="$PYTHON_CMD -m ddns"
else
    DDNS_CMD="$1"
fi

echo "=== DDNS Task Management Test for macOS ==="
echo "DDNS Command: $DDNS_CMD"
echo ""

# Function to check launchd services
check_launchd_service() {
    local expected_state=$1  # "exists" or "not_exists"
    
    if command -v launchctl >/dev/null 2>&1; then
        echo "Checking launchd services..."
        if launchctl list 2>/dev/null | grep -q "ddns"; then
            echo "✅ DDNS launchd service found"
            echo "Service details:"
            launchctl list | grep ddns || true
            if [[ "$expected_state" == "not_exists" ]]; then
                echo "❌ VERIFICATION FAILED: launchd service should not exist but was found"
                return 1
            fi
        else
            echo "ℹ️ No DDNS launchd service found"
            if [[ "$expected_state" == "exists" ]]; then
                echo "❌ VERIFICATION FAILED: launchd service should exist but was not found"
                return 1
            fi
        fi
    else
        echo "❌ VERIFICATION FAILED: launchctl not available on macOS"
        return 1
    fi
    return 0
}

# Function to check LaunchAgents directory
check_launch_agents() {
    local expected_state=$1  # "exists" or "not_exists"
    local user_agents_dir="$HOME/Library/LaunchAgents"
    local ddns_plist="$user_agents_dir/cc.newfuture.ddns.plist"
    
    echo "Checking LaunchAgents directory..."
    if [[ -f "$ddns_plist" ]]; then
        echo "✅ DDNS plist file found: $ddns_plist"
        echo "Plist content preview:"
        head -10 "$ddns_plist" 2>/dev/null || true
        if [[ "$expected_state" == "not_exists" ]]; then
            echo "❌ VERIFICATION FAILED: plist file should not exist but was found"
            return 1
        fi
    else
        echo "ℹ️ No DDNS plist file found in $user_agents_dir"
        if [[ "$expected_state" == "exists" ]]; then
            echo "❌ VERIFICATION FAILED: plist file should exist but was not found"
            return 1
        fi
    fi
    return 0
}

# Function to check crontab (fallback on macOS)
check_crontab() {
    local expected_state=$1  # "exists" or "not_exists"
    
    if command -v crontab >/dev/null 2>&1; then
        echo "Checking crontab (fallback scheduling)..."
        if crontab -l 2>/dev/null | grep -q "ddns\|DDNS"; then
            echo "✅ DDNS crontab entry found"
            echo "Crontab entries:"
            crontab -l 2>/dev/null | grep -i ddns || true
            if [[ "$expected_state" == "not_exists" ]]; then
                echo "❌ VERIFICATION FAILED: Crontab entry should not exist but was found"
                return 1
            fi
        else
            echo "ℹ️ No DDNS crontab entry found"
            if [[ "$expected_state" == "exists" ]]; then
                echo "❌ VERIFICATION FAILED: Crontab entry should exist but was not found"
                return 1
            fi
        fi
    else
        echo "⚠️ crontab not available"
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

# Check if we're actually on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ VERIFICATION FAILED: This script is designed for macOS (Darwin), detected: $(uname)"
    exit 1
fi

echo "✅ Confirmed running on macOS ($(sw_vers -productName) $(sw_vers -productVersion))"

# Test Step 1: Initial state check
echo ""
echo "=== Step 1: Initial state verification ==="
$DDNS_CMD task -h
$DDNS_CMD task --status
initial_status=$($DDNS_CMD task --status | grep "Installed:" | head -1 || echo "Installed: Unknown")
echo "Initial status: $initial_status"

# Check initial system state
echo ""
echo "=== Step 2: Initial system state verification ==="
check_launchd_service "not_exists" || exit 1
check_launch_agents "not_exists" || exit 1
check_crontab "not_exists" || exit 1

# Test Step 3: Install task
echo ""
echo "=== Step 3: Installing DDNS task ==="
if echo "$initial_status" | grep -q "Installed.*No"; then
    echo "Installing task with 15-minute interval..."
    $DDNS_CMD task --install 15 || {
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

# Check system state after installation
echo ""
echo "=== Step 5: System verification after installation ==="
check_launchd_service "exists" || {
    echo "ℹ️ Warning: launchd service not found (may use cron instead)"
}
check_launch_agents "exists" || {
    echo "ℹ️ Warning: LaunchAgent plist not found (may use cron instead)"
}
check_crontab "exists" || {
    echo "ℹ️ Warning: crontab entry not found (may use launchd instead)"
}

# Verify at least one scheduling method is active
if ! (launchctl list 2>/dev/null | grep -q "ddns" || crontab -l 2>/dev/null | grep -q "ddns\|DDNS"); then
    echo "❌ VERIFICATION FAILED: No scheduling system (launchd or cron) has DDNS task"
    exit 1
fi
echo "✅ At least one scheduling system has DDNS task"

# Test Step 6: Delete task
echo ""
echo "=== Step 6: Deleting DDNS task ==="
$DDNS_CMD task --delete || {
    echo "❌ VERIFICATION FAILED: Task deletion failed"
    exit 1
}
echo "✅ Task deletion command completed"

# Test Step 7: Verify deletion
echo ""
echo "=== Step 7: Verifying deletion ==="
check_ddns_status "No" || exit 1

# Final system state verification
echo ""
echo "=== Step 8: Final system state verification ==="
check_launchd_service "not_exists" || exit 1
check_launch_agents "not_exists" || exit 1
check_crontab "not_exists" || exit 1

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
echo "🍎 ============================================="
echo "🍎 ALL TESTS PASSED - macOS task management OK"
echo "🍎 ============================================="
echo ""

exit 0
