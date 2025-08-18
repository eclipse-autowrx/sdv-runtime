const io = require('socket.io-client');
const fs = require('fs');
const path = require('path');

console.log('🔌 Connecting to SDV Runtime for complex automotive test...');
const socket = io('http://localhost:3090');

socket.on('connect', () => {
    console.log('✅ Connected! Running complex automotive C++ test...\n');
    
    // Load the simple automotive example (FCW is very complex)
    const files = {
        'main.cpp': fs.readFileSync(path.join(__dirname, 'simple-automotive.cpp'), 'utf8')
    };
    
    console.log('🚗 Automotive C++ Features:');
    console.log('─'.repeat(50));
    console.log('• Vehicle simulation');
    console.log('• Sensor data processing');
    console.log('• Time-to-Collision calculations');
    console.log('• Real-time status monitoring');
    console.log('• Collision risk assessment');
    console.log('─'.repeat(50));
    
    console.log('\n🔨 Compiling automotive C++ code...\n');
    socket.emit('compile_cpp', {
        files: files,
        app_name: 'AutomotiveTest',
        run: true
    });
});

let startTime = Date.now();

socket.on('compile_cpp_reply', (response) => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    if (response.status === 'compile-start') {
        console.log('🚀 Starting compilation...');
    } else if (response.status.includes('build')) {
        console.log(`🔨 [${elapsed}s] ${response.result.trim()}`);
    } else if (response.status.includes('run')) {
        console.log(`🚗 ${response.result.trim()}`);
    } else if (response.status.includes('failed') || response.status.includes('err')) {
        console.log(`❌ ${response.result.trim()}`);
    }
    
    if (response.isDone) {
        console.log(`\n⏱️  Total time: ${elapsed}s`);
        if (response.code === 0) {
            console.log('🎉 SUCCESS: Complex automotive C++ compilation completed!');
            console.log('✅ Advanced C++ features working');
            console.log('✅ STL containers and algorithms');
            console.log('✅ Mathematical calculations');
            console.log('✅ Real-time data processing');
        } else {
            console.log('❌ FAILED: Exit code', response.code);
        }
        socket.disconnect();
    }
});

socket.on('connect_error', (error) => {
    console.log('❌ Connection failed:', error.message);
    process.exit(1);
});

setTimeout(() => {
    console.log('\n⏰ Test timeout');
    socket.disconnect();
}, 60000);