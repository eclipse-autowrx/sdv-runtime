// Validation test with a more complex C++ program
// Reference: See validation-test-request-structure.json for the complete tree structure being sent to syncer.py
const MockKitServer = require('./utils/mock-kit-server');

const COMPLEX_CPP = `#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

class Vehicle {
private:
    std::string id;
    double speed;
    std::vector<std::string> sensors;

public:
    Vehicle(const std::string& vehicleId) : id(vehicleId), speed(0.0) {
        sensors = {"GPS", "Camera", "Lidar", "Radar"};
    }
    
    void accelerate(double increment) {
        speed += increment;
        std::cout << "Vehicle " << id << " accelerating to " << speed << " km/h" << std::endl;
    }
    
    void reportStatus() {
        std::cout << "=== Vehicle Status Report ===" << std::endl;
        std::cout << "ID: " << id << std::endl;
        std::cout << "Speed: " << speed << " km/h" << std::endl;
        std::cout << "Active Sensors: ";
        for (const auto& sensor : sensors) {
            std::cout << sensor << " ";
        }
        std::cout << std::endl;
        std::cout << "Validation: Mock Kit Server → syncer.py → Kit-Manager WORKS!" << std::endl;
    }
};

int main() {
    std::cout << "🚗 SDV Runtime C++ Compilation Validation" << std::endl;
    
    Vehicle testVehicle("SDV-TEST-001");
    testVehicle.accelerate(30.5);
    testVehicle.accelerate(15.2);
    testVehicle.reportStatus();
    
    std::cout << "✅ Complex C++ compilation successful!" << std::endl;
    return 0;
}`;

const FILES = [{
    type: "file",
    name: "main.cpp",
    content: COMPLEX_CPP
}];

async function runValidation() {
    const mockServer = new MockKitServer(3092);  // Different port
    
    try {
        console.log('\n🔍 Running Validation Test with Complex C++ Program');
        await mockServer.start();
        
        // Start container with validation test
        const { spawn } = require('child_process');
        const dockerCmd = [
            'docker', 'run', '-d',
            '--name', 'sdv-validation-test',
            '--user', 'root',
            '--network', 'host',
            '-e', 'SYNCER_SERVER_URL=http://localhost:3092',
            '-v', `${process.cwd()}/output:/home/dev/data/output:rw`,
            'sdv-runtime-production:latest'
        ];
        
        await new Promise((resolve, reject) => {
            const child = spawn(dockerCmd[0], dockerCmd.slice(1), { stdio: 'pipe' });
            child.on('close', (code) => {
                if (code === 0) resolve();
                else reject(new Error(`Docker start failed: ${code}`));
            });
        });
        
        console.log('⏳ Waiting for syncer connection...');
        await mockServer.waitForSyncer(30000);
        
        console.log('📤 Sending complex C++ compilation request...');
        mockServer.sendCppCompileRequest(FILES, 'ValidationTest', true);
        
        console.log('⏳ Waiting for compilation...');
        const result = await mockServer.waitForCompilationComplete(60000);
        
        console.log('\n📊 Validation Results:');
        console.log(`   Success: ${result.success ? '✅' : '❌'}`);
        console.log(`   Responses: ${result.results.length}`);
        console.log(`   Exit Code: ${result.finalResult.code}`);
        
        // Check for specific outputs
        const expectedOutputs = [
            'Vehicle SDV-TEST-001 accelerating',
            'Active Sensors: GPS Camera Lidar Radar',
            'Complex C++ compilation successful!'
        ];
        
        const foundOutputs = expectedOutputs.filter(output =>
            result.results.some(resp => resp.result && resp.result.includes(output))
        );
        
        console.log('\n📋 Complex Program Validation:');
        expectedOutputs.forEach(output => {
            const found = foundOutputs.includes(output);
            console.log(`   ${found ? '✅' : '❌'} "${output.substring(0, 50)}..."`);
        });
        
        if (result.success && foundOutputs.length === expectedOutputs.length) {
            console.log('\n🎉 VALIDATION PASSED!');
            console.log('✅ Complex C++ programs compile and run correctly through syncer.py');
            return true;
        } else {
            console.log('\n❌ VALIDATION FAILED');
            return false;
        }
        
    } catch (error) {
        console.log(`❌ Validation error: ${error.message}`);
        return false;
    } finally {
        // Cleanup
        await new Promise((resolve) => {
            const cleanup = spawn('sh', ['-c', 'docker stop sdv-validation-test && docker rm sdv-validation-test'], { stdio: 'pipe' });
            cleanup.on('close', () => resolve());
        });
        mockServer.stop();
    }
}

if (require.main === module) {
    runValidation().then(success => process.exit(success ? 0 : 1));
}