#!/bin/bash
#
# Run all VSS array support tests
#

set -e

echo "VSS Array Support Test Suite"
echo "============================"
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Track test results
total_tests=0
passed_tests=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_dir="$2"
    local test_script="$3"
    
    echo "Running $test_name..."
    echo "----------------------------------------"
    
    if cd "$test_dir" && python3 "$test_script"; then
        echo "✅ $test_name PASSED"
        ((passed_tests++))
    else
        echo "❌ $test_name FAILED"
    fi
    
    ((total_tests++))
    echo
    cd "$SCRIPT_DIR"
}

# Run all test categories
echo "Starting VSS array support tests..."
echo

# String Array Serialization Tests
run_test "String Array Serialization" "string-array-serialization" "test_string_array_serialization.py"

# Summary
echo "==============================="
echo "Test Summary"
echo "==============================="
echo "Total tests: $total_tests"
echo "Passed: $passed_tests"
echo "Failed: $((total_tests - passed_tests))"
echo

if [ $passed_tests -eq $total_tests ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo "✅ VSS array support is working correctly"
    exit 0
else
    echo "❌ Some tests failed"
    echo "⚠️  VSS array support needs attention"
    exit 1
fi