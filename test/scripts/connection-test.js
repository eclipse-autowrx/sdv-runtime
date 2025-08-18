// Copyright (c) 2025 Eclipse Foundation.
// 
// This program and the accompanying materials are made available under the
// terms of the MIT License which is available at
// https://opensource.org/licenses/MIT.
//
// SPDX-License-Identifier: MIT

const io = require('socket.io-client');

console.log('🔌 Testing WebSocket connection to SDV Runtime...');

const socket = io('http://localhost:3090', {
    timeout: 5000,
    forceNew: true
});

socket.on('connect', () => {
    console.log('✅ Connection successful!');
    console.log('🔌 Socket ID:', socket.id);
    console.log('🌐 Server ready for C++ compilation');
    socket.disconnect();
});

socket.on('connect_error', (error) => {
    console.log('❌ Connection failed:', error.message);
    console.log('\n💡 Troubleshooting:');
    console.log('  1. Is SDV Runtime container running?');
    console.log('  2. Check port 3090 is accessible');
    console.log('  3. Try: docker ps | grep sdv-runtime');
    process.exit(1);
});

socket.on('disconnect', () => {
    console.log('👋 Disconnected');
    process.exit(0);
});

// Timeout after 10 seconds
setTimeout(() => {
    console.log('⏰ Connection timeout');
    socket.disconnect();
    process.exit(1);
}, 10000);