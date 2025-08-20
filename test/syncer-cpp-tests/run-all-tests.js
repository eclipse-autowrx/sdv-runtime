// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test runner for syncer C++ compilation tests
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const TEST_DIRECTORIES = [
    '01-basic-hello',
    '02-multi-file', 
    '03-error-handling'
];

const TIMEOUT_MS = 60000; // 1 minute per test

async function runTest(testDir) {
    const testPath = path.join(__dirname, testDir, 'test.js');
    
    if (!fs.existsSync(testPath)) {
        return {
            testDir,
            success: false,
            error: 'Test file not found',
            duration: 0
        };
    }
    
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Running: ${testDir}`);
    console.log(`${'='.repeat(60)}`);
    
    const startTime = Date.now();
    
    return new Promise((resolve) => {
        const child = spawn('node', [testPath], {
            cwd: path.join(__dirname, testDir),
            stdio: 'inherit'
        });
        
        const timeout = setTimeout(() => {
            child.kill('SIGKILL');
            resolve({
                testDir,
                success: false,
                error: 'Test timeout',
                duration: Date.now() - startTime
            });
        }, TIMEOUT_MS);
        
        child.on('close', (code) => {
            clearTimeout(timeout);
            const duration = Date.now() - startTime;
            
            resolve({
                testDir,
                success: code === 0,
                error: code !== 0 ? `Exit code: ${code}` : null,
                duration
            });
        });
        
        child.on('error', (error) => {
            clearTimeout(timeout);
            resolve({
                testDir,
                success: false,
                error: error.message,
                duration: Date.now() - startTime
            });
        });
    });
}

async function checkPrerequisites() {
    console.log(`🔍 Checking prerequisites...`);
    
    // Check if socket.io-client is installed
    try {
        require('socket.io-client');
        console.log(`✅ socket.io-client is available`);
    } catch (e) {
        console.log(`❌ socket.io-client not found. Run: npm install socket.io-client`);
        return false;
    }
    
    // Check if syncer port is accessible
    const net = require('net');
    return new Promise((resolve) => {
        const socket = new net.Socket();
        
        socket.setTimeout(3000);
        
        socket.on('connect', () => {
            socket.destroy();
            console.log(`✅ Syncer.py is accessible on port 55555`);
            resolve(true);
        });
        
        socket.on('error', () => {
            console.log(`❌ Cannot connect to syncer.py on port 55555`);
            console.log(`   Make sure SDV runtime container is running with syncer.py`);
            resolve(false);
        });
        
        socket.on('timeout', () => {
            socket.destroy();
            console.log(`❌ Timeout connecting to syncer.py on port 55555`);
            resolve(false);
        });
        
        socket.connect(55555, '127.0.0.1');
    });
}

async function main() {
    console.log(`🧪 Syncer C++ Compilation Test Suite`);
    console.log(`📡 Testing: Web Client → syncer.py → Kit-Manager`);
    
    // Check prerequisites
    const prereqsOk = await checkPrerequisites();
    if (!prereqsOk) {
        console.log(`\n❌ Prerequisites not met. Exiting.`);
        process.exit(1);
    }
    
    const startTime = Date.now();
    const results = [];
    
    // Run tests sequentially to avoid conflicts
    for (const testDir of TEST_DIRECTORIES) {
        const result = await runTest(testDir);
        results.push(result);
    }
    
    // Print summary
    const totalDuration = Date.now() - startTime;
    const passed = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    
    console.log(`\n${'='.repeat(60)}`);
    console.log(`📊 SYNCER C++ COMPILATION TEST RESULTS`);
    console.log(`${'='.repeat(60)}`);
    
    results.forEach(result => {
        const status = result.success ? '✅ PASS' : '❌ FAIL';
        const duration = `${(result.duration / 1000).toFixed(1)}s`;
        console.log(`${status} ${result.testDir.padEnd(20)} (${duration})`);
        
        if (!result.success && result.error) {
            console.log(`     Error: ${result.error}`);
        }
    });
    
    console.log(`\n📈 Summary:`);
    console.log(`   Passed: ${passed}/${results.length}`);
    console.log(`   Failed: ${failed}/${results.length}`);
    console.log(`   Total time: ${(totalDuration / 1000).toFixed(1)}s`);
    console.log(`   Architecture: Web Client → syncer.py (55555) → Kit-Manager (3090)`);
    
    if (failed > 0) {
        console.log(`\n❌ Some tests failed. Check output above.`);
        process.exit(1);
    } else {
        console.log(`\n✅ All syncer C++ compilation tests passed!`);
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error(`\n💥 Test runner error: ${error.message}`);
        process.exit(1);
    });
}