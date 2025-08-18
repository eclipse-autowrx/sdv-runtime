#!/bin/bash

# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

# CI/CD Test Runner for C++ Compilation Service
# Usage: ./run-tests.sh [server_url] [timeout]

set -e

SERVER_URL=${1:-"http://localhost:3090"}
TIMEOUT=${2:-60000}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Starting C++ Compilation Service Tests"
echo "📡 Server: $SERVER_URL"
echo "⏱️  Timeout: ${TIMEOUT}ms"
echo "📁 Project Root: $PROJECT_ROOT"
echo ""

# Function to check if server is ready
wait_for_server() {
    echo "⏳ Waiting for server to be ready..."
    local max_attempts=30
    local attempt=1
    local port=$(echo "$SERVER_URL" | sed 's/.*://')
    
    while [ $attempt -le $max_attempts ]; do
        # Check if port is open (WebSocket server)
        if nc -z localhost "$port" 2>/dev/null; then
            echo "✅ Server is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts: Still waiting..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ Server failed to start within $(($max_attempts * 2)) seconds"
    return 1
}

# Function to run a test with timeout
run_test_with_timeout() {
    local test_name="$1"
    local test_script="$2"
    local test_timeout="${3:-30}"
    
    echo "🧪 Running: $test_name"
    
    if timeout "${test_timeout}s" node "$test_script"; then
        echo "✅ PASSED: $test_name"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo "⏰ TIMEOUT: $test_name (${test_timeout}s)"
        else
            echo "❌ FAILED: $test_name (exit code: $exit_code)"
        fi
        return $exit_code
    fi
}

# Change to project root
cd "$PROJECT_ROOT"

# Check if server is running (for CI/CD, container should already be started)
if ! wait_for_server; then
    echo "💡 If running locally, start the container first:"
    echo "   docker run -d -p 3090:3090 --name sdv-runtime-container sdv-runtime-production:latest"
    exit 1
fi

# Initialize test counters
passed=0
failed=0
total=0

echo ""
echo "🎯 Running Test Suite"
echo "====================="

# Test 1: Automated Test Suite
echo ""
total=$((total + 1))
if SDV_SERVER_URL="$SERVER_URL" TEST_TIMEOUT="$TIMEOUT" node "$SCRIPT_DIR/automated-test-suite.js"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# Test 2: Connection Test
echo ""
total=$((total + 1))
if run_test_with_timeout "Connection Test" "$PROJECT_ROOT/test/scripts/connection-test.js" 15; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# Test 3: Basic Compilation
echo ""
total=$((total + 1))
if run_test_with_timeout "Basic Compilation" "$PROJECT_ROOT/test/scripts/basic-test.js" 30; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# Test 4: Multi-file Test
echo ""
total=$((total + 1))
if run_test_with_timeout "Multi-file Compilation" "$PROJECT_ROOT/test/02-multi-file/test-multifile.js" 90; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# Test 5: Complex Automotive
echo ""
total=$((total + 1))
if run_test_with_timeout "Complex Automotive" "$PROJECT_ROOT/test/03-complex/test-complex.js" 90; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# Summary
echo ""
echo "📊 TEST RESULTS SUMMARY"
echo "======================="
echo "Total Tests: $total"
echo "✅ Passed: $passed"
echo "❌ Failed: $failed"

if [ -d "$PROJECT_ROOT/docker-output" ] && [ -n "$(ls -A "$PROJECT_ROOT/docker-output" 2>/dev/null)" ]; then
    echo "📦 Executables Generated: ✅"
    echo "   $(ls -1 "$PROJECT_ROOT/docker-output" | wc -l) files in docker-output/"
else
    echo "📦 Executables Generated: ❌"
    failed=$((failed + 1))
fi

success_rate=$(echo "scale=1; $passed * 100 / $total" | bc -l 2>/dev/null || echo "0")
echo "📈 Success Rate: ${success_rate}%"
echo "======================="

# Exit with appropriate code
if [ $failed -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    exit 0
else
    echo "💥 $failed TEST(S) FAILED"
    exit 1
fi