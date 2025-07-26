# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

"""
Test script for syncer_lite functionality.
This demonstrates how the lite syncer would work with a simple Python app.
"""

import asyncio
import time
from pexpect_util import pexpect_subpiper

async def test_stdout_callback(master_id: str, line: str):
    """Test callback for stdout"""
    print(f"[{master_id}] STDOUT: {line}")

async def test_stderr_callback(master_id: str, line: str):
    """Test callback for stderr"""
    print(f"[{master_id}] STDERR: {line}")

async def test_finished_callback(master_id: str, return_code: int):
    """Test callback for process completion"""
    print(f"[{master_id}] FINISHED: Process completed with return code {return_code}")

def create_test_python_app():
    """Create a test Python app that generates output"""
    test_code = '''
import time
import sys

print("Starting test application...")
print("This is a test Python app for syncer_lite")

for i in range(5):
    print(f"Counter: {i}")
    time.sleep(1)

print("Test application completed successfully")
sys.exit(0)
'''
    
    with open("test_app.py", "w") as f:
        f.write(test_code)
    
    return "test_app.py"

async def test_syncer_lite():
    """Test the syncer_lite functionality"""
    print("Testing syncer_lite functionality...")
    print("=" * 50)
    
    # Create test Python app
    test_file = create_test_python_app()
    print(f"Created test app: {test_file}")
    
    # Test 1: Basic execution
    print("\nTest 1: Basic Python app execution")
    print("-" * 30)
    
    process = pexpect_subpiper(
        cmd=f"python -u {test_file}",
        master_id="test1",
        stdout_callback=test_stdout_callback,
        stderr_callback=test_stderr_callback,
        finished_callback=test_finished_callback
    )
    
    # Wait for process to complete
    return_code = process.wait()
    print(f"Process finished with return code: {return_code}")
    
    # Test 2: Process with error
    print("\nTest 2: Python app with error")
    print("-" * 30)
    
    error_code = '''
import sys
print("This will cause an error...")
undefined_variable  # This will cause a NameError
'''
    
    with open("error_app.py", "w") as f:
        f.write(error_code)
    
    process2 = pexpect_subpiper(
        cmd="python -u error_app.py",
        master_id="test2",
        stdout_callback=test_stdout_callback,
        stderr_callback=test_stderr_callback,
        finished_callback=test_finished_callback
    )
    
    return_code2 = process2.wait()
    print(f"Error process finished with return code: {return_code2}")
    
    # Test 3: Long-running process with kill
    print("\nTest 3: Long-running process with kill")
    print("-" * 30)
    
    long_running_code = '''
import time
import sys

print("Starting long-running process...")
for i in range(10):
    print(f"Long running: {i}")
    time.sleep(1)
print("Long running process completed")
'''
    
    with open("long_app.py", "w") as f:
        f.write(long_running_code)
    
    process3 = pexpect_subpiper(
        cmd="python -u long_app.py",
        master_id="test3",
        stdout_callback=test_stdout_callback,
        stderr_callback=test_stderr_callback,
        finished_callback=test_finished_callback
    )
    
    # Let it run for 3 seconds then kill it
    await asyncio.sleep(3)
    print("Killing long-running process...")
    process3.kill()
    
    # Wait a bit for cleanup
    await asyncio.sleep(1)
    
    # Test 4: Process info
    print("\nTest 4: Process information")
    print("-" * 30)
    
    process4 = pexpect_subpiper(
        cmd="python -c 'print(\"Quick test\"); exit(42)'",
        master_id="test4",
        stdout_callback=test_stdout_callback,
        stderr_callback=test_stderr_callback,
        finished_callback=test_finished_callback
    )
    
    # Get process info while running
    info = process4.get_info()
    print(f"Process info: {info}")
    
    return_code4 = process4.wait()
    print(f"Quick test finished with return code: {return_code4}")
    
    # Final info
    final_info = process4.get_info()
    print(f"Final process info: {final_info}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_syncer_lite()) 