#!/usr/bin/env node
// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test Suite Runner for SDV Runtime C++ Compilation

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Test configuration - All tests use Tree Structure Format
const TESTS = [
    { id: '01-hello-world', category: 'basic', timeout: 30 },
    { id: '02-tree-format', category: 'basic', timeout: 30 },
    { id: '03-multi-file-tree', category: 'basic', timeout: 40 },
    { id: '06-automotive-basic', category: 'advanced', timeout: 35 },
    { id: '08-stl-containers', category: 'advanced', timeout: 45 },
    { id: '09-error-handling', category: 'edge', timeout: 25 }
];

// Parse command line arguments
const args = process.argv.slice(2);
const categoryFilter = args.find(arg => arg.startsWith('--category='))?.split('=')[1];
const singleTest = args.find(arg => !arg.startsWith('--'));

class TestSuiteRunner {
    constructor() {
        this.results = [];
        this.startTime = Date.now();
    }

    async run() {
        console.log('🧪 SDV Runtime C++ Compilation Test Suite');
        console.log('═'.repeat(60));
        
        // Determine which tests to run
        let testsToRun = TESTS;
        
        if (singleTest) {
            testsToRun = TESTS.filter(t => t.id === singleTest);
            if (testsToRun.length === 0) {
                console.log(`❌ Test '${singleTest}' not found`);
                console.log('Available tests:', TESTS.map(t => t.id).join(', '));
                process.exit(1);
            }
        } else if (categoryFilter) {
            testsToRun = TESTS.filter(t => t.category === categoryFilter);
            if (testsToRun.length === 0) {
                console.log(`❌ No tests found for category '${categoryFilter}'`);
                console.log('Available categories: basic, advanced, edge');
                process.exit(1);
            }
        }

        console.log(`📋 Running ${testsToRun.length} tests`);
        if (categoryFilter) console.log(`📂 Category filter: ${categoryFilter}`);
        console.log('');

        // Check prerequisites
        await this.checkPrerequisites();

        // Run tests sequentially
        for (const test of testsToRun) {
            await this.runTest(test);
        }

        // Show summary
        this.showSummary();
    }

    async checkPrerequisites() {
        console.log('🔍 Checking prerequisites...');
        
        // Check if socket.io-client is installed
        try {
            require.resolve('socket.io-client');
            console.log('✅ socket.io-client found');
        } catch (e) {
            console.log('❌ socket.io-client not found');
            console.log('   Run: npm install socket.io-client');
            process.exit(1);
        }

        // Check if container is running (simple port check)
        const net = require('net');
        const isPortOpen = await new Promise((resolve) => {
            const socket = new net.Socket();
            socket.setTimeout(2000);
            socket.on('connect', () => {
                socket.destroy();
                resolve(true);
            });
            socket.on('timeout', () => {
                socket.destroy();
                resolve(false);
            });
            socket.on('error', () => {
                resolve(false);
            });
            socket.connect(3090, 'localhost');
        });

        if (isPortOpen) {
            console.log('✅ SDV Runtime container responding on port 3090');
        } else {
            console.log('❌ SDV Runtime container not accessible on port 3090');
            console.log('   Start container with:');
            console.log('   docker run -d --name sdv-runtime-test --user root \\');
            console.log('     -p 3090:3090 -p 55555:55555 \\');
            console.log('     -v "$(pwd)/output:/home/dev/data/output:rw" \\');
            console.log('     sdv-runtime-production:latest');
            process.exit(1);
        }

        console.log('');
    }

