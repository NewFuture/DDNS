#!/bin/sh
# OpenWRT Installation and Task Management Test Script
# Comprehensive test for DDNS installation on OpenWRT systems
# Tests installation path, binary execution, and cron task management
# Usage: test-openwrt-install.sh [INSTALL_SCRIPT_PATH]

set -e  # Exit on any error

echo "=== OpenWRT DDNS Installation and Task Test ==="
echo ""

# Use provided install script or default to docs/public/install.sh
INSTALL_SCRIPT="${1:-./install.sh}"
if [ ! -f "$INSTALL_SCRIPT" ]; then
    echo "❌ Install script not found: $INSTALL_SCRIPT"
    exit 1
fi
echo "Using install script: $INSTALL_SCRIPT"
echo ""

# Function to print test step
print_step() {
    echo ""
    echo "=== $1 ==="
}

# Function to verify command exists
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "✅ $1 is available"
        return 0
    else
        echo "❌ $1 is not available"
        return 1
    fi
}

# Function to check crontab for DDNS entries
check_crontab_entry() {
    if crontab -l 2>/dev/null | grep -q "ddns\|DDNS"; then
        echo "✅ DDNS crontab entry found:"
        crontab -l 2>/dev/null | grep -i ddns || true
        return 0
    else
        echo "ℹ️ No DDNS crontab entry found"
        return 1
    fi
}

# Test Step 1: System information
print_step "Step 1: System Information"
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Kernel: $(uname -r)"

# Check for musl (OpenWRT typically uses musl)
if ldd --version 2>&1 | grep -i musl > /dev/null; then
    echo "✅ Detected musl libc (typical for OpenWRT)"
elif ldd /bin/sh 2>&1 | grep -i musl > /dev/null; then
    echo "✅ Detected musl libc via /bin/sh (typical for OpenWRT)"
else
    echo "⚠️ Warning: musl not detected, may not be OpenWRT"
fi

# Check available tools
check_command wget || check_command curl || {
    echo "❌ Neither wget nor curl available"
    exit 1
}
check_command crontab || {
    echo "❌ crontab not available"
    exit 1
}

# Test Step 2: Test install script help
print_step "Step 2: Install Script Help"
sh "$INSTALL_SCRIPT" --help || {
    echo "❌ Install script help failed"
    exit 1
}
echo "✅ Install script help succeeded"

# Test Step 3: Install DDNS to default path
print_step "Step 3: Install DDNS (default path: /usr/local/bin)"
sh "$INSTALL_SCRIPT" || {
    echo "❌ DDNS installation failed"
    exit 1
}
echo "✅ DDNS installation succeeded"

# Test Step 4: Verify installation path
print_step "Step 4: Verify Installation Path"
EXPECTED_PATH="/usr/local/bin/ddns"
if [ -f "$EXPECTED_PATH" ]; then
    echo "✅ DDNS binary found at expected path: $EXPECTED_PATH"
else
    echo "❌ DDNS binary not found at expected path: $EXPECTED_PATH"
    echo "Searching for ddns binary..."
    find /usr -name "ddns" 2>/dev/null || echo "Not found in /usr"
    exit 1
fi

if [ -x "$EXPECTED_PATH" ]; then
    echo "✅ DDNS binary is executable"
else
    echo "❌ DDNS binary is not executable"
    ls -l "$EXPECTED_PATH"
    exit 1
fi

# Test Step 5: Check PATH
print_step "Step 5: Check PATH Configuration"
if echo "$PATH" | grep -q "/usr/local/bin"; then
    echo "✅ /usr/local/bin is in PATH"
else
    echo "⚠️ Warning: /usr/local/bin is not in PATH"
    echo "Current PATH: $PATH"
fi

# Test Step 6: Run DDNS version check
print_step "Step 6: DDNS Version Check"
DDNS_VERSION=$(ddns --version 2>&1 || echo "FAILED")
if [ "$DDNS_VERSION" = "FAILED" ]; then
    echo "❌ ddns --version failed"
    exit 1
fi
echo "✅ DDNS version: $DDNS_VERSION"

# Test Step 7: Run DDNS help
print_step "Step 7: DDNS Help Command"
if ddns --help >/dev/null 2>&1; then
    echo "✅ ddns --help succeeded"
else
    echo "❌ ddns --help failed"
    exit 1
fi

# Test Step 8: Test task subcommand
print_step "Step 8: Task Subcommand Help"
if ddns task --help | grep -q "install\|uninstall\|enable\|disable\|status"; then
    echo "✅ Task subcommand available with expected options"
else
    echo "❌ Task subcommand missing expected options"
    exit 1
fi

# Test Step 9: Check initial task status
print_step "Step 9: Initial Task Status"
ddns task --status || {
    echo "❌ Task status check failed"
    exit 1
}
echo "✅ Task status check succeeded"

# Verify no task is installed initially
initial_status=$(ddns task --status 2>&1 | grep "Installed:" | head -1 || echo "Installed: Unknown")
echo "Initial status: $initial_status"

# Check initial crontab state
echo ""
echo "Checking initial crontab state..."
if check_crontab_entry; then
    echo "⚠️ Warning: DDNS crontab entry exists before installation"
    echo "Cleaning up..."
    ddns task --uninstall 2>/dev/null || true
fi

# Test Step 10: Install scheduled task
print_step "Step 10: Install Scheduled Task (5-minute interval)"
if echo "$initial_status" | grep -q "Installed.*No"; then
    ddns task --install 5 || {
        echo "❌ Task installation failed"
        exit 1
    }
    echo "✅ Task installation succeeded"
