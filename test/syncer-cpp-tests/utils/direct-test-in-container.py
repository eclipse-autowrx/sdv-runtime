#!/usr/bin/env python3

"""
Direct test script to run inside the container
Tests syncer.py C++ compilation by simulating messageToKit events
"""

import asyncio
import socketio
import sys
import os

# Add the syncer directory to path
sys.path.insert(0, '/home/dev/ws/kuksa-syncer')

# Import syncer functions directly
from syncer import messageToKit

# Test data
TEST_CPP_CODE = """#include <iostream>
using namespace std;

int main() {
    cout << "Hello from Direct Container Test!" << endl;
    cout << "Testing C++ compilation in syncer.py" << endl;
    return 0;
}"""

TEST_FILES = [{
    "type": "file",
    "name": "main.cpp", 
    "content": TEST_CPP_CODE
}]

class DirectTest:
    def __init__(self):
        self.responses = []
        
    async def run_test(self):
        print("🧪 Starting direct container test...")
        print("📡 Testing syncer.py C++ compilation directly")
        
        # Create test request
        test_request = {
            "cmd": "compile_cpp_app",
            "request_from": "direct-test-client",
            "data": {
                "files": TEST_FILES,
                "app_name": "DirectTest",
                "run": True
            }
        }
        
        print("📤 Sending compile_cpp_app request to syncer...")
        
        try:
            # Call messageToKit directly
            result = await messageToKit(test_request)
            print(f"📥 messageToKit returned: {result}")
            
            if result == 0:
                print("✅ Request processed successfully")
            else:
                print("❌ Request failed")
                
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()

async def main():
    test = DirectTest()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())