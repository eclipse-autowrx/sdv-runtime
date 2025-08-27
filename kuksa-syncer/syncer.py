# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import signal
import subprocess
import socketio
import asyncio
from subpiper import subpiper
import time
import os
import json
from project_utils import ProjectUtils
import cpp_debugger_util

DEFAULT_KIT_SERVER = 'https://kit.digitalauto.tech'
DEFAULT_RUNTIME_NAME = 'CPP'

TIME_TO_KEEP_SUBSCRIBER_ALIVE = 60
TIME_TO_KEEP_RUNNER_ALIVE = 3*60


lsOfRunner = []

lsOfApiSubscriber = {}

sio = socketio.AsyncClient()

# Kit-Manager connection for C++ compilation
kit_manager_sio = None
KIT_MANAGER_URL = 'http://127.0.0.1:3090'


def is_process_running_nix(process_name):
    """Check if a process with the given name is running on Linux/macOS."""
    try:
        # Using pgrep (more direct)
        process = subprocess.Popen(['pgrep', '-x', process_name], stdout=subprocess.PIPE)
        output, error = process.communicate()
        return len(output) > 0
    except FileNotFoundError:
        # pgrep might not be available, try ps
        process = subprocess.Popen(['ps', '-ax', '-o', 'comm'], stdout=subprocess.PIPE)
        output, error = process.communicate()
        return process_name.lower().encode() in output.lower()

async def send_app_run_reply(master_id, is_done, retcode, content):
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": master_id,
        "cmd": "run_python_app",
        "data": "",
        "isDone": is_done,
        "result": content,
        "code": retcode
    })

async def send_reply(master_id, content, is_error=False, is_done=False, retcode=0, cmd="run_python_app"):
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": master_id,
        "cmd": cmd,
        "data": content,
        "isError": is_error,
        "isDone": is_done,
        "result": content,
        "code": retcode
    })

async def send_cpp_compile_reply(master_id, status, result, is_done, code, data=""):
    """Send C++ compilation status back to the web client"""
    await sio.emit("messageToKit-kitReply", {
        "kit_id": CLIENT_ID,
        "request_from": master_id,
        "cmd": "compile_cpp_app",
        "status": status,
        "data": data,
        "isDone": is_done,
        "result": result,
        "code": code
    })

def process_done(master_id: str, retcode: int):
    asyncio.run(send_app_run_reply(master_id, True, retcode, ""))

def my_stdout_callback(master_id: str, line: str):
    asyncio.run(send_app_run_reply(master_id, False, 0, line + '\r\n'))

def my_stderr_callback(master_id: str, line: str):
    asyncio.run(send_app_run_reply(master_id, False, 0, line + '\r\n'))


@sio.event
async def connect():
    print('Connected to Kit Server ',flush=True)
    await sio.emit("register_kit", {
        "kit_id": CLIENT_ID,
        "name": CLIENT_ID
    })
