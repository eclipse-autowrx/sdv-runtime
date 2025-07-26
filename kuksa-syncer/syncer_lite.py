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
    """Write code to a file"""
    with open(filename, "w+") as f:
        f.write(code)

async def send_app_run_reply(master_id: str, is_done: bool, retcode: int, content: str):
    """Send reply back to the server"""
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": master_id,
        "cmd": "run_python_app",
        "data": "",
        "isDone": is_done,
        "result": content,
        "code": retcode
    })

def process_done(master_id: str, retcode: int):
    """Callback when process finishes"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply(master_id, True, retcode, ""), loop
            )
        else:
            # Fallback: just print the output
            print(f"[{master_id}] FINISHED: Process completed with return code {retcode}", flush=True)
    except RuntimeError:
        # No event loop, just print
        print(f"[{master_id}] FINISHED: Process completed with return code {retcode}", flush=True)

def my_stdout_callback(master_id: str, line: str):
    """Callback for stdout lines"""
    print(f"stdout: {line}", flush=True)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply(master_id, False, 0, line + '\r\n'), loop
            )
        else:
            # Fallback: just print the output
            print(f"[{master_id}] STDOUT: {line}", flush=True)
    except RuntimeError as e:
        print(f"Error: {e}", flush=True)
        print(f"[{master_id}] STDOUT: {line}", flush=True)

def my_stderr_callback(master_id: str, line: str):
    """Callback for stderr lines"""
    print(f"stderr: {line}", flush=True)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply(master_id, False, 0, line + '\r\n'), loop
            )
        else:
            # Fallback: just print the output
            print(f"[{master_id}] STDERR: {line}", flush=True)
    except RuntimeError as e:
        print(f"Error: {e}", flush=True)
        print(f"[{master_id}] STDERR: {line}", flush=True)

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
    
    # Write code to file
    writeCodeToFile(data["data"]["code"], filename="main.py")
    
    print(f"Running app: {app_name} for request_from: {request_from}", flush=True)

    # Send initial response
    await send_app_run_reply(request_from, False, 0, f"Starting {app_name}...\r\n")
    
    # Start process using pexpect
    print(f"Starting process for {app_name} with request_from: {request_from}", flush=True)
    try:
        proc = pexpect_subpiper(
            master_id=request_from,
            cmd='python3 -u main.py',
            stdout_callback=my_stdout_callback,
            stderr_callback=my_stderr_callback,
            finished_callback=process_done,
            event_loop=asyncio.get_event_loop()
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