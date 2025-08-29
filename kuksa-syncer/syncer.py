# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import subprocess
import socketio
import asyncio
import time
import os
import json
from project_utils import ProjectUtils
import cpp_debugger_util

DEFAULT_KIT_SERVER = 'https://kit.digitalauto.tech'
DEFAULT_RUNTIME_NAME = 'CPP'

TIME_TO_KEEP_SUBSCRIBER_ALIVE = 60
TIME_TO_KEEP_RUNNER_ALIVE = 3*60

PERIODIC_GLOBAL_VAR_REPORT = 1


lsOfRunner = []

lsOfApiSubscriber = {}

sio = socketio.AsyncClient()

# Kit-Manager connection for C++ compilation
kit_manager_sio = None
KIT_MANAGER_URL = 'http://127.0.0.1:3090'

# Track C++ processes by client ID
cpp_processes = {}  # {from_id: [{"proc": subprocess.Popen, "pid": int, "type": "cpp"}]}


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

async def stop_client_processes(from_id):
    """Stop all processes belonging to a specific client"""
    if from_id in cpp_processes:
        print(f"Stopping all processes for client {from_id}", flush=True)
        
        for process_info in cpp_processes[from_id]:
            try:
                proc = process_info["proc"]
                pid = process_info["pid"]
                
                if proc is not None:
                    print(f"Terminating process PID {pid} for client {from_id}", flush=True)
                    proc.terminate()
                    
                    # Wait a bit for graceful termination
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=5.0)
                        print(f"Process PID {pid} terminated gracefully", flush=True)
                    except asyncio.TimeoutExpired:
                        print(f"Process PID {pid} didn't terminate gracefully, killing it", flush=True)
                        proc.kill()
                        
            except Exception as e:
                print(f"Error stopping process PID {pid}: {str(e)}", flush=True)
        
        # Clear the client's process list
        del cpp_processes[from_id]
        print(f"Cleared all processes for client {from_id}", flush=True)
        
        # Clean up shared memory
        cpp_debugger_util.cleanup_shm()
        
        return True
    else:
        print(f"No processes found for client {from_id}", flush=True)
        return False

async def capture_app_output(proc, master_id):
    """Capture stdout and stderr from the C++ app and forward to client"""
    try:
        print(f"Starting output capture for process {proc.pid}", flush=True)
        
        # Create tasks for both stdout and stderr
        stdout_task = asyncio.create_task(stream_output(proc.stdout, master_id, "stdout"))
        stderr_task = asyncio.create_task(stream_output(proc.stderr, master_id, "stderr"))
        
        # Monitor the process and wait for it to complete
        while True:
            # Check if process is still running
            if not cpp_debugger_util.is_process_running(proc.pid):
                print(f"Process {proc.pid} has stopped, ending output capture", flush=True)
                break
                
            # Wait a bit before checking again
            await asyncio.sleep(0.5)
        
        # Cancel any remaining tasks
        if not stdout_task.done():
            stdout_task.cancel()
        if not stderr_task.done():
            stderr_task.cancel()
        
        # Try to get the exit code
        try:
            exit_code = proc.returncode if hasattr(proc, 'returncode') else 0
            await send_reply(master_id, f"Application completed with exit code {exit_code}", is_done=True, retcode=exit_code)
        except:
            await send_reply(master_id, "Application completed", is_done=True, retcode=0)
        
    except Exception as e:
        print(f"Error capturing app output: {str(e)}", flush=True)
        await send_reply(master_id, f"Error capturing output: {str(e)}", is_error=True, retcode=1)

