import os
import subprocess
import asyncio
import re
import datetime

# This utility uses GDB to attach to running processes for debugging.
# It attaches to child processes that we control, which is safe and doesn't require
# special ptrace permissions beyond what's needed for normal process management.

APP_DIR = os.path.join(os.path.dirname(__file__), 'app')
CPP_FILE = os.path.join(APP_DIR, 'main.cpp')
BINARY_FILE = os.path.join(APP_DIR, 'main_bin')

async def compile_cpp():
    """Compile main.cpp in the app directory."""
    if not os.path.exists(CPP_FILE):
        return False, 'main.cpp not found.'
    
    # Linux compilation - no -arch flag needed
    cmd = ['g++', CPP_FILE, '-g', '-O0', '-o', BINARY_FILE]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return False, stderr.decode()
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
    """Use gdb to extract only the specified watch_vars and their values from the running process."""
    values = {}
    
    # If no PID provided, we can't monitor a running process
    if pid is None:
        for var in [v.strip() for v in watch_vars.split(',') if v.strip()]:
            values[var] = "No process ID provided for monitoring"
        return values, None
    
    for var in [v.strip() for v in watch_vars.split(',') if v.strip()]:
        # Use GDB to attach to the running process and read variables
        # This is safe because we're attaching to our own child process
        gdb_cmd = f"gdb -q --batch -ex 'file {BINARY_FILE}' -ex 'attach {pid}' -ex 'print {var}' -ex 'detach' -ex 'quit'"
        proc_val = await asyncio.create_subprocess_shell(
            gdb_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        out_val, err_val = await proc_val.communicate()
        
        if proc_val.returncode != 0:
            values[var] = f"Error: {err_val.decode().strip()}"
            continue
        
        # Try to match the output - GDB might output in different formats
        output = out_val.decode()
        match = re.search(r'\$\d+ = (.+)', output)
        if not match:
            # Try alternative pattern for global variables
            match = re.search(rf'{var}\s*=\s*(.+)', output)
        if not match:
            # Try to find any number in the output
            match = re.search(r'(\d+)', output)
            
        if match:
            values[var] = match.group(1).strip()
        else:
            values[var] = "N/A"
    
    return values, None

def validate_variable_setting(var_name: str, new_value: str):
    """Validate variable setting request for safety"""
    # List of allowed variables that can be safely modified
    allowed_vars = ['counter', 'globalValue']
    
    if var_name not in allowed_vars:
        return False, f"Variable '{var_name}' not in allowed list: {allowed_vars}"
    
    # Type validation for specific variables
    if var_name == 'counter':
        try:
            int_val = int(new_value)
            if int_val < 0:
                return False, f"Counter value must be non-negative, got: {int_val}"
            if int_val > 1000000:  # Reasonable upper limit
                return False, f"Counter value too high: {int_val}"
        except ValueError:
            return False, f"Counter value must be an integer, got: '{new_value}'"
    
    elif var_name == 'globalValue':
        try:
            float_val = float(new_value)
            if float_val < -1000000 or float_val > 1000000:
                return False, f"Global value out of reasonable range: {float_val}"
        except ValueError:
            return False, f"Global value must be a number, got: '{new_value}'"
    
    return True, "Valid"

async def set_global_variable(var_name: str, new_value: str, pid: int):
    """Set a global variable value in a running C++ process using GDB"""
    try:
        if pid is None:
            return False, "No process ID provided for setting variable"
        
        # Validate the variable setting request
        is_valid, validation_msg = validate_variable_setting(var_name, new_value)
        if not is_valid:
            return False, f"Validation failed: {validation_msg}"
        
        # Use GDB to attach to the running process and set the variable
        # This is safe because we're attaching to our own child process
        gdb_cmd = f"gdb -q --batch -ex 'file {BINARY_FILE}' -ex 'attach {pid}' -ex 'set {var_name} = {new_value}' -ex 'print {var_name}' -ex 'detach' -ex 'quit'"
        
        proc = await asyncio.create_subprocess_shell(
            gdb_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return False, f"GDB error: {stderr.decode().strip()}"
        
        # Verify the variable was set by checking the print output
        output = stdout.decode()
        match = re.search(r'\$\d+ = (.+)', output)
        
        if match:
            actual_value = match.group(1).strip()
            return True, f"Successfully set {var_name} = {new_value} (verified: {actual_value})"
        else:
            return False, f"Could not verify variable {var_name} was set"
            
    except Exception as e:
        return False, f"Error setting variable: {str(e)}"

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
            
        values, err = await get_global_variables(watch_vars, pid)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if values is not None:
            print(f"[{timestamp}] Global variables: {values}", flush=True)
            # INSERT_YOUR_CODE
            # If values is a string (from get_global_variables), try to parse it into a dict of {var_name: value}
            # If it's already a dict, use as is.
            # Otherwise, fallback to sending as-is.
            result_data = {}
            if isinstance(values, dict):
                result_data = values
            elif isinstance(values, str):
                # Try to parse lines like "counter = 42\nfoo = 1.23"
                for line in values.strip().splitlines():
                    if '=' in line:
                        k, v = line.split('=', 1)
                        result_data[k.strip()] = v.strip()
            else:
                # fallback
                result_data = {"value": values}
            await sio.emit("messageToKit-kitReply", {
                "kit_id": client_id,
                "request_from": from_id,
                "data": result_data,
                "cmd": "trace_vars"
            })
        else:
            print(f"[{timestamp}] Error getting global variables: {err}", flush=True)
            await sio.emit("messageToKit-kitReply", {
                "kit_id": client_id,
                "result": err,
                "request_from": from_id,
                "cmd": "trace_vars"
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
