// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 03: Multi-file Project (Tree Structure Format)
const fs = require('fs');
const path = require('path');
const testConfig = require('../utils/test-config');

const TEST_NAME = '03 Multi-file Project (Tree Structure Format)';

const FILES = [
    {
        type: "folder",
        name: "project",
        items: [
            {
                type: "file",
                name: "main.cpp",
                content: fs.readFileSync(path.join(__dirname, 'main.cpp'), 'utf8')
            },
            {
                type: "folder",
                name: "math",
                items: [
                    {
                        type: "file",
                        name: "calculator.h",
                        content: fs.readFileSync(path.join(__dirname, 'math/calculator.h'), 'utf8')
                    },
                    {
                        type: "file",
                        name: "calculator.cpp",
                        content: fs.readFileSync(path.join(__dirname, 'math/calculator.cpp'), 'utf8')
                    }
                ]
            },
            {
                type: "folder",
                name: "utils",
                items: [
                    {
                        type: "file",
                        name: "logger.h",
                        content: fs.readFileSync(path.join(__dirname, 'utils/logger.h'), 'utf8')
                    },
                    {
                        type: "file",
                        name: "logger.cpp",
                        content: fs.readFileSync(path.join(__dirname, 'utils/logger.cpp'), 'utf8')
                    }
                ]
            }
        ]
    }
];

testConfig.runTest({
    testName: TEST_NAME,
    files: FILES,
    appName: 'MultiFileTree',
    run: true,
    timeout: 30000,
    expectedOutput: '10 + 5 = 15'
});