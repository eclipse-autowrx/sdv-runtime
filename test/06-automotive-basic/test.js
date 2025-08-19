// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 06: Automotive Basic - Vehicle simulation
const fs = require('fs');
const path = require('path');
const testConfig = require('../utils/test-config');

const TEST_NAME = '06 Automotive Basic - Vehicle Simulation';

const FILES = [
    {
        type: "folder",
        name: "automotive",
        items: [
            {
                type: "file",
                name: "main.cpp",
                content: fs.readFileSync(path.join(__dirname, 'main.cpp'), 'utf8')
            },
            {
                type: "file",
                name: "vehicle.h",
                content: fs.readFileSync(path.join(__dirname, 'vehicle.h'), 'utf8')
            },
            {
                type: "file",
                name: "vehicle.cpp",
                content: fs.readFileSync(path.join(__dirname, 'vehicle.cpp'), 'utf8')
            }
        ]
    }
];

testConfig.runTest({
    testName: TEST_NAME,
    files: FILES,
    appName: 'AutomotiveBasic',
    run: true,
    timeout: 25000,
    expectedOutput: 'SDV-001'
});