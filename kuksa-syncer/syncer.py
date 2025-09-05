# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import signal
import subprocess
from kuksa_client.grpc.aio import VSSClient
from kuksa_client.grpc import VSSClient as KClient
from kuksa_client.grpc import Datapoint
from kuksa_client.grpc import VSSClientError
from kuksa_client.grpc import MetadataField
from kuksa_client.grpc import EntryType
import socketio
import asyncio
from subpiper import subpiper
import time
import os
import sys
import json
from json_array_patch import apply_global_patch
from project_utils import create_project_from_json

# Apply global JSON patch for array serialization
apply_global_patch()

from vehicle_model_manager import generate_vehicle_model, revert_vehicle_model
import pkg_manager

BORKER_IP = '127.0.0.1'
BROKER_PORT = 55555

DEFAULT_KIT_SERVER = 'https://kit.digitalauto.tech'
DEFAULT_RUNTIME_NAME = 'MyRuntime'
DEFAULT_RUNTIME_PREFIX = 'Runtime-'

TIME_TO_KEEP_SUBSCRIBER_ALIVE = 60
TIME_TO_KEEP_RUNNER_ALIVE = 3*60


lsOfRunner = []

lsOfApiSubscriber = {}

sio = socketio.AsyncClient()

client = VSSClient(BORKER_IP, BROKER_PORT)

mock_signal_path = "/home/dev/ws/mock/signals.json"

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

async def send_app_deploy_reply(master_id, content, is_finish, cmd="deploy-request"):
    await sio.emit("messageToKit-kitReply", {
        "token": "12a-124-45634-12345-1swer",
        "request_from": master_id,
        "cmd": cmd,
        "data": "",
        "result": content,
        "is_finish": is_finish
    })

main_loop = None

def process_done(master_id: str, retcode: int):
    if main_loop:
        asyncio.run_coroutine_threadsafe(send_app_run_reply(master_id, True, retcode, ""), main_loop)

def my_stdout_callback(master_id: str, line: str):
    if main_loop:
        asyncio.run_coroutine_threadsafe(send_app_run_reply(master_id, False, 0, line + '\r\n'), main_loop)

def my_stderr_callback(master_id: str, line: str):
    if main_loop:
        asyncio.run_coroutine_threadsafe(send_app_run_reply(master_id, False, 0, line + '\r\n'), main_loop)

