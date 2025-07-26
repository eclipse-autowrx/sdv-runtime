# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

"""
Lite version of syncer that only handles remote command execution with real-time output.
Simplified version focusing on core functionality.
"""

import signal
import asyncio
import socketio
import time
import os
import sys
import json
from typing import Dict, List, Optional
from pexpect_util import pexpect_subpiper, PexpectProcess
import re
import pkg_manager

# Configuration
DEFAULT_KIT_SERVER = 'https://kit.digitalauto.tech'
DEFAULT_RUNTIME_NAME = 'LiteRuntime'
BORKER_IP = '127.0.0.1'
BROKER_PORT = 55555

# Global variables
CLIENT_ID = None
sio = socketio.AsyncClient()
lsOfRunner: List[Dict] = []
TIME_TO_KEEP_RUNNER_ALIVE = 3 * 60  # 3 minutes

def writeCodeToFile(code: str, filename: str = "main.py"):
    """Write code to a file with global variable monitoring"""
    # Extract global variables from the code
    global_vars = extract_global_variables(code)
    
    # Create monitoring code
    monitoring_code = create_monitoring_code(global_vars)
    
    # Combine original code with monitoring
    enhanced_code = monitoring_code + "\n" + code
    
    with open(filename, "w+") as f:
        f.write(enhanced_code)
    
    return global_vars

def extract_global_variables(code: str) -> List[str]:
    """Extract global variable names from Python code"""
    import ast
    
    try:
        tree = ast.parse(code)
        global_vars = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_vars.append(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                global_vars.append(node.target.id)
        
        # Remove duplicates and filter out common names
        filtered_vars = []
        common_names = {'i', 'j', 'k', 'temp', 'tmp', 'var', 'val', 'data', 'result', 'output'}
        for var in set(global_vars):
            if var not in common_names and not var.startswith('_'):
                filtered_vars.append(var)
        
        return filtered_vars
    except Exception as e:
        print(f"Error extracting variables: {e}", flush=True)
        return []

def create_monitoring_code(global_vars: List[str]) -> str:
    """Create code to monitor global variables"""
    if not global_vars:
        return ""
    
    monitoring_code = f"""
import json
import time
import threading
import sys

# Global variable monitoring
_monitored_vars = {global_vars}
_monitoring_active = True

def _monitor_globals():
    while _monitoring_active:
        try:
            globals_data = {{}}
            for var_name in _monitored_vars:
                if var_name in globals():
                    value = globals()[var_name]
                    try:
                        # Try to serialize the value
                        if isinstance(value, (int, float, str, bool, list, dict, tuple)):
                            globals_data[var_name] = value
                        else:
                            globals_data[var_name] = str(type(value).__name__) + ': ' + str(value)[:100]
                    except:
                        globals_data[var_name] = str(type(value).__name__)
                else:
                    globals_data[var_name] = "undefined"
            
            # Print in a format that can be captured by pexpect
            print(f"GLOBALS_UPDATE: {{json.dumps(globals_data)}}", flush=True)
        except Exception as e:
            print(f"GLOBALS_ERROR: {{str(e)}}", flush=True)
        
        time.sleep(1)  # Update every second

# Start monitoring in a separate thread
_monitor_thread = threading.Thread(target=_monitor_globals, daemon=True)
_monitor_thread.start()

# Function to stop monitoring
def stop_global_monitoring():
    global _monitoring_active
    _monitoring_active = False
"""
    
    return monitoring_code

async def send_app_run_reply(master_id: str, is_done: bool, retcode: int, content: str):
    """Send reply back to the server"""
    clean_content = remove_ansi_codes(content)
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": master_id,
        "cmd": "run_python_app",
        "data": "",
        "isDone": is_done,
        "result": clean_content,
        "code": retcode
    })

def process_done_factory(loop):
    def process_done(master_id: str, retcode: int):
        """Callback when process finishes"""
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply(master_id, True, retcode, ""), loop
            )
        else:
            print(f"[{master_id}] FINISHED: Process completed with return code {retcode}", flush=True)
    return process_done

def my_stdout_callback_factory(loop):
    def my_stdout_callback(master_id: str, line: str):
        print(f"stdout: {line}", flush=True)
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply(master_id, False, 0, line + '\r\n'), loop
            )
        else:
            print(f"[{master_id}] STDOUT: {line}", flush=True)
    return my_stdout_callback

