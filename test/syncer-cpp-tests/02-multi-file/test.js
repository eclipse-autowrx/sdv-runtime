// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

// Test 02: Multi-file Project through syncer.py
// Reference: See request-structure.json for the complete tree structure being sent to syncer.py
const { runSyncerTest, validateSyncerResponses } = require('../utils/syncer-test-config');

const TEST_NAME = '02 Multi-file Project (via Syncer)';

const MAIN_CPP = `#include "math/Calculator.h"
#include "utils/Logger.h"
#include <iostream>

int main() {
    Logger logger;
    Calculator calc;
    
    logger.log("Starting syncer multi-file test");
    
    int result = calc.add(10, 25);
    logger.log("Calculation: 10 + 25 = " + std::to_string(result));
    
    result = calc.multiply(4, 7);
    logger.log("Calculation: 4 * 7 = " + std::to_string(result));
    
    std::cout << "Multi-file compilation through syncer successful!" << std::endl;
    return 0;
}`;

const CALCULATOR_H = `#pragma once

class Calculator {
public:
    int add(int a, int b);
    int multiply(int a, int b);
    int subtract(int a, int b);
};`;

const CALCULATOR_CPP = `#include "Calculator.h"

int Calculator::add(int a, int b) {
    return a + b;
}

int Calculator::multiply(int a, int b) {
    return a * b;
}

int Calculator::subtract(int a, int b) {
    return a - b;
}`;

const LOGGER_H = `#pragma once
#include <string>

class Logger {
public:
    void log(const std::string& message);
    void error(const std::string& message);
};`;

const LOGGER_CPP = `#include "Logger.h"
#include <iostream>
#include <ctime>

void Logger::log(const std::string& message) {
    std::time_t now = std::time(0);
    std::cout << "[LOG] " << message << std::endl;
}

void Logger::error(const std::string& message) {
    std::cout << "[ERROR] " << message << std::endl;
}`;

// Build tree structure
const FILES = [
    {
        type: "folder",
        name: "project",
        items: [
            {
                type: "file",
                name: "main.cpp",
                content: MAIN_CPP
            },
            {
                type: "folder",
                name: "math",
                items: [
                    {
                        type: "file",
                        name: "Calculator.h",
                        content: CALCULATOR_H
                    },
                    {
                        type: "file",
                        name: "Calculator.cpp", 
                        content: CALCULATOR_CPP
                    }
                ]
            },
            {
                type: "folder",
                name: "utils",
                items: [
                    {
                        type: "file",
                        name: "Logger.h",
                        content: LOGGER_H
                    },
                    {
                        type: "file",
                        name: "Logger.cpp",
                        content: LOGGER_CPP
                    }
                ]
            }
        ]
    }
];

async function main() {
    try {
        const result = await runSyncerTest({
            testName: TEST_NAME,
            files: FILES,
            appName: 'MultiFileSyncer',
            run: true,
            timeout: 45000
        });
        
        // Validate response format
        const errors = validateSyncerResponses(result.responses);
        if (errors.length > 0) {
            console.log('❌ Response validation errors:');
            errors.forEach(err => console.log(`   - ${err}`));
            process.exit(1);
        }
        
        // Check build process messages
        const buildMessages = ['configure-stdout', 'build-stdout', 'run-stdout'];
        const foundMessages = buildMessages.filter(msg => 
            result.responses.some(resp => resp.status === msg)
        );
        
        console.log(`\n📋 Build Process Validation:`);
        console.log(`   - Expected messages: ${buildMessages.join(', ')}`);
        console.log(`   - Found messages: ${foundMessages.join(', ')}`);
        
        // Check for expected output
        const expectedOutputs = [
            'Starting syncer multi-file test',
            'Calculation: 10 + 25 = 35',
            'Multi-file compilation through syncer successful!'
        ];
        
        const foundOutputs = expectedOutputs.filter(output =>
            result.responses.some(resp => 
                resp.result && resp.result.includes(output)
            )
        );
        
        console.log(`\n📋 Output Validation:`);
        expectedOutputs.forEach(output => {
            const found = foundOutputs.includes(output);
            console.log(`   ${found ? '✅' : '❌'} "${output}"`);
        });
        
        console.log(`\n📊 Test Summary:`);
        console.log(`   - Total responses: ${result.responses.length}`);
        console.log(`   - Final exit code: ${result.finalResponse.code}`);
        console.log(`   - Files compiled: 5 (main.cpp + 2 headers + 2 implementations)`);
        console.log(`   - Communication: syncer.py → Kit-Manager → CMake → Make`);
        
        if (foundOutputs.length === expectedOutputs.length) {
            console.log('✅ All expected outputs found');
            process.exit(0);
        } else {
            console.log('⚠️  Some expected outputs missing');
            process.exit(1);
        }
        
    } catch (error) {
        console.log(`❌ Test failed: ${error.message}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}