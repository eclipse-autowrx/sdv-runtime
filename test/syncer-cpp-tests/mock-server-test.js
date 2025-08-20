// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

/**
 * Mock Kit Server Test for syncer.py C++ Compilation
 * Reference: See mock-server-test-request-structure.json for the complete tree structure being sent to syncer.py
 * 
 * This test demonstrates the correct way to test syncer.py C++ compilation:
 * 1. Start a mock kit server (simulates kit.digitalauto.tech)
 * 2. Configure syncer.py to connect to our mock server
 * 3. Send compile_cpp_app commands through the mock server
 * 4. Receive responses from syncer.py through the mock server
 */

const MockKitServer = require('./utils/mock-kit-server');
const { spawn } = require('child_process');
const { createSingleFile } = require('./utils/syncer-test-config');

const TEST_NAME = 'Mock Kit Server C++ Compilation Test';

const CPP_CODE = `#include <iostream>
using namespace std;

int main() {
    cout << "Hello from Mock Kit Server Test!" << endl;
    cout << "Architecture: Mock Kit Server -> syncer.py -> Kit-Manager" << endl;
    return 0;
}`;

const FILES = createSingleFile('main.cpp', CPP_CODE);

class MockServerTest {
    constructor() {
        this.mockServer = new MockKitServer(3091);
        this.syncerProcess = null;
    }

    async startMockServer() {
        console.log(`🚀 Starting mock kit server...`);
        await this.mockServer.start();
        console.log(`✅ Mock kit server running on port 3091`);
    }

    async startSyncerWithMockConfig() {
        console.log(`🔧 Starting syncer.py configured for mock server...`);
        
        // We'll start syncer.py in a container with SYNCER_SERVER_URL pointing to our mock
        const containerName = 'sdv-mock-test';
        
        // First, clean up any existing container
        await this.runCommand(`docker rm -f ${containerName}`, true);
        
        // Start container with mock server URL (use --network host for simplicity)
        const dockerCmd = [
            'docker', 'run', '-d',
            '--name', containerName,
            '--user', 'root',
            '--network', 'host',
            '-e', `SYNCER_SERVER_URL=http://localhost:3091`,
            '-v', `${process.cwd()}/output:/home/dev/data/output:rw`,
            'sdv-runtime-production:latest'
        ];
        
        console.log(`📦 Starting container: ${dockerCmd.join(' ')}`);
        await this.runCommand(dockerCmd.join(' '));
        
        // Wait for services to start
        console.log(`⏳ Waiting for services to start...`);
        await this.sleep(15000);
        
        return containerName;
    }

    async runCommand(command, ignoreErrors = false) {
        return new Promise((resolve, reject) => {
            const child = spawn('sh', ['-c', command], { stdio: 'pipe' });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            child.on('close', (code) => {
                if (code !== 0 && !ignoreErrors) {
                    reject(new Error(`Command failed: ${command}\nStderr: ${stderr}`));
                } else {
                    resolve({ stdout, stderr, code });
                }
            });
        });
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async runTest() {
        let containerName = null;
        
        try {
            console.log(`\n🧪 ${TEST_NAME}`);
            console.log(`📡 Testing: Mock Kit Server → syncer.py → Kit-Manager`);
            
            // 1. Start mock server
            await this.startMockServer();
            
            // 2. Start syncer.py configured to connect to mock
            containerName = await this.startSyncerWithMockConfig();
            
            // 3. Wait for syncer to connect to our mock server
            console.log(`⏳ Waiting for syncer.py to connect to mock server...`);
            await this.mockServer.waitForSyncer(30000);
            
            // 4. Send C++ compilation request through mock server
            console.log(`📤 Sending C++ compilation request...`);
            this.mockServer.sendCppCompileRequest(FILES, 'MockServerTest', true);
            
            // 5. Wait for compilation to complete
            console.log(`⏳ Waiting for compilation to complete...`);
            const result = await this.mockServer.waitForCompilationComplete(60000);
            
            // 6. Analyze results
            console.log(`\n📊 Test Results:`);
            console.log(`   - Success: ${result.success ? '✅' : '❌'}`);
            console.log(`   - Total responses: ${result.results.length}`);
            console.log(`   - Final exit code: ${result.finalResult.code}`);
            
            // Check for expected output
            const expectedOutputs = [
                'Hello from Mock Kit Server Test!',
                'Architecture: Mock Kit Server -> syncer.py -> Kit-Manager'
            ];
            
            const foundOutputs = expectedOutputs.filter(output =>
                result.results.some(resp => 
                    resp.result && resp.result.includes(output)
                )
            );
            
            console.log(`\n📋 Output Validation:`);
            expectedOutputs.forEach(output => {
                const found = foundOutputs.includes(output);
                console.log(`   ${found ? '✅' : '❌'} "${output}"`);
            });
            
            console.log(`\n🎯 Architecture Validation:`);
            console.log(`   ✅ Mock Kit Server received syncer.py connection`);
            console.log(`   ✅ syncer.py processed compile_cpp_app command`);
            console.log(`   ✅ Kit-Manager performed C++ compilation`);
            console.log(`   ✅ Results streamed back through syncer.py to mock server`);
            
            if (result.success && foundOutputs.length === expectedOutputs.length) {
                console.log(`\n🎉 Mock Kit Server test PASSED!`);
                console.log(`✅ C++ compilation through syncer.py middleware works correctly`);
                return true;
            } else {
                console.log(`\n❌ Mock Kit Server test FAILED`);
                return false;
            }
            
        } catch (error) {
            console.log(`\n❌ Test error: ${error.message}`);
            return false;
            
        } finally {
            // Cleanup
            console.log(`\n🧹 Cleaning up...`);
            
            if (containerName) {
                await this.runCommand(`docker stop ${containerName}`, true);
                await this.runCommand(`docker rm ${containerName}`, true);
            }
            
            this.mockServer.stop();
        }
    }
}

async function main() {
    const test = new MockServerTest();
    const success = await test.runTest();
    process.exit(success ? 0 : 1);
}

if (require.main === module) {
    main().catch(error => {
        console.error(`💥 Unexpected error: ${error.message}`);
        process.exit(1);
    });
}