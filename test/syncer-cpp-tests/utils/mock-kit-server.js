// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

/**
 * Mock Kit Server for testing syncer.py C++ compilation
 * This acts as the external kit server (kit.digitalauto.tech) that syncer.py connects to
 * 
 * Usage:
 * 1. Start this mock server
 * 2. Configure syncer.py with SYNCER_SERVER_URL=http://localhost:3091
 * 3. syncer.py will connect to this mock instead of real kit server
 * 4. Send compile_cpp_app commands through this mock server to syncer.py
 */

const { Server } = require('socket.io');
const http = require('http');

class MockKitServer {
    constructor(port = 3091) {
        this.port = port;
        this.server = http.createServer();
        this.io = new Server(this.server, {
            cors: {
                origin: "*",
                methods: ["GET", "POST"]
            }
        });
        this.syncerSocket = null;
        this.testResults = [];
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.io.on('connection', (socket) => {
            console.log(`🔌 Client connected: ${socket.id}`);
            
            // Listen for syncer registration
            socket.on('register_kit', (data) => {
                console.log(`📝 Kit registered: ${data.kit_id}`);
                this.syncerSocket = socket;
                socket.kit_id = data.kit_id;
            });

            // Listen for syncer responses
            socket.on('messageToKit-kitReply', (response) => {
                console.log(`📥 [${response.status || response.cmd}] ${response.result?.substring(0, 100) || 'No result'}...`);
                
                // Store test results
                this.testResults.push(response);
                
                // Emit to any test clients listening
                this.io.emit('compilation_progress', response);
                
                // Check if this is the final response for a C++ compilation
                if (response.cmd === 'compile_cpp_app' && response.isDone) {
                    console.log(`✅ C++ compilation completed with code: ${response.code}`);
                }
            });

            socket.on('disconnect', () => {
                console.log(`📴 Client disconnected: ${socket.id}`);
                if (this.syncerSocket === socket) {
                    this.syncerSocket = null;
                }
            });
        });
    }

    async start() {
        return new Promise((resolve) => {
            this.server.listen(this.port, () => {
                console.log(`🎯 Mock Kit Server running on port ${this.port}`);
                console.log(`📡 Configure syncer.py with: SYNCER_SERVER_URL=http://localhost:${this.port}`);
                resolve();
            });
        });
    }

    // Send a C++ compilation request to the connected syncer
    sendCppCompileRequest(files, appName = 'TestApp', run = true) {
        if (!this.syncerSocket) {
            throw new Error('No syncer connected');
        }

        const request = {
            cmd: 'compile_cpp_app',
            request_from: 'mock-kit-server',
            data: {
                files: files,
                app_name: appName,
                run: run
            }
        };

        console.log(`📤 Sending C++ compilation request for: ${appName}`);
        this.syncerSocket.emit('messageToKit', request);
    }

    // Wait for syncer to connect
    async waitForSyncer(timeoutMs = 30000) {
        const startTime = Date.now();
        while (!this.syncerSocket && (Date.now() - startTime) < timeoutMs) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        if (!this.syncerSocket) {
            throw new Error(`Syncer did not connect within ${timeoutMs}ms`);
        }
        
        console.log(`✅ Syncer connected: ${this.syncerSocket.kit_id}`);
        return this.syncerSocket;
    }
    
    // Wait for compilation to complete
    async waitForCompilationComplete(timeoutMs = 60000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeoutMs) {
            const lastResult = this.testResults[this.testResults.length - 1];
            if (lastResult && lastResult.cmd === 'compile_cpp_app' && lastResult.isDone) {
                return {
                    success: lastResult.code === 0,
                    results: this.testResults,
                    finalResult: lastResult
                };
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        throw new Error(`Compilation did not complete within ${timeoutMs}ms`);
    }
    
    // Get all test results
    getTestResults() {
        return [...this.testResults];
    }
    
    // Clear test results
    clearResults() {
        this.testResults = [];
    }

    stop() {
        if (this.server) {
            this.server.close();
            console.log(`🛑 Mock Kit Server stopped`);
        }
    }
}

module.exports = MockKitServer;