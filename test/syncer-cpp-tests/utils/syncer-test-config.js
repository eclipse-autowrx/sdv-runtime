// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

const io = require('socket.io-client');

/**
 * Test configuration for syncer.py C++ compilation tests
 * Tests the production flow: Web Client → syncer.py → Kit-Manager
 */

const SYNCER_URL = 'http://localhost:55555';
const DEFAULT_TIMEOUT = 45000;

function generateClientId() {
    return 'test-client-' + Math.random().toString(36).substr(2, 9);
}

async function runSyncerTest(options) {
    const {
        testName,
        files,
        appName = 'SyncerTestApp',
        run = true,
        timeout = DEFAULT_TIMEOUT
    } = options;

    console.log(`\n🧪 Starting: ${testName}`);
    console.log(`📡 Connecting to syncer.py at ${SYNCER_URL}`);
    
    const clientId = generateClientId();
    console.log(`🆔 Client ID: ${clientId}`);

    return new Promise((resolve, reject) => {
        const socket = io(SYNCER_URL);
        let responses = [];
        let timeoutId;
        let connected = false;

        // Set timeout
        timeoutId = setTimeout(() => {
            console.log(`❌ Test timeout after ${timeout}ms`);
            socket.disconnect();
            reject(new Error(`Test timeout: ${testName}`));
        }, timeout);

        // Connection handlers
        socket.on('connect', () => {
            connected = true;
            console.log(`✅ Connected to syncer.py`);
            
            // Send compilation request through syncer
            const request = {
                cmd: "compile_cpp_app",
                request_from: clientId,
                data: {
                    files: files,
                    app_name: appName,
                    run: run
                }
            };
            
            console.log(`📤 Sending compile_cpp_app request`);
            console.log(`   Files: ${files.length} items`);
            console.log(`   App: ${appName}`);
            console.log(`   Run: ${run}`);
            
            socket.emit('messageToKit', request);
        });

        socket.on('connect_error', (error) => {
            console.log(`❌ Connection failed: ${error.message}`);
            clearTimeout(timeoutId);
            reject(new Error(`Connection failed: ${error.message}`));
        });

        // Listen for syncer responses
        socket.on('messageToKit-kitReply', (response) => {
            if (response.request_from === clientId && response.cmd === 'compile_cpp_app') {
                responses.push(response);
                
                console.log(`📥 [${response.status}] ${response.result.trim()}`);
                
                if (response.isDone) {
                    clearTimeout(timeoutId);
                    socket.disconnect();
                    
                    const success = response.code === 0;
                    const statusIcon = success ? '✅' : '❌';
                    console.log(`${statusIcon} ${testName} - Exit code: ${response.code}`);
                    
                    if (success) {
                        resolve({
                            success: true,
                            responses: responses,
                            finalResponse: response
                        });
                    } else {
                        reject(new Error(`Compilation failed with code ${response.code}`));
                    }
                }
            }
        });

        socket.on('disconnect', () => {
            if (!connected) return;
            console.log(`📴 Disconnected from syncer.py`);
        });
    });
}

/**
 * Validate that responses follow expected syncer protocol
 */
function validateSyncerResponses(responses) {
    const errors = [];
    
    if (!Array.isArray(responses) || responses.length === 0) {
        errors.push('No responses received');
        return errors;
    }
    
    // Check each response has required syncer fields
    responses.forEach((resp, i) => {
        if (!resp.hasOwnProperty('kit_id')) {
            errors.push(`Response ${i}: missing kit_id field`);
        }
        if (!resp.hasOwnProperty('request_from')) {
            errors.push(`Response ${i}: missing request_from field`);
        }
        if (resp.cmd !== 'compile_cpp_app') {
            errors.push(`Response ${i}: expected cmd=compile_cpp_app, got ${resp.cmd}`);
        }
        if (!resp.hasOwnProperty('status')) {
            errors.push(`Response ${i}: missing status field`);
        }
        if (!resp.hasOwnProperty('isDone')) {
            errors.push(`Response ${i}: missing isDone field`);
        }
    });
    
    // Check final response is marked as done
    const finalResponse = responses[responses.length - 1];
    if (!finalResponse.isDone) {
        errors.push('Final response not marked as done');
    }
    
    return errors;
}

/**
 * Simple tree structure helper for single file
 */
function createSingleFile(filename, content) {
    return [{
        type: "file",
        name: filename,
        content: content
    }];
}

/**
 * Tree structure helper for folder with files
 */
function createFolder(folderName, files) {
    return [{
        type: "folder", 
        name: folderName,
        items: files.map(f => ({
            type: "file",
            name: f.name,
            content: f.content
        }))
    }];
}

module.exports = {
    runSyncerTest,
    validateSyncerResponses,
    createSingleFile,
    createFolder,
    SYNCER_URL,
    DEFAULT_TIMEOUT
};