    async runTest(test) {
        const testDir = path.join(__dirname, test.id);
        const testScript = path.join(testDir, 'test.js');

        // Check if test exists
        if (!fs.existsSync(testScript)) {
            this.results.push({
                id: test.id,
                status: 'SKIP',
                message: 'Test file not found',
                duration: 0
            });
            console.log(`⏭️  SKIP: ${test.id} (test file not found)`);
            return;
        }

        console.log(`🏃 Running: ${test.id}`);
        const startTime = Date.now();

        try {
            const result = await this.executeTest(testScript, test.timeout * 1000);
            const duration = Date.now() - startTime;
            
            if (result.code === 0) {
                this.results.push({
                    id: test.id,
                    status: 'PASS',
                    message: 'Test completed successfully',
                    duration: duration
                });
                console.log(`✅ PASS: ${test.id} (${(duration/1000).toFixed(1)}s)`);
            } else {
                this.results.push({
                    id: test.id,
                    status: 'FAIL',
                    message: `Exit code: ${result.code}`,
                    duration: duration
                });
                console.log(`❌ FAIL: ${test.id} (exit code: ${result.code})`);
            }
        } catch (error) {
            const duration = Date.now() - startTime;
            this.results.push({
                id: test.id,
                status: 'ERROR',
                message: error.message,
                duration: duration
            });
            console.log(`💥 ERROR: ${test.id} (${error.message})`);
        }

        console.log(''); // Separator between tests
    }

    executeTest(scriptPath, timeout) {
        return new Promise((resolve, reject) => {
            const child = spawn('node', [scriptPath], {
                cwd: path.dirname(scriptPath),
                stdio: 'pipe'
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                resolve({ code, stdout, stderr });
            });

            child.on('error', (error) => {
                reject(error);
            });

            // Set timeout
            const timer = setTimeout(() => {
                child.kill('SIGTERM');
                reject(new Error('Test timeout'));
            }, timeout);

            child.on('close', () => {
                clearTimeout(timer);
            });
        });
    }

    showSummary() {
        const totalTime = ((Date.now() - this.startTime) / 1000).toFixed(1);
        
        console.log('📊 Test Suite Summary');
        console.log('═'.repeat(60));
        
        const passed = this.results.filter(r => r.status === 'PASS').length;
        const failed = this.results.filter(r => r.status === 'FAIL').length;
        const errors = this.results.filter(r => r.status === 'ERROR').length;
        const skipped = this.results.filter(r => r.status === 'SKIP').length;
        
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`💥 Errors: ${errors}`);
        console.log(`⏭️  Skipped: ${skipped}`);
        console.log(`⏱️  Total time: ${totalTime}s`);
        
        console.log('\\nDetailed Results:');
        this.results.forEach(result => {
            const duration = (result.duration / 1000).toFixed(1);
            console.log(`  ${this.getStatusIcon(result.status)} ${result.id.padEnd(20)} ${duration.padStart(6)}s  ${result.message}`);
        });
        
        console.log('');
        
        if (failed > 0 || errors > 0) {
            console.log('❌ Some tests failed. Check the output above for details.');
            process.exit(1);
        } else {
            console.log('🎉 All tests passed successfully!');
            process.exit(0);
        }
    }

    getStatusIcon(status) {
        switch (status) {
            case 'PASS': return '✅';
            case 'FAIL': return '❌';
            case 'ERROR': return '💥';
            case 'SKIP': return '⏭️ ';
            default: return '❓';
        }
    }
}

// Show usage if needed
if (args.includes('--help') || args.includes('-h')) {
    console.log('SDV Runtime C++ Test Suite Runner');
    console.log('');
    console.log('Usage:');
    console.log('  node run-all-tests.js                    # Run all tests');
    console.log('  node run-all-tests.js --category=basic   # Run basic tests only');
    console.log('  node run-all-tests.js --category=advanced # Run advanced tests only');
    console.log('  node run-all-tests.js --category=edge    # Run edge case tests only');
    console.log('  node run-all-tests.js 01-hello-world     # Run specific test');
    console.log('  node run-all-tests.js --help             # Show this help');
    console.log('');
    console.log('Available tests:');
    TESTS.forEach(test => {
        console.log(`  ${test.id.padEnd(20)} (${test.category})`);
    });
    process.exit(0);
}

// Run the test suite
const runner = new TestSuiteRunner();
runner.run().catch(error => {
    console.error('Fatal error:', error.message);
    process.exit(1);
});