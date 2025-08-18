// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

const io = require('socket.io-client');

// Example showing complete frontend integration pattern
class CppCompilationClient {
    constructor(url = 'http://localhost:3090') {
        this.socket = io(url);
        this.isCompiling = false;
        this.output = [];
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('✅ Connected to SDV Runtime');
        });

        this.socket.on('compile_cpp_reply', (response) => {
            this.handleCompilationResponse(response);
        });

        this.socket.on('connect_error', (error) => {
            console.log('❌ Connection error:', error.message);
        });
    }

    handleCompilationResponse(response) {
        // Add to output log
        this.output.push({
            timestamp: new Date().toISOString(),
            status: response.status,
            message: response.result.trim(),
            phase: this.getPhase(response.status),
            isError: this.isError(response.status)
        });

        // Log to console (in real frontend, update UI here)
        const icon = this.getStatusIcon(response.status);
        console.log(`${icon} [${response.status}] ${response.result.trim()}`);

        // Handle completion
        if (response.isDone) {
            this.isCompiling = false;
            this.onCompilationComplete(response.code);
        }
    }

    getPhase(status) {
        if (status.includes('configure')) return 'configure';
        if (status.includes('build')) return 'build';
        if (status.includes('run')) return 'run';
        return 'prepare';
    }

    isError(status) {
        return status.includes('failed') || status.includes('err');
    }

    getStatusIcon(status) {
        if (status.includes('failed') || status.includes('err')) return '❌';
        if (status.includes('run')) return '🚀';
        if (status.includes('build')) return '🔨';
        if (status.includes('configure')) return '⚙️';
        return 'ℹ️';
    }

    compileCode(files, appName = 'TestApp', run = true) {
        if (this.isCompiling) {
            console.log('⚠️  Compilation already in progress');
            return;
        }

        this.isCompiling = true;
        this.output = [];
        
        console.log(`🔨 Starting compilation of ${appName}...`);
        
        this.socket.emit('compile_cpp', {
            files: files,
            app_name: appName,
            run: run
        });
    }

    onCompilationComplete(exitCode) {
        if (exitCode === 0) {
            console.log('\n🎉 Compilation and execution successful!');
        } else {
            console.log(`\n❌ Compilation failed with exit code: ${exitCode}`);
        }
        
        console.log(`📊 Total messages: ${this.output.length}`);
        
        // In real frontend, you might:
        // - Update state management (Redux/Zustand)
        // - Show notifications
        // - Update progress bars
        // - Enable/disable UI elements
    }

    getCompilationLog() {
        return this.output;
    }

    disconnect() {
        this.socket.disconnect();
    }
}

// Example usage
const client = new CppCompilationClient();

const sampleCode = {
    'main.cpp': `
#include <iostream>
#include <vector>

int main() {
    std::cout << "Frontend Integration Example" << std::endl;
    
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    int sum = 0;
    
    for (int num : numbers) {
        sum += num;
    }
    
    std::cout << "Sum: " << sum << std::endl;
    return 0;
}
`
};

// Wait a moment for connection, then compile
setTimeout(() => {
    client.compileCode(sampleCode, 'FrontendExample', true);
}, 1000);

// Cleanup after 30 seconds
setTimeout(() => {
    console.log('\n🔄 Frontend example completed');
    client.disconnect();
}, 30000);