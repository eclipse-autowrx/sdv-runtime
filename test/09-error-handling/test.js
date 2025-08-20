// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 09: Error Handling - Intentional compilation errors
const fs = require('fs');
const path = require('path');
const testConfig = require('../utils/test-config');

const TEST_NAME = '09 Error Handling - Compilation Error Test';

const FILES = [
    {
        type: "folder",
        name: "error_test",
        items: [
            {
                type: "file",
                name: "main.cpp",
                content: fs.readFileSync(path.join(__dirname, 'main.cpp'), 'utf8')
            },
            {
                type: "file",
                name: "broken_syntax.cpp",
                content: fs.readFileSync(path.join(__dirname, 'broken_syntax.cpp'), 'utf8')
            }
        ]
    }
];

testConfig.runTest({
    testName: TEST_NAME,
    files: FILES,
    appName: 'ErrorTest',
    run: false,  // Don't try to run since compilation should fail
    timeout: 20000,
    shouldFail: true  // We expect this test to fail
});