def my_stderr_callback_factory(loop):
    def my_stderr_callback(master_id: str, line: str):
        print(f"stderr: {line}", flush=True)
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply(master_id, False, 0, line + '\r\n'), loop
            )
        else:
            print(f"[{master_id}] STDERR: {line}", flush=True)
    return my_stderr_callback

def my_globals_callback_factory(loop):
    def my_globals_callback(master_id: str, line: str):
        """Callback for global variable updates"""
        if line.startswith("GLOBALS_UPDATE: "):
            try:
                # Extract the JSON data
                json_data = line[16:]  # Remove "GLOBALS_UPDATE: " prefix
                globals_data = json.loads(json_data)
                
                # Send global variables update to client
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        send_globals_update(master_id, globals_data), loop
                    )
            except Exception as e:
                print(f"Error parsing globals data: {str(e)}", flush=True)
        elif line.startswith("GLOBALS_ERROR: "):
            error_msg = line[15:]  # Remove "GLOBALS_ERROR: " prefix
            print(f"Globals monitoring error: {error_msg}", flush=True)
    return my_globals_callback

async def send_globals_update(master_id: str, globals_data: Dict):
    """Send global variables update to the client"""
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": master_id,
        "cmd": "globals_update",
        "data": globals_data,
        "result": "Global variables updated"
    })

def remove_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

@sio.event
async def connect():
    """Handle connection to server"""
    print('Connected to Kit Server', flush=True)
    await sio.emit("register_kit", {
        "kit_id": CLIENT_ID,
        "name": CLIENT_ID
    })

@sio.event
async def messageToKit(data):
    """Handle incoming messages from server"""
    print(f"Received command: {data.get('cmd', 'unknown')}", flush=True)
    
    if data["cmd"] == "run_python_app":
        await handle_run_python_app(data)
    elif data["cmd"] == "stop_python_app":
        await handle_stop_python_app(data)
    elif data["cmd"] == "get-runtime-info":
        await handle_get_runtime_info(data)
    elif data["cmd"] == "list_python_packages":
        await handle_list_python_packages(data)
    elif data["cmd"] == "install_python_packages":
        await handle_install_python_packages(data)
    else:
        print(f"Unknown command: {data.get('cmd', 'unknown')}", flush=True)

async def handle_run_python_app(data):
    """Handle run_python_app command"""
    # Check if we have code
    if "code" not in data["data"]:
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "run_python_app",
            "result": "Error: Missing code",
            "data": ""
        })
        return
    
    # Get app name
    app_name = data["data"].get("name", "App")
    request_from = data["request_from"]
    
    # Write code to file with global variable monitoring
    global_vars = writeCodeToFile(data["data"]["code"], filename="main.py")
    
    print(f"Running app: {app_name} for request_from: {request_from}", flush=True)
    print(f"Monitoring global variables: {global_vars}", flush=True)

    # Send initial response
    await send_app_run_reply(request_from, False, 0, f"Starting {app_name}...\r\n")
    if global_vars:
        await send_app_run_reply(request_from, False, 0, f"Monitoring global variables: {', '.join(global_vars)}\r\n")
    
    # Start process using pexpect
    print(f"Starting process for {app_name} with request_from: {request_from}", flush=True)
    try:
        loop = asyncio.get_event_loop()
        proc = pexpect_subpiper(
            master_id=request_from,
            cmd='python3 -u main.py',
            stdout_callback=my_stdout_callback_factory(loop),
            stderr_callback=my_stderr_callback_factory(loop),
            globals_callback=my_globals_callback_factory(loop),
            finished_callback=process_done_factory(loop),
            event_loop=loop
        )
        
        # Store runner info
        lsOfRunner.append({
            "appName": app_name,
            "runner": proc,
            "request_from": request_from,
            "from": time.time()
        })
        
        print(f"Process started with PID: {proc.get_info().pid}", flush=True)
        await send_app_run_reply(request_from, False, 0, f"Process started with PID: {proc.get_info().pid}\r\n")
        
    except Exception as e:
        error_msg = f"Failed to start process: {str(e)}"
        print(error_msg, flush=True)
        await send_app_run_reply(request_from, True, 1, error_msg)