@sio.event
async def messageToKit(data):
    # print("SYNCER: Command received from server",flush=True)
    # print(data,flush=True)
    from_id = data["request_from"]
    if data["cmd"] == "run_python_app" or data["cmd"] == "run_cpp_app" or data["cmd"] == "run_app":
        # Check if data.code exists and is valid JSON
        if "data" in data and "code" in data["data"]:
            try:
                # Validate JSON format
                code_data = data["data"]["code"]
                json.loads(code_data)  # This will raise an error if invalid JSON

                print(f"Valid JSON code received, processing project data...", flush=True)

                # Initialize ProjectUtils
                project_utils = ProjectUtils()

                # Step 1: Clean up app directory
                print("Step 1: Cleaning up app directory...", flush=True)
                cleanup_success = project_utils.empty_app_directory()
                if cleanup_success:
                    print("✓ App directory cleaned successfully", flush=True)
                    await send_reply(from_id, "App directory cleaned successfully", is_done=True, retcode=0)
                else:
                    print("✗ Failed to clean app directory", flush=True)
                    await send_reply(from_id, "Failed to clean app directory", is_error=True, retcode=1)

                # Step 2: Create content in app based on payload data.code
                await send_reply(from_id, "Creating project content...\r\n", is_done=False, retcode=0)
                try:
                    app_path = project_utils.save_from_payload(data)
                    print(f"✓ Project content created successfully", flush=True)
                except Exception as e:
                    print(f"✗ Failed to create project content: {str(e)}", flush=True)
                    await send_reply(from_id, f"Failed to create project content: {str(e)}", is_error=True, retcode=1)

                # Step 3: If C++ app, compile and periodically print out global variables
                compile_ok, compile_msg = await cpp_debugger_util.compile_cpp()
                print(f"Compiling project...\r\n{compile_msg}", flush=True)
                await send_reply(from_id, f"Compiling project...\r\n{compile_msg}\r\n", is_done=False, retcode=0)
                if not compile_ok:
                    await send_reply(from_id, "Compilation failed", is_error=True, retcode=1)
                    return 0
                print("Run app")
                proc, pid, run_msg = await cpp_debugger_util.run_binary()
                await send_reply(from_id, f"Running app...\r\n{run_msg}\r\n", is_done=False, retcode=0)
                # Get watch_vars from data if present, else use default
                watch_vars = data.get("watch_vars", "counter, temperature, is_active")
                if proc is not None and pid is not None:
                    asyncio.create_task(cpp_debugger_util.periodic_global_var_report(0.5, sio, CLIENT_ID, watch_vars, pid))
                else:
                    print("✗ Failed to start binary", flush=True)

            except json.JSONDecodeError as e:
                print(f"Invalid JSON in data.code: {str(e)}", flush=True)
                await send_reply(from_id, f"Invalid JSON in data.code: {str(e)}", is_error=True, retcode=1)
            except Exception as e:
                print(f"Error processing project data: {str(e)}", flush=True)
                await send_reply(from_id, f"Error processing project data: {str(e)}", is_error=True, retcode=1)

    await send_reply(from_id, "Project content created successfully", is_done=True, retcode=0)
    return 0
    
    if data["cmd"] == "run_bin_app":
        # Compile and run C++ app, then start periodic global var reporting
        compile_ok, compile_msg = await cpp_debugger_util.compile_cpp()
        await sio.emit("cpp_debugger_compile_result", {
            "kit_id": CLIENT_ID,
            "result": compile_msg,
            "success": compile_ok
        })
        if not compile_ok:
            return 0
        proc, run_msg = await cpp_debugger_util.run_binary()
        await sio.emit("cpp_debugger_run_result", {
            "kit_id": CLIENT_ID,
            "result": run_msg,
            "success": proc is not None
        })
        if proc is not None:
            # Start periodic reporting in background
            asyncio.create_task(cpp_debugger_util.periodic_global_var_report(1, sio, CLIENT_ID))
        return 0
    
    elif data["cmd"] == "stop_python_app":
        # print(data["code"])
        for runner in lsOfRunner:
            if runner["request_from"] == data["request_from"]:
                proc = runner["runner"]
                if proc is not None:
                    try:
                        proc.kill()
                        lsOfRunner.remove(runner)
                    except Exception as e:
                        print("Kill proc get error", str(e))
                        await sio.emit("messageToKit-kitReply", {
                            "kit_id": CLIENT_ID,
                            "request_from": data["request_from"],
                            "cmd": "stop_python_app",
                            "result": str(e)
                        })
        return 0
    
    elif data["cmd"] == "get-runtime-info":
        return 0
    
    elif data["cmd"] == "compile_cpp_app":
        """Handle C++ compilation requests by forwarding to Kit-Manager"""
        global kit_manager_sio
        
        try:
            # Initialize Kit-Manager connection if needed
            if kit_manager_sio is None:
                kit_manager_sio = socketio.AsyncClient()
                
                # Set up event handlers for Kit-Manager responses
                @kit_manager_sio.on('compile_cpp_reply')
                async def on_cpp_reply(msg):
                    """Forward C++ compilation responses back to web client"""
                    # Get the original requester from our tracking
                    if hasattr(kit_manager_sio, 'current_requester'):
                        await send_cpp_compile_reply(
                            kit_manager_sio.current_requester,
                            msg.get("status", ""),
                            msg.get("result", ""),
                            msg.get("isDone", False),
                            msg.get("code", 0),
                            msg.get("data", "")
                        )
                
                # Connect to Kit-Manager
                await kit_manager_sio.connect(KIT_MANAGER_URL)
                print(f"Connected to Kit-Manager at {KIT_MANAGER_URL} for C++ compilation", flush=True)
            
            # Track the requester
            kit_manager_sio.current_requester = data["request_from"]
            
            # Forward the compilation request to Kit-Manager
            await kit_manager_sio.emit('compile_cpp', {
                'files': data["data"]["files"],
                'app_name': data["data"]["app_name"],
                'run': data["data"].get("run", False)
            })
            
        except Exception as e:
            print(f"Error connecting to Kit-Manager: {str(e)}", flush=True)
            await send_cpp_compile_reply(
                data["request_from"],
                "err: connection",
                f"Failed to connect to Kit-Manager: {str(e)}\r\n",
                True,
                1
            )
        return 0
    
    return 1

def convertLsOfRunnerToJson(lsOfRunner):
    result = []
    for runner in lsOfRunner:
        result.append({
            "appName": runner["appName"],
            "request_from": runner["request_from"],
            "from": runner["from"]
        })
    return result

def writeCodeToFile(code, filename="main.py"):
    f = open(filename, "w+")
    f.write(code)
    f.close()

async def start_socketio(SERVER):
    print("Connecting to Kit Server: " + SERVER, flush=True)
    await sio.connect(SERVER)
    await sio.wait()


'''
    Faster ticker: 0.3 seconds sleep
        - Report API value back to client
'''
async def ticker_fast():
    while True:
        await asyncio.sleep(0.3)
        # count number of child in lsOfApiSubscriber
        # TODO: Add actual functionality here

'''
    One second ticker
        - Handle old subscriber remove
        - Stop long runner
'''
async def ticker():
    while True:
        await asyncio.sleep(1)

'''
    5 second ticker: 5 seconds sleep
        - Report API value back to client
'''
async def ticker_5s():
    lastLstRunString = ""
    lastNoApiSubscriber = 0
    while True:
        await asyncio.sleep(1)

async def main():
    SERVER = os.getenv('SYNCER_SERVER_URL', DEFAULT_KIT_SERVER) + ""
    global CLIENT_ID
    CLIENT_ID = "RunTime-" + os.getenv('RUNTIME_NAME', DEFAULT_RUNTIME_NAME)
    print("RunTime display name: " + CLIENT_ID, flush=True)

    await asyncio.gather(start_socketio(SERVER), ticker(), ticker_fast(), ticker_5s())

if __name__ == "__main__":
    asyncio.run(main())