async def install_dependencies(request_from):
    """Install dependencies from requirements.txt."""
    requirements_path = "app/requirements.txt"
    if not os.path.exists(requirements_path):
        return True

    await send_app_run_reply(request_from, False, 0, "Installing dependencies from requirements.txt...\r\n")

    # Using asyncio.create_subprocess_exec to run pip
    process = await asyncio.create_subprocess_exec(
        'pip', 'install', '-r', requirements_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Stream stdout
    async def stream_output(stream, callback):
        while True:
            line = await stream.readline()
            if not line:
                break
            callback(request_from, line.decode())

    # Create tasks to stream stdout and stderr
    stdout_task = asyncio.create_task(stream_output(process.stdout, my_stdout_callback))
    stderr_task = asyncio.create_task(stream_output(process.stderr, my_stdout_callback))

    # Wait for the process to complete and for the streams to be fully read
    await asyncio.gather(stdout_task, stderr_task)
    
    return_code = await process.wait()

    if return_code != 0:
        await send_app_run_reply(request_from, False, return_code, "Failed to install dependencies.\r\n")
        return False
    else:
        await send_app_run_reply(request_from, False, 0, "Dependencies installed successfully.\r\n")
        return True


@sio.event
async def connect():
    print('Connected to Kit Server ',flush=True)
    await sio.emit("register_kit", {
        "kit_id": CLIENT_ID,
        "name": CLIENT_ID
    })

def wait_for_databroker_ready(max_attempts=10, sleep_time=0.5):
    for attempt in range(max_attempts):
        try:
            with KClient(BORKER_IP, BROKER_PORT) as temp_client:
                # Test connection by fetching server info or metadata
                temp_client.get_server_info()
            print("Databroker is ready.")
            return True
        except VSSClientError as e:
            if "Connection refused" in str(e):
                print(f"Databroker not ready yet (attempt {attempt + 1}/{max_attempts}). Retrying...")
                time.sleep(sleep_time)
            else:
                raise
    raise Exception("Databroker failed to become ready after retries.")

async def install_dependencies(request_from):
    """Install dependencies from requirements.txt."""
    requirements_path = "app/requirements.txt"
    if not os.path.exists(requirements_path):
        return True

    await send_app_run_reply(request_from, False, 0, "Installing dependencies from requirements.txt...\r\n")

    process = await asyncio.create_subprocess_exec(
        'pip', 'install', '-r', requirements_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def stream_output(stream, callback):
        while True:
            line = await stream.readline()
            if not line:
                break
            # The callbacks use asyncio.run, which is not ideal inside an already running loop.
            # A better approach would be to pass the loop and use loop.call_soon_threadsafe
            # or simply await the callback if it were async.
            # For now, we'll stick to the existing callback structure.
            callback(request_from, line.decode())

    stdout_task = asyncio.create_task(stream_output(process.stdout, my_stdout_callback))
    stderr_task = asyncio.create_task(stream_output(process.stderr, my_stdout_callback))

    await asyncio.gather(stdout_task, stderr_task)
    return_code = await process.wait()

    if return_code != 0:
        await send_app_run_reply(request_from, False, return_code, "Failed to install dependencies.\r\n")
        return False
    else:
        await send_app_run_reply(request_from, False, 0, "Dependencies installed successfully.\r\n")
        return True

@sio.event
async def messageToKit(data):
    # print("SYNCER: Command received from server",flush=True)
    # print(data,flush=True)
    if data["cmd"] in ("deploy_request", "deploy-request"):
        print("Receive deploy_request...")
        request_from =  data["request_from"]
        # your code to run app
        await send_app_deploy_reply(request_from, "Receive deploy request \r\n", False, data["cmd"])
        await asyncio.sleep(1)
        writeCodeToFile(data["code"], filename="main.py")
        await send_app_deploy_reply(request_from, "Check syntax.... \r\n", False, data["cmd"])
        # your_code_to_check_velocitas_code(data["code"])
        await asyncio.sleep(3)
        await send_app_deploy_reply(request_from, "Build docker image \r\n", False, data["cmd"])
        # your_code_to_build_docker(data["code"])
        await asyncio.sleep(3)
        await send_app_deploy_reply(request_from, "Send to HW kit \r\n", False, data["cmd"])
        # your_code...()
        await asyncio.sleep(3)
        await send_app_deploy_reply(request_from, "Run docker on HW kit \r\n", False, data["cmd"])
        # your_code...()
        await asyncio.sleep(3)
        await send_app_deploy_reply(request_from, "Deploy done! \r\n", True, data["cmd"])
        return 0
    
    if data["cmd"] == "subscribe_apis":
        if data["apis"] is not None:
            apis = data["apis"]
            master_id=data["request_from"]
            lsOfApiSubscriber[master_id] = {
                "from": time.time(),
                "apis": apis
            }

            if isinstance(apis,list) and len(apis)>0:
                try:
                    appendMockSignal(apis)
                except Exception as e:
                    print("Error: ", str(e))
                    pass
            
            await sio.emit("messageToKit-kitReply", {
                "kit_id": CLIENT_ID,
                "request_from": data["request_from"],
                "cmd": "subscribe_apis",
                "result": "Successful"
            })
        return 0
    
    if data["cmd"] == "unsubscribe_apis":
        master_id=data["request_from"]
        del lsOfApiSubscriber[master_id]
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "unsubscribe_apis",
            "result": "Successful"
        })
        return 0
    
    if data["cmd"] == "list_mock_signal":
        mock_signal = listMockSignal()
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "list_mock_signal",
            "data": mock_signal,
            "result": "Successful"
        })
        return 0
    
    if data["cmd"] == "set_mock_signals":
        modifyMockSignal(data["data"])
        mock_signal = listMockSignal()
        # print("After modifying:")
        # print(mock_signal)
        restartMockProvider()
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "set_mock_signals",
            "data": mock_signal,
            "result": "Successful"
        })
        return 0
    
    if data["cmd"] == "write_signals_value":
        writeSignalsValue(data["data"])
        # mock_signal = listMockSignal()
        mock_signal = {}
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "write_signals_value",
            "data": mock_signal,
            "result": "Successful"
        })
        return 0
    
    if data["cmd"] == "reset_signals_value":
        with open(mock_signal_path) as f:
            signal_list = json.load(f)
        writeSignalsValue(str(signal_list))
        mock_signal = listMockSignal()
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "reset_signals_value",
            "data": mock_signal,
            "result": "Successful"
        })
        return 0
    
    if data["cmd"] == "generate_vehicle_model":
        print("receive reauest generate_vehicle_model")
        # print(data["data"])
        # print type of data["data"]
        # print(type(data["data"]))

        try:
            await sio.emit("messageToKit-kitReply", {
                "kit_id": CLIENT_ID,
                "request_from": data["request_from"],
                "cmd": "revert_vehicle_model",
                "result": "Start to rebuild vehicle model...\r\n"
            })
            stopMockService()
            generate_vehicle_model(json.dumps(data["data"]))
            
            time.sleep(0.5)
            if not os.environ.get('DISABLE_DATABROKER'):
                # Check is databroker app running or not
                if is_process_running_nix("databroker"):
                    print("databroker is running")
                else:
                    print("databroker is not running")
                    raise Exception("Databroker is not running")
                
                # Wait until databroker is fully ready (port is listening)
                wait_for_databroker_ready()
            
            modifyMockSignal([""])
            time.sleep(0.5)
            startMockService()
            await sio.emit("messageToKit-kitReply", {
                "kit_id": CLIENT_ID,
                "request_from": data["request_from"],
                "cmd": "generate_vehicle_model",
                "result": "Generate new model Successful"
            })
            return 0
        except Exception as e:
            # print("generate_vehicle_model Error: ", str(e))
            
            await sio.emit("messageToKit-kitReply", {
                "kit_id": CLIENT_ID,
                "request_from": data["request_from"],
                "cmd": "generate_vehicle_model",
                "result": "Error: generate_vehicle_model Failed: " + str(e) + "\r\nRevert back to default model" 
            })
            revert_vehicle_model();
            return 0

    if data["cmd"] == "revert_vehicle_model":
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "revert_vehicle_model",
            "result": "Start to revert to default vehicle model...\r\n"
        })
        stopMockService()
        revert_vehicle_model()
        time.sleep(0.5)
        startMockService()
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "revert_vehicle_model",
            "result": "Revert to default Vehicle Model Successful\r\n"
        })
        return 0  
    
    if data["cmd"] == "list_python_packages":
        pkgs = pkg_manager.listPkg()
        # print(pkgs,flush=True)
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "list_python_packages",
            "data": pkgs,
            "result": "Successful"
        })
        return 0
        
    if data["cmd"] == "install_python_packages":
        msg = data["data"]
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "install_python_packages",
            "result": "Installing",
            "data": f"Installing packages: {msg}\n"
        })
        # print(msg,flush=True)
        response = await pkg_manager.installPkg(data["data"])
        # await asyncio.sleep(1)
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "install_python_packages",
            "result": "Successful",
            "data": str(response)
        }) 

        return 0  

    if data["cmd"] == "run_python_app":
        # check do we have data["data"]["code"]
        if "code" not in data["data"]:
            await sio.emit("messageToKit-kitReply", {
                "kit_id": CLIENT_ID,
                "request_from": data["request_from"],
                "cmd": "run_python_app",
                "result": "Error: Missing code",
                "data": ""
            })
            return 1
        appName = "App name"
        if "name" in data["data"]:
            appName = data["data"]["name"]
       
        code_data = data["data"]["code"]
        cmd_to_run = 'python -u main.py'
        is_project = False
        try:
            # Try to parse the code as JSON
            json.loads(code_data)
            is_project = True
            create_project_from_json(code_data, base_dir="app")
            cmd_to_run = 'python -u app/main.py'
        except json.JSONDecodeError:
            # Not a JSON, treat as raw code
            writeCodeToFile(code_data, filename="main.py")

        if is_project:
            install_success = await install_dependencies(data["request_from"])
            if not install_success:
                return 1  # Stop execution if dependencies failed to install

        # try:
        usedAPIs = data["usedAPIs"]
        if isinstance(usedAPIs,list) and len(usedAPIs)>0:
            try:
                appendMockSignal(usedAPIs)
            except Exception as e:
                print("Error: ", str(e))
                pass
        # except Exception as e:
        #     print("Fail to appendMockSignal for usedAPIs")
        #     print(str(e))

        proc = subpiper(
            master_id=data["request_from"],
            cmd=cmd_to_run,
            stdout_callback=my_stdout_callback,
            stderr_callback=my_stdout_callback,
            finished_callback=process_done
        )
        lsOfRunner.append({
            "appName": appName,
            "runner": proc,
            "request_from": data["request_from"],
            "from": time.time()
        })
        return 0
    
    if data["cmd"] == "run_bin_app":
        if "data" not in data:
            await sio.emit("messageToKit-kitReply", {
                "kit_id": CLIENT_ID,
                "request_from": data["request_from"],
                "cmd": "run_bin_app",
                "result": "Error: Missing app name",
                "data": ""
            }) 
            return 1
        app_name = data["data"]
        if os.path.isfile(f'/home/dev/output/{app_name}'):
            try:
                usedAPIs = data["usedAPIs"]
                if isinstance(usedAPIs,list) and len(usedAPIs)>0:
                    try:
                        appendMockSignal(usedAPIs)
                    except Exception as e:
                        print("Error: ", str(e))
                        pass
            except Exception as e:
                print("Fail to appendMockSignal for usedAPIs")
                print(str(e))
                
            await asyncio.sleep(0.5)
            proc = subpiper(
                master_id=data["request_from"],
                cmd=f'/home/dev/output/{app_name}',
                stdout_callback=my_stdout_callback,
                stderr_callback=my_stdout_callback,
                finished_callback=process_done
            )
            lsOfRunner.append({
                "appName": app_name,
                "runner": proc,
                "request_from": data["request_from"],
                "from": time.time()
            })
        else:
            await sio.emit("messageToKit-kitReply", {
                "kit_id": CLIENT_ID,
                "request_from": data["request_from"],
                "cmd": "run_bin_app",
                "result": "Failed: Rust app not found",
                "data": ""
            }) 
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
        await sio.emit("messageToKit-kitReply", {
            "kit_id": CLIENT_ID,
            "request_from": data["request_from"],
            "cmd": "get-runtime-info",
            "data": {
                "lsOfRunner": convertLsOfRunnerToJson(lsOfRunner),
                "lsOfApiSubscriber": lsOfApiSubscriber
            }
            
        })
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

