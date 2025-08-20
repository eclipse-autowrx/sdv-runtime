// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 01: Basic Hello World through syncer.py using mock kit server
const MockKitServer = require('../utils/mock-kit-server');
const { createSingleFile } = require('../utils/syncer-test-config');

const TEST_NAME = '01 Basic Hello World (via Mock Kit Server)';

const CPP_CODE = `#include <iostream>
using namespace std;

int main() {
    cout << "Hello from Syncer C++ Test via Mock Server!" << endl;
    cout << "Testing syncer.py → Kit-Manager communication" << endl;
    return 0;
}`;

const FILES = createSingleFile('main.cpp', CPP_CODE);

async function main() {
    console.log(`\n🧪 Starting: ${TEST_NAME}`);
    
    // Start mock kit server
    const mockServer = new MockKitServer(3091);
    await mockServer.start();
    
    // Wait for syncer to connect (if it's configured to connect to our mock server)
    console.log(`⏳ Waiting for syncer.py to connect...`);
    console.log(`💡 To test this, restart syncer.py with SYNCER_SERVER_URL=http://localhost:3091`);
    
    let responses = [];
    let testCompleted = false;
    
    // Listen for compilation progress
    mockServer.io.on('compilation_progress', (response) => {
        responses.push(response);
        
        if (response.request_from === 'mock-kit-server' && response.cmd === 'compile_cpp_app') {
            if (response.isDone) {
                testCompleted = true;
                const success = response.code === 0;
                const statusIcon = success ? '✅' : '❌';
                console.log(`${statusIcon} Test completed - Exit code: ${response.code}`);
                
                // Check for expected output
                const outputFound = responses.some(resp => 
                    resp.result && resp.result.includes('Hello from Syncer C++ Test via Mock Server!')
                );
                
                if (outputFound) {
                    console.log('✅ Expected output found in responses');
                } else {
                    console.log('⚠️  Expected output not found in responses');
                }
                
                console.log(`\n📊 Test Summary:`);
                console.log(`   - Total responses: ${responses.length}`);
                console.log(`   - Communication path: Mock Kit Server → syncer.py → Kit-Manager`);
                
                mockServer.stop();
                process.exit(success ? 0 : 1);
            }
        }
    });
    
    // Wait a bit for syncer to connect, then send request
    setTimeout(() => {
        try {
            mockServer.sendCppCompileRequest(FILES, 'BasicHelloMock', true);
        } catch (error) {
            console.log(`❌ Failed to send request: ${error.message}`);
            console.log(`💡 Make sure syncer.py is running and configured to connect to localhost:3091`);
            mockServer.stop();
            process.exit(1);
        }
    }, 5000);
    
    // Timeout after 45 seconds
    setTimeout(() => {
        if (!testCompleted) {
            console.log(`❌ Test timeout - no syncer connection or response`);
            mockServer.stop();
            process.exit(1);
        }
    }, 45000);
}

if (require.main === module) {
    main().catch(error => {
        console.error(`❌ Test error: ${error.message}`);
        process.exit(1);
    });
}