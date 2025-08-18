// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

const io = require('socket.io-client');

const socket = io('http://localhost:3090');

const cppCode = `
#include <iostream>
int main() {
    std::cout << "Hello from basic test!" << std::endl;
    return 0;
}
`;

socket.on('connect', () => {
    console.log('✅ Connected to SDV Runtime');
    console.log('🔨 Starting basic C++ compilation...\n');
    
    socket.emit('compile_cpp', {
        files: {
            'main.cpp': cppCode
        },
        app_name: 'BasicTest',
        run: true
    });
});

socket.on('compile_cpp_reply', (response) => {
    console.log(`[${response.status}] ${response.result.trim()}`);
    
    if (response.isDone) {
        if (response.code === 0) {
            console.log('\n🎉 SUCCESS!');
        } else {
            console.log('\n❌ FAILED');
        }
        socket.disconnect();
    }
});

socket.on('connect_error', (error) => {
    console.log('❌ Connection failed:', error.message);
    process.exit(1);
});