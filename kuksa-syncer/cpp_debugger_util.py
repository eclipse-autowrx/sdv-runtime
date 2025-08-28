import os
import subprocess
import asyncio
import re
import datetime
import time
from pathlib import Path

# This utility uses GDB to attach to running processes for debugging.
# It attaches to child processes that we control, which is safe and doesn't require
# special ptrace permissions beyond what's needed for normal process management.

APP_DIR = Path(os.path.dirname(__file__)) / 'app'
BINARY_FILE = APP_DIR / 'main_bin'

import shm_util

# Shared memory instance
shm = None

async def compile_cpp():
    """Compile all .cpp files in the app directory."""
    global shm
    if not APP_DIR.exists():
        return False, 'App directory not found.'

    cpp_files = list(APP_DIR.rglob('*.cpp'))
    if not cpp_files:
        return False, 'No .cpp files found in the project.'

    # Convert Path objects to strings for the command
    cpp_file_paths = [str(f) for f in cpp_files]
    
    # Linux compilation with real-time library for shared memory
    cmd = ['g++', '-g', '-O0', '-o', str(BINARY_FILE)] + cpp_file_paths + ['-lrt']
    
    print(f"Compilation command: {' '.join(cmd)}", flush=True)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return False, stderr.decode()
    
    # Create shared memory after successful compilation
    shm_util.cleanup_shared_memory() # Clean up any old segment
    shm = shm_util.create_shared_memory()
    if shm is None:
        return False, "Failed to create shared memory."
        
    return True, 'Compiled successfully.'

async def run_binary():
    """Run the compiled binary in the background and return the process and its PID."""
    if not os.path.exists(BINARY_FILE):
        return None, None, 'Binary not found.'
    proc = await asyncio.create_subprocess_exec(
        BINARY_FILE,
        cwd=APP_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        bufsize=0  # Unbuffered output for real-time streaming
    )
    await asyncio.sleep(0.2)  # Give process time to start
    pid = proc.pid
    return proc, pid, 'Started.'

async def get_global_variables(watch_vars, pid=None):
    """Read global variables from shared memory."""
    global shm
    if shm is None:
        return {"error": "Shared memory not initialized"}, "Shared memory not initialized"
    
    # Write the variable names we are interested in to shared memory
    shm_util.write_to_shm(shm, watch_vars)
    
    # Read the values back immediately - no delay needed with shared memory!
    values = shm_util.read_from_shm(shm)
    return values, None

def validate_variable_setting(var_name: str, new_value: str):
    """Validate variable setting request for safety"""
    # For shared memory, we can be more flexible, but let's keep some basic validation.
    try:
        # Check if it can be converted to a number, but allow strings too.
        float(new_value)
    except ValueError:
        # It's a string, let's limit its length
        if len(new_value) > 50:
            return False, "String value is too long."
    
    return True, "Valid"

async def set_global_variable(var_name: str, new_value: str, pid: int):
    """Set a global variable value in a running C++ process using shared memory."""
    global shm
    if shm is None:
        return False, "Shared memory not initialized"
        
    is_valid, validation_msg = validate_variable_setting(var_name, new_value)
    if not is_valid:
        return False, f"Validation failed: {validation_msg}"
        
    if not is_process_running(pid):
        return False, f"Process {pid} is not running"
        
    success, message = shm_util.set_variable_in_shm(shm, var_name, new_value)
    return success, message

async def periodic_global_var_report(interval, sio, client_id, watch_vars, pid, from_id):
    """Periodically send global variable values to the client via sio.emit, from the running process."""
    first = True
    while True:
        if first:
            await asyncio.sleep(1)  # Wait 1 second before first GDB run
            first = False
        else:
            await asyncio.sleep(interval)
        
        # Check if process is still running before trying to read variables
        if not is_process_running(pid):
            print(f"Process {pid} is no longer running, stopping global variable monitoring", flush=True)
            break
            
        # Measure timing for shared memory variable read performance
        start_time = time.time()
        values, err = await get_global_variables(watch_vars, pid)
        end_time = time.time()
        read_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if values is not None:
            print(f"[{timestamp}] Global variables: {values} (read time: {read_time_ms:.2f}ms)", flush=True)
            await sio.emit("messageToKit-kitReply", {
                "kit_id": client_id,
                "request_from": from_id,
                "data": values,
                "cmd": "trace_vars",
                "read_time_ms": round(read_time_ms, 2)  # Include timing in response
            })
        else:
            print(f"[{timestamp}] Error getting global variables: {err} (read time: {read_time_ms:.2f}ms)", flush=True)
            await sio.emit("messageToKit-kitReply", {
                "kit_id": client_id,
                "result": err,
                "request_from": from_id,
                "cmd": "trace_vars",
                "read_time_ms": round(read_time_ms, 2)  # Include timing even for errors
            })

def is_process_running(pid):
    """Check if a process with the given PID is still running"""
    try:
        # Check if /proc/{pid} exists (Linux-specific but reliable)
        return os.path.exists(f"/proc/{pid}")
    except Exception:
        # Fallback: try to send signal 0 (doesn't actually send a signal)
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

def cleanup_shm():
    """Cleanup shared memory."""
    global shm
    if shm is not None:
        shm.close()
        shm = None
    shm_util.cleanup_shared_memory()
