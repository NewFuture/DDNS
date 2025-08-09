#!/bin/bash
#
# Test script for install.sh
#

set -e

TEST_DIR="/tmp/ddns_install_test"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/install.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

print_test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS:${NC} $2"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL:${NC} $2"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Clean up test directory
cleanup() {
    rm -rf "$TEST_DIR"
}

# Test 1: Help function
test_help() {
    echo "Testing help function..."
    if "$INSTALL_SCRIPT" --help >/dev/null 2>&1; then
        print_test_result 0 "Help function works"
    else
        print_test_result 1 "Help function failed"
    fi
}

# Test 2: Version detection
test_version_detection() {
    echo "Testing version detection..."
    # Test that we can fetch version info (without actually installing)
    # We'll create a mock test by checking the script logic
    
    # Check if script can detect OS and arch without errors
    if bash -c 'source '"$INSTALL_SCRIPT"'; check_os; detect_arch; detect_libc' >/dev/null 2>&1; then
        print_test_result 0 "System detection works"
    else
        print_test_result 1 "System detection failed"
    fi
}

# Test 3: Download tool detection
test_download_tool() {
    echo "Testing download tool detection..."
    if bash -c 'source '"$INSTALL_SCRIPT"'; check_download_tool' >/dev/null 2>&1; then
        print_test_result 0 "Download tool detection works"
    else
        print_test_result 1 "Download tool detection failed"
    fi
}

# Test 4: Actual installation
test_installation() {
    echo "Testing actual installation..."
    cleanup
    mkdir -p "$TEST_DIR"
    
    if "$INSTALL_SCRIPT" latest --install-dir "$TEST_DIR" >/dev/null 2>&1; then
        if [ -f "$TEST_DIR/ddns" ] && [ -x "$TEST_DIR/ddns" ]; then
            print_test_result 0 "Installation successful"
        else
            print_test_result 1 "Installation completed but binary not executable"
        fi
    else
        print_test_result 1 "Installation failed"
    fi
}

# Test 5: Force reinstallation
test_force_install() {
    echo "Testing force reinstallation..."
    
    if "$INSTALL_SCRIPT" latest --install-dir "$TEST_DIR" --force >/dev/null 2>&1; then
        print_test_result 0 "Force reinstallation works"
    else
        print_test_result 1 "Force reinstallation failed"
    fi
}

# Main test runner
main() {
    echo "Running install.sh tests..."
    echo "============================"
    
    test_help
    test_version_detection  
    test_download_tool
    test_installation
    test_force_install
    
    cleanup
    
    echo "============================"
    echo "Test Results:"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

main "$@"