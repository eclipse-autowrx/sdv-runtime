const io = require('socket.io-client');
const fs = require('fs');
const path = require('path');

console.log('🔌 Connecting to SDV Runtime for multi-file test...');
const socket = io('http://localhost:3090');

// Helper to read all source files
function loadProjectFiles() {
    const files = {};
    
    // Read main.cpp
    files['main.cpp'] = fs.readFileSync(path.join(__dirname, 'main.cpp'), 'utf8');
    
    // Read vehicle files
    files['vehicle/Vehicle.h'] = fs.readFileSync(path.join(__dirname, 'vehicle/Vehicle.h'), 'utf8');
    files['vehicle/Vehicle.cpp'] = fs.readFileSync(path.join(__dirname, 'vehicle/Vehicle.cpp'), 'utf8');
    
    // Read utils files
    files['utils/Logger.h'] = fs.readFileSync(path.join(__dirname, 'utils/Logger.h'), 'utf8');
    files['utils/Logger.cpp'] = fs.readFileSync(path.join(__dirname, 'utils/Logger.cpp'), 'utf8');
    
    return files;
}

socket.on('connect', () => {
    console.log('✅ Connected! Running multi-file C++ compilation test...\n');
    
    const files = loadProjectFiles();
    
    console.log('📁 Project Structure:');
    console.log('─'.repeat(40));
    Object.keys(files).forEach(filename => {
        const lines = files[filename].split('\n').length;
        console.log(`📄 ${filename} (${lines} lines)`);
    });
    console.log('─'.repeat(40));
    
    // Send compilation request
    console.log('\n🔨 Compiling multi-file C++ project...\n');
    socket.emit('compile_cpp', {
        files: files,
        app_name: 'MultiFileTest',
        run: true
    });
});

let buildPhase = 'Starting';
let fileCount = 0;

socket.on('compile_cpp_reply', (response) => {
    // Track build phases
    if (response.status === 'file-written') {
        fileCount++;
        console.log(`📝 File ${fileCount}/5: ${response.result.trim()}`);
    } else if (response.status.includes('configure')) {
        if (buildPhase !== 'Configure') {
            buildPhase = 'Configure';
            console.log('\n🔧 CMake Configuration Phase:');
        }
        console.log(`   ${response.result.trim()}`);
    } else if (response.status.includes('build')) {
        if (buildPhase !== 'Build') {
            buildPhase = 'Build';
            console.log('\n🔨 Build Phase:');
        }
        console.log(`   ${response.result.trim()}`);
    } else if (response.status.includes('run')) {
        if (buildPhase !== 'Run') {
            buildPhase = 'Run';
            console.log('\n🚀 Execution Phase:');
        }
        console.log(`   ${response.result.trim()}`);
    } else {
        console.log(`[${response.status}] ${response.result.trim()}`);
    }
    
    // Handle completion
    if (response.isDone) {
        if (response.code === 0) {
            console.log('\n🎉 SUCCESS: Multi-file C++ project compiled and executed!');
            console.log('✅ All files processed successfully');
            console.log('✅ Dependencies resolved automatically');
            console.log('✅ CMake build system working');
        } else {
            console.log('\n❌ FAILED: Exit code', response.code);
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
}, 45000);