async def stream_output(stream, master_id, stream_type):
    """Stream output from a process stream to the client"""
    try:
        print(f"Starting {stream_type} stream capture", flush=True)
        line_count = 0
        
        while True:
            if stream is None:
                print(f"{stream_type} stream is None, stopping", flush=True)
                break
                
            try:
                line = await asyncio.wait_for(stream.readline(), timeout=1.0)
                if not line:
                    print(f"{stream_type} stream closed (no more data)", flush=True)
                    break
                    
                # Decode and send the line to the client
                output_line = line.decode('utf-8', errors='replace').rstrip('\r\n')
                if output_line:  # Only send non-empty lines
                    await send_reply(master_id, f"{output_line}\r\n", is_done=False, retcode=0)
                    line_count += 1
                    if line_count % 10 == 0:  # Log every 10 lines
                        print(f"{stream_type} stream: captured {line_count} lines", flush=True)
                        
            except asyncio.TimeoutError:
                # Timeout is expected, just continue
                continue
            except Exception as e:
                print(f"Error reading from {stream_type} stream: {str(e)}", flush=True)
                break
                
        print(f"{stream_type} stream capture completed after {line_count} lines", flush=True)
                
    except Exception as e:
        print(f"Error in {stream_type} stream capture: {str(e)}", flush=True)


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
    # Save the incoming data payload to payload.json for later comparison/improvement
    # try:
    #     with open("payload.json", "w") as f:
    #         json.dump(data, f, indent=2)
    #     print("Saved incoming payload to payload.json", flush=True)
    # except Exception as e:
    #     print(f"Failed to save payload.json: {str(e)}", flush=True)
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
                    await send_reply(from_id, "App directory cleaned successfully\r\n", is_done=False, retcode=0)
                else:
                    print("✗ Failed to clean app directory", flush=True)
                    await send_reply(from_id, "Failed to clean app directory\r\n", is_error=True, retcode=1)

                # Step 2: Create content in app based on payload data.code
                await send_reply(from_id, "Creating project content...\r\n", is_done=False, retcode=0)
                try:
                    app_path = project_utils.save_from_payload(data)
                    print(f"✓ Project content created successfully", flush=True)
                except Exception as e:
                    print(f"✗ Failed to create project content: {str(e)}", flush=True)
                    await send_reply(from_id, f"Failed to create project content: {str(e)}", is_error=True, retcode=1)
                await send_reply(from_id, "Project content created successfully", is_done=False, retcode=0)

                # Step 3: If C++ app, compile and periodically print out global variables
                compile_ok, compile_msg = await cpp_debugger_util.compile_cpp()
                print(f"Compiling project...\r\n{compile_msg}", flush=True)
                await send_reply(from_id, f"Compiling project...\r\n{compile_msg}\r\n", is_done=False, retcode=0)
                if not compile_ok:
                    await send_reply(from_id, "Compilation failed", is_error=True, is_done=True, retcode=1)
                    return 0
                print("Run app")
                proc, pid, run_msg = await cpp_debugger_util.run_binary()
                await send_reply(from_id, f"Running app...\r\n{run_msg}\r\n", is_done=False, retcode=0)
                
                if proc is not None and pid is not None:
                    # Track this process for this client
                    if from_id not in cpp_processes:
                        cpp_processes[from_id] = []
                    
                    cpp_processes[from_id].append({
                        "proc": proc,
                        "pid": pid,
                        "type": "cpp",
                        "start_time": time.time()
                    })
                    
                    print(f"Tracked C++ process PID {pid} for client {from_id}", flush=True)
                    
                    # Get watch_vars from data if present, else use default
                    watch_vars = data["data"].get("watch_vars", "")
                    print(f"Watch vars: {watch_vars}", flush=True)
                    # Check if watch_vars is empty or only whitespace after trimming
                    if watch_vars is not None and watch_vars.strip():
                        # Start periodic monitoring of global variables
                        asyncio.create_task(cpp_debugger_util.periodic_global_var_report(
                            PERIODIC_GLOBAL_VAR_REPORT, sio, CLIENT_ID, watch_vars, pid, from_id
                        ))
                    
                    # Start capturing and forwarding app output
                    asyncio.create_task(capture_app_output(proc, from_id))
                else:
                    print("✗ Failed to start binary", flush=True)

            except json.JSONDecodeError as e:
                print(f"Invalid JSON in data.code: {str(e)}", flush=True)
                await send_reply(from_id, f"Invalid JSON in data.code: {str(e)}", is_error=True, retcode=1)
            except Exception as e:
                print(f"Error processing project data: {str(e)}", flush=True)
                await send_reply(from_id, f"Error processing project data: {str(e)}", is_error=True, retcode=1)

    elif data["cmd"] == "run_bin_app":
        # Compile and run C++ app, then start periodic global var reporting
        compile_ok, compile_msg = await cpp_debugger_util.compile_cpp()
        await sio.emit("cpp_debugger_compile_result", {
            "kit_id": CLIENT_ID,
            "result": compile_msg,
            "success": compile_ok
        })
        if not compile_ok:
            return 0
        proc, pid, run_msg = await cpp_debugger_util.run_binary()
        await sio.emit("cpp_debugger_run_result", {
            "kit_id": CLIENT_ID,
            "result": run_msg,
            "success": proc is not None
        })
        if proc is not None:
            # Track this process for this client
            if from_id not in cpp_processes:
                cpp_processes[from_id] = []
            
            cpp_processes[from_id].append({
                "proc": proc,
                "pid": pid,
                "type": "cpp",
                "start_time": time.time()
            })
            
            # Start periodic reporting in background
            asyncio.create_task(cpp_debugger_util.periodic_global_var_report(1, sio, CLIENT_ID, "counter", pid))
        return 0
    
    elif data["cmd"] == "stop_python_app":
        # Stop all processes for this client
        from_id = data["request_from"]
        success = await stop_client_processes(from_id)
        
        if success:
            await send_reply(from_id, "All processes stopped successfully\r\n", is_done=True, retcode=0)
        else:
            await send_reply(from_id, "No processes found to stop\r\n", is_done=True, retcode=0)
        return 0        
    
    elif data["cmd"] == "get-runtime-info":
        return 0
        
    elif data["cmd"] == "stop_cpp_app":
        """Stop all C++ processes for a specific client"""
        from_id = data["request_from"]
        success = await stop_client_processes(from_id)
        
        if success:
            await send_reply(from_id, "All C++ processes stopped successfully", is_done=True, retcode=0)
        else:
            await send_reply(from_id, "No C++ processes found to stop", is_done=True, retcode=0)
        return 0
    
    elif data["cmd"] == "set_vars_value":
        """Set global variable values remotely in a running C++ process"""
        from_id = data["request_from"]

        '''
        Sample data["data"]: {
            "counter": 10,
            "foo": 1.23,
            "bar": "Hello, World!"
        }
        '''
        
        # Extract variables from data - variables are stored as key-value pairs
        variables_data = data["data"]
        
        if not variables_data:
            await send_reply(from_id, "No variables data provided", is_error=True, retcode=1)
            return 0
        
        # Find the client's running processes
        if from_id not in cpp_processes or not cpp_processes[from_id]:
            # await send_reply(from_id, "No running C++ processes found\r\n", is_error=True, retcode=1)
            # print(f"No running processes found for client {from_id}", flush=True)
            return 0
        
        # Use the first running process (or iterate through all)
        process_info = cpp_processes[from_id][0]
        pid = process_info["pid"]
        
        print(f"Setting variables for client {from_id} (PID: {pid}): {variables_data}", flush=True)
        
        # Track results for multiple variable operations
        results = []
        success_count = 0
        total_count = 0
        
        # Set multiple variables as key-value pairs
        for var_name, new_value in variables_data.items():
            total_count += 1
            
            # Skip internal fields that aren't actual variables
            if var_name in ["request_id", "timestamp", "session_id"]:
                continue
            
            success, message = await cpp_debugger_util.set_global_variable(var_name, new_value, pid)
            
            # if success:
            #     results.append(f"✓ {var_name} = {new_value}")
            #     success_count += 1
            #     #print(f"Successfully set {var_name} = {new_value} for client {from_id}", flush=True)
            # else:
            #     results.append(f"✗ {var_name}: {message}")
            #     #print(f"Failed to set {var_name} = {new_value} for client {from_id}: {message}", flush=True)
        
        # Send comprehensive response
        # if total_count == 0:
        #     await send_reply(from_id, "No valid variables to set", is_error=True, retcode=1)
        # elif success_count == total_count:
        #     # All variables set successfully
        #     #response_msg = f"All variables set successfully:\n" + "\n".join(results)
        #     await send_reply(from_id, response_msg + "\r\n", is_done=False, retcode=0)
        # elif success_count > 0:
        #     # Partial success
        #     response_msg = f"Partial success ({success_count}/{total_count} variables set):\n" + "\n".join(results)
        #     await send_reply(from_id, response_msg + "\r\n", is_done=False, retcode=0)
        # else:
        #     # All variables failed
        #     #response_msg = f"Failed to set any variables:\n" + "\n".join(results)
        #     #await send_reply(from_id, response_msg + "\r\n", is_error=True, retcode=1)
        
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
