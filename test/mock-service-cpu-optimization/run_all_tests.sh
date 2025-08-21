#!/bin/bash

# Mock Service CPU Optimization - Test Runner
# Runs all test suites for the CPU optimization implementation

set -e

echo "================================================================"
echo "Mock Service CPU Optimization - Test Suite"
echo "================================================================"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test_suite() {
    local suite_name="$1"
    local test_dir="$2"
    local test_script="$3"
    
    echo -e "${BLUE}Running $suite_name...${NC}"
    echo "----------------------------------------"
    
    if [ -d "$test_dir" ] && [ -f "$test_dir/$test_script" ]; then
        cd "$test_dir"
        if python3 "$test_script"; then
            echo -e "${GREEN}✅ $suite_name PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ $suite_name FAILED${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        cd - > /dev/null
    else
        echo -e "${RED}❌ $suite_name - Test not found${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "Test Directory: $SCRIPT_DIR"
echo

# Run test suites
run_test_suite "01 - Idle Detection" "01_idle_detection" "test_idle_detection.py"
run_test_suite "02 - Functionality Verification" "02_functionality_verification" "test_functionality.py"
run_test_suite "03 - Performance Validation" "03_performance_validation" "test_performance.py"

# Summary
echo "================================================================"
echo "TEST SUMMARY"
echo "================================================================"
echo "Total Test Suites: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo
    echo "The mock service CPU optimization is working correctly:"
    echo "- ✅ Idle detection mechanism functions properly"
    echo "- ✅ Existing functionality remains intact"
    echo "- ✅ Performance improvements are validated"
    echo
    echo "Ready for deployment!"
    exit 0
else
    echo
    echo -e "${RED}❌ SOME TESTS FAILED!${NC}"
    echo
    echo "Please review the test output above and fix any issues"
    echo "before proceeding with deployment."
    exit 1
fi