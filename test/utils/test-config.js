// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Shared test configuration and utilities
const io = require('socket.io-client');

class TestRunner {
    constructor() {
        this.socket = null;
        this.startTime = null;
    }

    async runTest(config) {
        const {
            testName,
            files,
            appName,
            run = true,
            timeout = 30000,
            expectedOutput = null,
            shouldFail = false
        } = config;

        console.log(`${testName}`);
        console.log('-'.repeat(60));
        
        this.socket = io('http://localhost:3090');
        this.startTime = Date.now();

        // Set up event handlers
        this.setupEventHandlers(testName, expectedOutput, shouldFail);

        // Set up timeout
        setTimeout(() => {
            console.log('\nTest timeout');
            this.cleanup();
        }, timeout);

        // Wait for connection
        this.socket.on('connect', () => {
            console.log('Connected to SDV Runtime\n');
            
            // Show file structure
            this.showFileStructure(files);
            
            console.log('\nStarting compilation...\n');
            
            // Send compilation request
            this.socket.emit('compile_cpp', {
                files: files,
                app_name: appName,
                run: run
            });
        });

        this.socket.on('connect_error', (error) => {
            console.log('Connection failed:', error.message);
            console.log('Make sure SDV Runtime container is running:');
            console.log('   docker logs sdv-runtime-test | grep "Kit Manager"');
            process.exit(1);
        });
    }

    showFileStructure(files) {
        console.log('File Structure:');
        
        if (Array.isArray(files)) {
            console.log('Format: Tree Structure');
            this.printTreeStructure(files, '');
        } else if (typeof files === 'object' && files.type) {
            console.log('Format: Tree Structure (Single Object)');
            this.printTreeStructure([files], '');
        } else {
            console.log('Format: Flat Structure');
            Object.keys(files).forEach(filename => {
                const lines = files[filename].split('\n').length;
                console.log(`   ${filename} (${lines} lines)`);
            });
        }
    }

    printTreeStructure(items, indent) {
        items.forEach(item => {
            if (item.type === 'file') {
                const lines = item.content ? item.content.split('\n').length : 0;
                console.log(`${indent}   ${item.name} (${lines} lines)`);
            } else if (item.type === 'folder') {
                console.log(`${indent}   ${item.name}/`);
                if (item.items) {
                    this.printTreeStructure(item.items, indent + '  ');
                }
            }
        });
    }

    setupEventHandlers(testName, expectedOutput, shouldFail) {
        let buildOutput = [];
        let runOutput = [];
        let fileCount = 0;
        let hasErrors = false;

        this.socket.on('compile_cpp_reply', (response) => {
            if (response.status === 'compile-start') {
                console.log('Compilation started');
            } else if (response.status === 'file-written') {
                fileCount++;
                console.log(`Written: ${response.result.trim()}`);
            } else if (response.status.includes('configure')) {
                console.log(`[Configure] ${response.result.trim()}`);
                if (response.status.includes('stderr')) {
                    buildOutput.push(response.result);
                }
            } else if (response.status.includes('build')) {
                console.log(`[Build] ${response.result.trim()}`);
                buildOutput.push(response.result);
            } else if (response.status.includes('run')) {
                if (response.status === 'run-stdout') {
                    console.log(`[Run] ${response.result.trim()}`);
                    runOutput.push(response.result.trim());
                } else {
                    console.log(`[Run Status] ${response.result.trim()}`);
                }
            } else if (response.status.includes('failed') || response.status.includes('err')) {
                console.log(`[Error] ${response.result.trim()}`);
                hasErrors = true;
            }

            // Handle completion
            if (response.isDone) {
                const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(1);
                console.log(`\nTotal time: ${elapsed}s`);
                
                this.handleTestCompletion(
                    testName, 
                    response.code, 
                    hasErrors, 
                    shouldFail, 
                    runOutput, 
                    expectedOutput,
                    fileCount
                );
            }
        });
    }

    handleTestCompletion(testName, code, hasErrors, shouldFail, runOutput, expectedOutput, fileCount) {
        console.log('\n' + '='.repeat(60));
        
        if (shouldFail) {
            if (code !== 0 || hasErrors) {
                console.log('[SUCCESS] Test correctly failed as expected');
                console.log(`Error handling test passed`);
            } else {
                console.log('[FAILED] Test should have failed but succeeded');
            }
        } else {
            if (code === 0 && !hasErrors) {
                console.log('[SUCCESS] Compilation and execution completed!');
                console.log(`Files processed: ${fileCount}`);
                console.log(`Exit code: ${code}`);
                
                // Validate expected output if provided
                if (expectedOutput) {
                    const actualOutput = runOutput.join(' ').toLowerCase();
                    const expected = expectedOutput.toLowerCase();
                    
                    if (actualOutput.includes(expected)) {
                        console.log('[PASS] Output validation passed');
                    } else {
                        console.log('[WARN] Output validation failed');
                        console.log(`   Expected: "${expected}"`);
                        console.log(`   Got: "${actualOutput}"`);
                    }
                }
                
                console.log('[INFO] Binary saved to output/ directory');
            } else {
                console.log('[FAILED] Compilation or execution error');
                console.log(`Exit code: ${code}`);
                console.log(`Had errors: ${hasErrors}`);
            }
        }
        
        console.log('='.repeat(60));
        this.cleanup();
    }

    cleanup() {
        if (this.socket) {
            this.socket.disconnect();
        }
        // Small delay to ensure clean exit
        setTimeout(() => process.exit(0), 100);
    }
}

// Export singleton instance
module.exports = {
    runTest: (config) => {
        const runner = new TestRunner();
        runner.runTest(config);
    }
};