else
    echo "Task already installed, reinstalling..."
    ddns task --uninstall 2>/dev/null || true
    ddns task --install 5 || {
        echo "❌ Task installation failed"
        exit 1
    }
    echo "✅ Task installation succeeded"
fi

# Test Step 11: Verify task installation
print_step "Step 11: Verify Task Installation"
installed_status=$(ddns task --status 2>&1 | grep "Installed:" | head -1 || echo "Installed: Unknown")
echo "Installed status: $installed_status"

if echo "$installed_status" | grep -q "Installed.*Yes"; then
    echo "✅ Task is installed"
else
    echo "❌ Task installation verification failed"
    echo "Status output:"
    ddns task --status
    exit 1
fi

# Test Step 12: Verify crontab entry
print_step "Step 12: Verify Crontab Entry"
if ! check_crontab_entry; then
    echo "❌ DDNS crontab entry not found after installation"
    echo "Full crontab:"
    crontab -l 2>/dev/null || echo "Empty crontab"
    exit 1
fi

# Verify interval in crontab
cron_entry=$(crontab -l 2>/dev/null | grep -i ddns | head -1)
if echo "$cron_entry" | grep -q "\*/5"; then
    echo "✅ Crontab entry has correct 5-minute interval"
else
    echo "⚠️ Warning: Crontab entry interval may not match expected 5 minutes"
    echo "Cron entry: $cron_entry"
fi

# Verify crontab entry contains path to ddns
if echo "$cron_entry" | grep -q "/usr/local/bin/ddns\|ddns"; then
    echo "✅ Crontab entry contains ddns command"
else
    echo "❌ Crontab entry does not contain ddns command"
    echo "Cron entry: $cron_entry"
    exit 1
fi

# Test Step 13: Disable task
print_step "Step 13: Disable Scheduled Task"
ddns task --disable || {
    echo "❌ Task disable failed"
    exit 1
}
echo "✅ Task disable succeeded"

# Verify disabled state
disabled_status=$(ddns task --status 2>&1 | grep "Enabled:" | head -1 || echo "Enabled: Unknown")
echo "Disabled status: $disabled_status"

if echo "$disabled_status" | grep -q "Enabled.*False\|Enabled.*No"; then
    echo "✅ Task is disabled"
else
    echo "⚠️ Warning: Task disable verification unclear"
    echo "Status output:"
    ddns task --status
fi

# Test Step 14: Enable task
print_step "Step 14: Enable Scheduled Task"
ddns task --enable || {
    echo "❌ Task enable failed"
    exit 1
}
echo "✅ Task enable succeeded"

# Verify enabled state
enabled_status=$(ddns task --status 2>&1 | grep "Enabled:" | head -1 || echo "Enabled: Unknown")
echo "Enabled status: $enabled_status"

if echo "$enabled_status" | grep -q "Enabled.*True\|Enabled.*Yes"; then
    echo "✅ Task is enabled"
else
    echo "⚠️ Warning: Task enable verification unclear"
    echo "Status output:"
    ddns task --status
fi

# Test Step 15: Uninstall task
print_step "Step 15: Uninstall Scheduled Task"
ddns task --uninstall || {
    echo "❌ Task uninstallation failed"
    exit 1
}
echo "✅ Task uninstallation succeeded"

# Test Step 16: Verify task removal
print_step "Step 16: Verify Task Removal"
final_status=$(ddns task --status 2>&1 | grep "Installed:" | head -1 || echo "Installed: Unknown")
echo "Final status: $final_status"

if echo "$final_status" | grep -q "Installed.*No"; then
    echo "✅ Task is uninstalled"
else
    echo "❌ Task uninstallation verification failed"
    echo "Status output:"
    ddns task --status
    exit 1
fi

# Verify crontab is clean
echo ""
echo "Verifying crontab cleanup..."
if check_crontab_entry; then
    echo "❌ DDNS crontab entry still exists after uninstallation"
    exit 1
else
    echo "✅ Crontab is clean"
fi

# Test Step 17: Test uninstall script
print_step "Step 17: Uninstall DDNS"
sh "$INSTALL_SCRIPT" --uninstall || {
    echo "❌ DDNS uninstallation failed"
    exit 1
}
echo "✅ DDNS uninstallation succeeded"

# Verify binary is removed
if [ -f "$EXPECTED_PATH" ]; then
    echo "❌ DDNS binary still exists after uninstallation: $EXPECTED_PATH"
    exit 1
else
    echo "✅ DDNS binary removed successfully"
fi

# Test Step 18: Reinstall for final verification
print_step "Step 18: Final Installation Test"
sh "$INSTALL_SCRIPT" || {
    echo "❌ Final DDNS installation failed"
    exit 1
}
echo "✅ Final DDNS installation succeeded"

# Final verification
if [ -x "$EXPECTED_PATH" ]; then
    echo "✅ DDNS binary is present and executable"
    echo "Version: $(ddns --version 2>&1)"
else
    echo "❌ Final installation verification failed"
    exit 1
fi

# Summary
echo ""
echo "🎉 =============================================="
echo "🎉 ALL OPENWRT TESTS PASSED"
echo "🎉 =============================================="
echo ""
echo "Summary:"
echo "  ✅ Install script works correctly"
echo "  ✅ Installation path is correct (/usr/local/bin/ddns)"
echo "  ✅ Binary is executable and functional"
echo "  ✅ Scheduled tasks can be installed"
echo "  ✅ Cron integration works correctly"
echo "  ✅ Task enable/disable functions properly"
echo "  ✅ Task uninstallation works"
echo "  ✅ Binary uninstallation works"
echo ""

exit 0