async def handle_stop_python_app(data):
    """Handle stop_python_app command"""
    request_from = data["request_from"]
    
    # Find and kill the process
    for runner in lsOfRunner[:]:  # Copy list to avoid modification during iteration
        if runner["request_from"] == request_from:
            proc = runner["runner"]
            if proc and proc.is_alive():
                try:
                    proc.kill()
                    lsOfRunner.remove(runner)
                    await sio.emit("messageToKit-kitReply", {
                        "kit_id": CLIENT_ID,
                        "request_from": request_from,
                        "cmd": "stop_python_app",
                        "result": "Process stopped successfully"
                    })
                except Exception as e:
                    await sio.emit("messageToKit-kitReply", {
                        "kit_id": CLIENT_ID,
                        "request_from": request_from,
                        "cmd": "stop_python_app",
                        "result": f"Error stopping process: {str(e)}"
                    })
            else:
                lsOfRunner.remove(runner)

async def handle_get_runtime_info(data):
    """Handle get-runtime-info command"""
    request_from = data["request_from"]
    
    # Convert runner list to JSON-serializable format
    runner_info = []
    for runner in lsOfRunner:
        runner_info.append({
            "appName": runner["appName"],
            "request_from": runner["request_from"],
            "from": runner["from"],
            "pid": runner["runner"].get_info().pid if runner["runner"] else None,
            "state": runner["runner"].get_info().state.value if runner["runner"] else "unknown"
        })
    
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": request_from,
        "cmd": "get-runtime-info",
        "data": {
            "lsOfRunner": runner_info,
            "total_runners": len(lsOfRunner)
        }
    })

async def handle_list_python_packages(data):
    """Handle list_python_packages command"""
    request_from = data["request_from"]
    
    try:
        pkgs = pkg_manager.listPkg()
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": request_from,
            "cmd": "list_python_packages",
            "data": pkgs,
            "result": "Successful"
        })
    except Exception as e:
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": request_from,
            "cmd": "list_python_packages",
            "result": f"Error: {str(e)}"
        })

async def handle_install_python_packages(data):
    """Handle install_python_packages command"""
    request_from = data["request_from"]
    
    if "data" not in data:
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": request_from,
            "cmd": "install_python_packages",
            "result": "Error: Missing package data",
            "data": ""
        })
        return
    
    msg = data["data"]
    
    # Send initial response
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": request_from,
        "cmd": "install_python_packages",
        "result": "Installing",
        "data": f"Installing packages: {msg}\n"
    })
    
    try:
        response = await pkg_manager.installPkg(data["data"])
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": request_from,
            "cmd": "install_python_packages",
            "result": "Successful",
            "data": str(response)
        })
    except Exception as e:
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": request_from,
            "cmd": "install_python_packages",
            "result": f"Error: {str(e)}",
            "data": ""
        })

async def cleanup_old_runners():
    """Clean up old runners that have been running too long"""
    while True:
        await asyncio.sleep(1)
        
        current_time = time.time()
        for runner in lsOfRunner[:]:  # Copy list to avoid modification during iteration
            time_passed = current_time - runner["from"]
            if time_passed > TIME_TO_KEEP_RUNNER_ALIVE:
                try:
                    proc = runner["runner"]
                    if proc and proc.is_alive():
                        proc.kill()
                    lsOfRunner.remove(runner)
                    print(f"Cleaned up old runner: {runner['appName']}", flush=True)
                except Exception as e:
                    print(f"Error cleaning up runner: {str(e)}", flush=True)

async def start_socketio(server_url: str):
    """Start socketio connection"""
    print(f"Connecting to Kit Server: {server_url}", flush=True)
    await sio.connect(server_url)
    await sio.wait()

async def main():
    """Main function"""
    global CLIENT_ID
    
    # Get configuration from environment
    server_url = os.getenv('SYNCER_SERVER_URL', DEFAULT_KIT_SERVER)
    CLIENT_ID = "Runtime-" + os.getenv('RUNTIME_NAME', DEFAULT_RUNTIME_NAME)
    
    print(f"Lite Runtime starting with ID: {CLIENT_ID}", flush=True)
    print(f"Connecting to server: {server_url}", flush=True)
    
    # Start cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_runners())
    
    # Start socketio connection
    try:
        await start_socketio(server_url)
    except KeyboardInterrupt:
        print("Shutting down...", flush=True)
    except Exception as e:
        print(f"Error: {str(e)}", flush=True)
    finally:
        # Clean up all running processes
        for runner in lsOfRunner:
            try:
                proc = runner["runner"]
                if proc and proc.is_alive():
                    proc.kill()
            except Exception as e:
                print(f"Error killing process: {str(e)}", flush=True)
        
        cleanup_task.cancel()
        print("Lite Runtime stopped", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user", flush=True)
    except Exception as e:
        print(f"Fatal error: {str(e)}", flush=True)
        sys.exit(1) 