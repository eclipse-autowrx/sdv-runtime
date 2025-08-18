#!/usr/bin/env node

/**
 * Automated Test Suite for C++ Compilation Service
 * Designed for GitHub Actions CI/CD pipeline
 */

const io = require('socket.io-client');
const fs = require('fs');
const path = require('path');

class CppCompilationTestSuite {
    constructor(serverUrl = 'http://localhost:3090', timeout = 60000) {
        this.serverUrl = serverUrl;
        this.timeout = timeout;
        this.testResults = [];
        this.socket = null;
        this.currentTest = null;
    }

    async runAllTests() {
        console.log('🚀 Starting Automated C++ Compilation Test Suite');
        console.log(`📡 Server: ${this.serverUrl}`);
        console.log(`⏱️  Timeout: ${this.timeout}ms\n`);

        const tests = [
            { name: 'Connection Test', method: this.testConnection },
            { name: 'Basic Compilation', method: this.testBasicCompilation },
            { name: 'Multi-File Project', method: this.testMultiFileCompilation },
            { name: 'Complex Automotive', method: this.testComplexAutomotive },
            { name: 'Error Handling', method: this.testErrorHandling },
            { name: 'Performance Benchmark', method: this.testPerformance }
        ];

        let passed = 0;
        let failed = 0;

        for (const test of tests) {
            try {
                console.log(`🧪 Running: ${test.name}`);
                const result = await this.runSingleTest(test.name, test.method.bind(this));
                
                if (result.success) {
                    console.log(`✅ PASSED: ${test.name} (${result.duration}ms)`);
                    passed++;
                } else {
                    console.log(`❌ FAILED: ${test.name} - ${result.error}`);
                    failed++;
                }
                
                this.testResults.push(result);
            } catch (error) {
                console.log(`💥 ERROR: ${test.name} - ${error.message}`);
                failed++;
                this.testResults.push({
                    name: test.name,
                    success: false,
                    error: error.message,
                    duration: 0
                });
            }

            // Brief pause between tests
            await this.sleep(1000);
        }

        this.printSummary(passed, failed);
        return { passed, failed, results: this.testResults };
    }

    async runSingleTest(testName, testMethod) {
        const startTime = Date.now();
        this.currentTest = testName;

        try {
            await testMethod();
            const duration = Date.now() - startTime;
            return { name: testName, success: true, duration, error: null };
        } catch (error) {
            const duration = Date.now() - startTime;
            return { name: testName, success: false, duration, error: error.message };
        }
    }

    async testConnection() {
        return new Promise((resolve, reject) => {
            const socket = io(this.serverUrl, { timeout: 5000 });
            
            const timeoutId = setTimeout(() => {
                socket.disconnect();
                reject(new Error('Connection timeout'));
            }, 10000);

            socket.on('connect', () => {
                clearTimeout(timeoutId);
                socket.disconnect();
                resolve();
            });

            socket.on('connect_error', (error) => {
                clearTimeout(timeoutId);
                reject(new Error(`Connection failed: ${error.message}`));
            });
        });
    }

    async testBasicCompilation() {
        const code = `
#include <iostream>
int main() {
    std::cout << "CI Test: Basic compilation working!" << std::endl;
    return 0;
}`;

        return this.compileAndRun({
            'main.cpp': code
        }, 'CIBasicTest', true);
    }

    async testMultiFileCompilation() {
        const files = {
            'main.cpp': `
#include "math/Calculator.h"
#include <iostream>

int main() {
    Calculator calc;
    int result = calc.add(15, 27);
    std::cout << "CI Test: Multi-file result = " << result << std::endl;
    return result == 42 ? 0 : 1;
}`,
            'math/Calculator.h': `
#pragma once
class Calculator {
public:
    int add(int a, int b);
    int multiply(int a, int b);
};`,
            'math/Calculator.cpp': `
#include "Calculator.h"

int Calculator::add(int a, int b) {
    return a + b;
}

int Calculator::multiply(int a, int b) {
    return a * b;
}`
        };

        return this.compileAndRun(files, 'CIMultiFileTest', true);
    }

    async testComplexAutomotive() {
        const code = `
#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>

class VehicleSystem {
private:
    std::vector<double> speeds;
    double maxSpeed;

public:
    VehicleSystem(double max) : maxSpeed(max) {}
    
    void addSpeed(double speed) {
        speeds.push_back(std::min(speed, maxSpeed));
    }
    
    double getAverageSpeed() const {
        if (speeds.empty()) return 0;
        double sum = 0;
        for (double speed : speeds) sum += speed;
        return sum / speeds.size();
    }
    
    bool hasSpeedViolation() const {
        return std::any_of(speeds.begin(), speeds.end(), 
                          [this](double s) { return s > maxSpeed * 0.9; });
    }
};

int main() {
    VehicleSystem vehicle(120.0);
    
    vehicle.addSpeed(80.0);
    vehicle.addSpeed(95.0);
    vehicle.addSpeed(110.0);
    
    double avg = vehicle.getAverageSpeed();
    bool violation = vehicle.hasSpeedViolation();
    
    std::cout << "CI Test: Automotive system - Average: " << avg 
              << ", Violation: " << (violation ? "Yes" : "No") << std::endl;
    
    return (avg > 85 && avg < 100 && violation) ? 0 : 1;
}`;

        return this.compileAndRun({
            'main.cpp': code
        }, 'CIAutomotiveTest', true);
    }