def listMockSignal():
    if os.path.exists(mock_signal_path):
        with open(mock_signal_path,'r') as file:
            mock_signal_array = json.load(file)
            return mock_signal_array
    else:
        print("No signals found.",flush=True)

def stopMockService():
    pid_file = "/home/dev/mockprovider.pid"
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, signal.SIGKILL)
            print(f"mockprovider with PID {pid} has been killed.", flush=True)
        except ProcessLookupError:
            print(f"No process found with PID {pid}.", flush=True)
            pass
    else:
        print(f"mockprovider pid file at '{pid_file}' does not exist.", flush=True)

def startMockService():
    try:
        print("Starting mock provider...", flush=True)
        subprocess.Popen(["python", "/home/dev/ws/mock/mockprovider.py"])
        print("mock provider started.", flush=True)
    except Exception as e:
        print(f"Error starting mock provider: {e}", flush=True)
        return 1

def restartMockProvider():
    stopMockService()
    time.sleep(0.5)
    startMockService()

def appendMockSignal(signals):
    if signals is None or len(signals) <=0:
        return 0
    hasNew = False
    with KClient(BORKER_IP, BROKER_PORT) as kclient:
        with open(mock_signal_path,'r+') as f:
            content = f.read()
            # print(f"mock file content")
            if len(content) == 0 :
                content = "[]"
            # print(content)
            cur_mocks = json.loads(content)
            cur_mock_names = []
            for cur_mock in cur_mocks:
                cur_mock_names.append(cur_mock["signal"])
            # print("cur_mock_names", cur_mock_names)
            for run_signal in signals:
                if run_signal not in cur_mock_names:
                    try: 
                        if kclient.get_metadata([run_signal, ]) is not None:
                            hasNew = True
                            print(f">>> Append new mock signal {run_signal}")
                            cur_mock_names.append(run_signal)
                            cur_mocks.append({
                                "signal":  run_signal,
                                "value": "0"
                            })
                    except Exception as e:
                        print(e,flush=True)
                    
            if hasNew:
                f.seek(0)
                json.dump(cur_mocks,f,indent=4)
                f.truncate()

    if hasNew:
        restartMockProvider()
        
    return 0

