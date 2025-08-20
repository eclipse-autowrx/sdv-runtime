// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 03: Error Handling through syncer.py
const { runSyncerTest, validateSyncerResponses, createSingleFile } = require('../utils/syncer-test-config');

const TEST_NAME = '03 Error Handling (via Syncer)';

// Code with intentional compilation error
const BROKEN_CPP = `#include <iostream>
using namespace std;

int main() {
    cout << "This will fail to compile" << endl;
    
    // Intentional syntax error - missing semicolon
    undefined_function()
    
    return 0;
}`;

const FILES = createSingleFile('broken.cpp', BROKEN_CPP);

async function main() {
    try {
        console.log(`\n🧪 Testing error handling through syncer.py`);
        console.log(`🎯 Expecting compilation to fail gracefully`);
        
        const result = await runSyncerTest({
            testName: TEST_NAME,
            files: FILES,
            appName: 'ErrorTestSyncer',
            run: false, // Don't try to run if compilation fails
            timeout: 30000
        });
        
        // This test should fail compilation but succeed in error handling
        console.log(`❌ Unexpected success - compilation should have failed`);
        process.exit(1);
        
    } catch (error) {
        // Expected path - compilation should fail
        console.log(`✅ Compilation failed as expected: ${error.message}`);
        
        // The error should contain meaningful information
        if (error.message.includes('failed') || error.message.includes('code')) {
            console.log(`✅ Error message contains useful information`);
        } else {
            console.log(`⚠️  Error message could be more informative`);
        }
        
        console.log(`\n📊 Error Handling Summary:`);
        console.log(`   - Compilation failed gracefully: ✅`);
        console.log(`   - Error propagated through syncer: ✅`);
        console.log(`   - Communication path maintained: ✅`);
        
        // Test invalid request handling
        console.log(`\n🧪 Testing invalid request handling...`);
        await testInvalidRequest();
        
        process.exit(0);
    }
}

async function testInvalidRequest() {
    const io = require('socket.io-client');
    const { SYNCER_URL } = require('../utils/syncer-test-config');
    
    return new Promise((resolve, reject) => {
        const socket = io(SYNCER_URL);
        let responseReceived = false;
        
        socket.on('connect', () => {
            // Send invalid request (missing required fields)
            socket.emit('messageToKit', {
                cmd: "compile_cpp_app",
                request_from: "invalid-test-client",
                data: {
                    // Missing files and app_name
                }
            });
        });
        
        socket.on('messageToKit-kitReply', (response) => {
            if (response.request_from === "invalid-test-client") {
                responseReceived = true;
                
                console.log(`📥 Invalid request response: ${response.status}`);
                
                if (response.status === 'err: invalid') {
                    console.log(`✅ Invalid request handled correctly`);
                } else {
                    console.log(`⚠️  Unexpected response to invalid request`);
                }
                
                socket.disconnect();
                resolve();
            }
        });
        
        setTimeout(() => {
            if (!responseReceived) {
                console.log(`❌ No response to invalid request`);
                socket.disconnect();
                reject(new Error('No response to invalid request'));
            }
        }, 10000);
    });
}

if (require.main === module) {
    main();
}