    async testErrorHandling() {
        const invalidCode = `
#include <nonexistent_header.h>
int main() {
    UndefinedFunction();
    return 0;
}`;

        return new Promise((resolve, reject) => {
            const socket = io(this.serverUrl);
            let hasCompleted = false;

            const timeoutId = setTimeout(() => {
                if (!hasCompleted) {
                    socket.disconnect();
                    reject(new Error('Error handling test timeout'));
                }
            }, this.timeout);

            socket.on('connect', () => {
                socket.emit('compile_cpp', {
                    files: { 'main.cpp': invalidCode },
                    app_name: 'CIErrorTest',
                    run: false
                });
            });

            socket.on('compile_cpp_reply', (response) => {
                if (response.isDone) {
                    hasCompleted = true;
                    clearTimeout(timeoutId);
                    socket.disconnect();

                    // Should fail with non-zero exit code
                    if (response.code !== 0 || response.status.includes('failed')) {
                        resolve(); // Expected failure
                    } else {
                        reject(new Error(`Expected compilation to fail but got exit code ${response.code}`));
                    }
                }
            });

            socket.on('connect_error', (error) => {
                clearTimeout(timeoutId);
                reject(new Error(`Connection error in error handling test: ${error.message}`));
            });
        });
    }

    async testPerformance() {
        const startTime = Date.now();
        
        await this.testBasicCompilation();
        
        const duration = Date.now() - startTime;
        if (duration > 30000) { // 30 seconds max
            throw new Error(`Performance test failed: took ${duration}ms (max 30000ms)`);
        }
    }

    async compileAndRun(files, appName, shouldSucceed = true) {
        return new Promise((resolve, reject) => {
            const socket = io(this.serverUrl);
            let hasCompleted = false;
            let compilationOutput = [];
            let lastExitCode = null;

            const timeoutId = setTimeout(() => {
                if (!hasCompleted) {
                    socket.disconnect();
                    reject(new Error('Test timeout'));
                }
            }, this.timeout);

            socket.on('connect', () => {
                socket.emit('compile_cpp', {
                    files: files,
                    app_name: appName,
                    run: true
                });
            });

            socket.on('compile_cpp_reply', (response) => {
                compilationOutput.push(response);

                if (response.isDone) {
                    hasCompleted = true;
                    clearTimeout(timeoutId);
                    socket.disconnect();

                    lastExitCode = response.code;
                    
                    if (shouldSucceed && response.code === 0) {
                        resolve();
                    } else if (!shouldSucceed && response.code !== 0) {
                        resolve(); // Expected failure
                    } else {
                        const output = compilationOutput
                            .map(msg => msg.result)
                            .join('\\n')
                            .substring(0, 500);
                        reject(new Error(
                            `Compilation ${shouldSucceed ? 'failed' : 'succeeded'} unexpectedly. ` +
                            `Exit code: ${response.code}. Output: ${output}`
                        ));
                    }
                }
            });

            socket.on('connect_error', (error) => {
                clearTimeout(timeoutId);
                reject(new Error(`Connection error: ${error.message}`));
            });
        });
    }

    printSummary(passed, failed) {
        const total = passed + failed;
        const percentage = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

        console.log('\\n' + '='.repeat(60));
        console.log('📊 TEST SUITE SUMMARY');
        console.log('='.repeat(60));
        console.log(`Total Tests: ${total}`);
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${percentage}%`);
        console.log('='.repeat(60));

        if (failed > 0) {
            console.log('\\n💡 Failed Tests:');
            this.testResults
                .filter(r => !r.success)
                .forEach(r => console.log(`   • ${r.name}: ${r.error}`));
        }

        // Exit with appropriate code for CI/CD
        process.exitCode = failed > 0 ? 1 : 0;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Run if called directly
if (require.main === module) {
    const serverUrl = process.env.SDV_SERVER_URL || 'http://localhost:3090';
    const timeout = parseInt(process.env.TEST_TIMEOUT) || 60000;
    
    const testSuite = new CppCompilationTestSuite(serverUrl, timeout);
    
    testSuite.runAllTests()
        .then(results => {
            console.log(`\\n🏁 Test suite completed: ${results.passed}/${results.passed + results.failed} passed`);
        })
        .catch(error => {
            console.error('💥 Test suite crashed:', error.message);
            process.exit(1);
        });
}

module.exports = CppCompilationTestSuite;