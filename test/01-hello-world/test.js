// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 01: Hello World - Basic C++ compilation (Tree Structure Format)
const fs = require('fs');
const path = require('path');
const testConfig = require('../utils/test-config');

const TEST_NAME = '01 Hello World (Tree Structure Format)';

const FILES = [
    {
        type: "folder",
        name: "src",
        items: [
            {
                type: "file",
                name: "main.cpp",
                content: fs.readFileSync(path.join(__dirname, 'main.cpp'), 'utf8')
            }
        ]
    }
];

testConfig.runTest({
    testName: TEST_NAME,
    files: FILES,
    appName: 'HelloWorld',
    run: true,
    timeout: 20000,
    expectedOutput: 'hello from sdv runtime'
});