def modifyMockSignal(input_str):
    with open(mock_signal_path,'w') as file:
        json_string = json.dumps(input_str)
        input_signals = json.loads(json_string)
        final_signals = []
        with KClient(BORKER_IP, BROKER_PORT) as kclient:
            for signal in input_signals:
                try: 
                    if kclient.get_metadata([signal['signal'], ]) is not None:
                        final_signals.append(signal)
                except Exception as e:
                    print(e,flush=True)
        
        file.seek(0)
        json.dump(final_signals,file,indent=4)
        file.truncate()
        return 0

def writeSignalsValue(input_str):
    json_str = json.dumps(input_str)
    signal_values = json.loads(json_str)
    with KClient(BORKER_IP, BROKER_PORT) as kclient:
        for path,value in signal_values.items():
            try:
                meta_data = kclient.get_metadata([path], MetadataField.ENTRY_TYPE)
                entry_type = meta_data[path].entry_type
                if entry_type == EntryType.ACTUATOR:
                    try:
                        target_value = {path: Datapoint(value)}
                        kclient.set_target_values(target_value)
                        # print(target_value,flush=True)
                    except Exception as e:
                        print("Error occured when writing target values: " + str(e),flush=True)
                elif entry_type == EntryType.SENSOR:
                    try:
                        current_value = {path: Datapoint(value)}
                        kclient.set_current_values(current_value)
                        # print(current_value, flush=True)
                    except Exception as e:
                        print("Error occured when writing current values: " + str(e), flush=True)
                else:
                    print("The signal path provided was not actuator or sensor", flush=True)
            except Exception as e:
                print("Error occured when writing signal values: " + str(e),flush=True)

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

        if len(lsOfApiSubscriber) <= 0:
            continue
        if not client.connected:
            await client.connect()
            print("Kuksa connected", client.connected)
            continue

        try:
            for client_id in lsOfApiSubscriber:
                apis = lsOfApiSubscriber[client_id]["apis"]
                if len(apis) > 0:
                    # print(f"read apis {apis}")
                    # start_time = time.time()
                    current_values_dict = {}
                    for api in apis:
                        try:
                            current_values = await client.get_current_values([api])
                            current_values_dict.update(current_values)
                        except Exception as e:
                            # print("get_current_values Error: ", str(e))
                            pass
                    result = {}
                    for api in current_values_dict:
                        if current_values_dict[api] is not None:
                            value = current_values_dict[api].value
                            # Convert array types to list for JSON serialization
                            if hasattr(value, 'values') and hasattr(value.values, '__iter__'):
                                result[api] = list(value.values)
                            elif hasattr(value, 'tolist'):
                                result[api] = value.tolist()
                            else:
                                result[api] = value
                        else:
                            result[api] = None
                    # elapsed_time = time.time() - start_time
                    # print(f"Execution time of one subscriber read: {elapsed_time:.6f} seconds")
                    await sio.emit("messageToKit-kitReply", {
                        "kit_id": CLIENT_ID,
                        "request_from": client_id,
                        "cmd":"apis-value",
                        "result": result
                    })
        except VSSClientError as vssErr:
            print("Error Code:" , str(vssErr),flush=True)
        except Exception as e:
            # pass
            print("Error:" , str(e),flush=True)

