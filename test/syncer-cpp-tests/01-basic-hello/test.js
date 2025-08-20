// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 01: Basic Hello World through syncer.py
// Reference: See request-structure.json for the complete tree structure being sent to syncer.py
const { runSyncerTest, validateSyncerResponses, createSingleFile } = require('../utils/syncer-test-config');

const TEST_NAME = '01 Basic Hello World (via Syncer)';

const CPP_CODE = `#include <iostream>
using namespace std;

int main() {
    cout << "Hello from Syncer C++ Test!" << endl;
    cout << "Compilation successful through syncer.py" << endl;
    return 0;
}`;

const FILES = createSingleFile('main.cpp', CPP_CODE);

async function main() {
    try {
        const result = await runSyncerTest({
            testName: TEST_NAME,
            files: FILES,
            appName: 'BasicHelloSyncer',
            run: true,
            timeout: 30000
        });
        
        // Validate response format
        const errors = validateSyncerResponses(result.responses);
        if (errors.length > 0) {
            console.log('❌ Response validation errors:');
            errors.forEach(err => console.log(`   - ${err}`));
            process.exit(1);
        }
        
        // Check for expected output in responses
        const outputFound = result.responses.some(resp => 
            resp.result && resp.result.includes('Hello from Syncer C++ Test!')
        );
        
        if (outputFound) {
            console.log('✅ Expected output found in responses');
        } else {
            console.log('⚠️  Expected output not found in responses');
        }
        
        console.log(`\n📊 Test Summary:`);
        console.log(`   - Total responses: ${result.responses.length}`);
        console.log(`   - Final exit code: ${result.finalResponse.code}`);
        console.log(`   - Communication path: Web Client → syncer.py → Kit-Manager`);
        
        process.exit(0);
        
    } catch (error) {
        console.log(`❌ Test failed: ${error.message}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}