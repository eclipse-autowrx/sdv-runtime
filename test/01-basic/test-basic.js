const io = require('socket.io-client');
const fs = require('fs');
const path = require('path');

console.log('🔌 Connecting to SDV Runtime...');
const socket = io('http://localhost:3090');

socket.on('connect', () => {
    console.log('✅ Connected! Running basic C++ compilation test...\n');
    
    // Read the C++ source file
    const cppCode = fs.readFileSync(path.join(__dirname, 'main.cpp'), 'utf8');
    
    console.log('📁 C++ Source Code:');
    console.log('─'.repeat(40));
    console.log(cppCode);
    console.log('─'.repeat(40));
    
    // Send compilation request
    console.log('\n🔨 Compiling C++ code...\n');
    socket.emit('compile_cpp', {
        files: {
            'main.cpp': cppCode
        },
        app_name: 'BasicTest',
        run: true
    });
});

socket.on('compile_cpp_reply', (response) => {
    // Log all responses for learning
    console.log(`[${response.status}] ${response.result.trim()}`);
    
    // Handle final result
    if (response.isDone) {
        if (response.code === 0) {
            console.log('\n🎉 SUCCESS: C++ compilation and execution completed!');
        } else {
            console.log('\n❌ FAILED: Exit code', response.code);
        }
        socket.disconnect();
    }
});

socket.on('connect_error', (error) => {
    console.log('❌ Connection failed:', error.message);
    console.log('💡 Make sure SDV Runtime container is running on port 3090');
    process.exit(1);
});

// Timeout after 30 seconds
setTimeout(() => {
    console.log('\n⏰ Test timeout - disconnecting');
    socket.disconnect();
}, 30000);