'''
    One second ticker
        - Handle old subscriber remove
        - Stop long runner
'''
async def ticker():
    print("Kuksa connected", client.connected)
    while True:
        await asyncio.sleep(1)

        # remove old subscriber
        if len(list(lsOfApiSubscriber.keys())) > 0:
            for client_id in list(lsOfApiSubscriber.keys()):
                subscriber = lsOfApiSubscriber[client_id]
                timePass = time.time() - subscriber["from"]
                if timePass > TIME_TO_KEEP_SUBSCRIBER_ALIVE:
                    del lsOfApiSubscriber[client_id]


        # remove old subscriber
        if len(lsOfRunner) > 0:
            for runner in lsOfRunner:
                timePass = time.time() - runner["from"]
                if timePass > TIME_TO_KEEP_RUNNER_ALIVE:
                    try:
                        runner["runner"].kill()
                        lsOfRunner.remove(runner)
                    except Exception as e:
                        print(str(e))

'''
    5 second ticker: 5 seconds sleep
        - Report API value back to client
'''
async def ticker_5s():
    lastLstRunString = ""
    lastNoApiSubscriber = 0
    while True:
        await asyncio.sleep(1)
        noSubscriber = len(list(lsOfApiSubscriber.keys()))
        if noSubscriber <= 0:
            continue
        try:
            lstRunString = json.dumps(convertLsOfRunnerToJson(lsOfRunner))
            if lastLstRunString != lstRunString or lastNoApiSubscriber != noSubscriber:
                lastLstRunString = lstRunString
                lastNoApiSubscriber = noSubscriber

                await sio.emit("report-runtime-state", {
                    "kit_id": CLIENT_ID,
                    "data": {
                        "noOfRunner": len(lsOfRunner),
                        "noOfApiSubscriber": noSubscriber,
                    }
                })

                for client_sid in lsOfApiSubscriber:
                    # Convert lsOfApiSubscriber to JSON-safe format
                    safe_api_subscriber = {}
                    for key, val in lsOfApiSubscriber.items():
                        safe_api_subscriber[key] = {
                            "apis": val.get("apis", []),
                            "keep_alive": val.get("keep_alive", 0)
                        }
                    await sio.emit("messageToKit-kitReply", {
                            "kit_id": CLIENT_ID,
                            "request_from": client_sid,
                            "cmd":"report-runtime-state",
                            "data": {
                                "lsOfRunner": convertLsOfRunnerToJson(lsOfRunner),
                                "lsOfApiSubscriber": safe_api_subscriber
                            }
                        })
        except Exception as e:
            print("Error: ", str(e))

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    SERVER = os.getenv('SYNCER_SERVER_URL', DEFAULT_KIT_SERVER) + ""
    global CLIENT_ID
    runtime_prefix = os.getenv('RUNTIME_PREFIX', DEFAULT_RUNTIME_PREFIX)
    runtime_name = os.getenv('RUNTIME_NAME', DEFAULT_RUNTIME_NAME)
    CLIENT_ID = runtime_prefix + runtime_name
    print("RunTime display name: " + CLIENT_ID, flush=True)

    await client.connect()
    await asyncio.gather(start_socketio(SERVER), ticker(), ticker_fast(), ticker_5s())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
