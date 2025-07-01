# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import os
import subprocess
import shutil
from velocitas.model_generator import generate_model
import json
import signal
import re
# from utils import correct_parent_class_in_vehicle_model

def extract_class_names(python_code):
    """Extracts class names from a string of Python code.

    Args:
        python_code: The string containing Python code.

    Returns:
        A list of strings, where each string is a class name found in the code.
        Returns an empty list if no class names are found.
    """

    # Regular expression to match class definitions.  Handles inheritance.
    pattern = r"class\s+(\w+)\s*(\(.*\))?:"  # Improved regex

    matches = re.findall(pattern, python_code)
    class_names = [match[0] for match in matches]  # Extract the class name (group 1)
    return class_names
  
def correct_parent_class_in_vehicle_model(file_path):
   # Read the file
    with open(file_path, "r") as file:
        file_contents = file.read()

    # Extract class names from the file
    class_names = extract_class_names(file_contents)

    # Check if the file contains a class definition
    if class_names and len(class_names) > 0:
        # Get the first class name
        class_name = class_names[0]

        # Replace the parent class name
        new_file_contents = file_contents.replace('vehicle = Vehicle("Vehicle")', f'vehicle = {class_name}("{class_name}")')

        # Write the new contents back to the file
        with open(file_path, "w") as file:
            file.write(new_file_contents)

        print(f"Parent class name in '{file_path}' has been corrected to '{class_name}'.", flush=True)
    else:
        print(f"No class definitions")

def restart_databroker():
    try:
        result = subprocess.check_output(["pgrep", "-f", "/app/databroker"]).decode().strip()
        pids = result.split('\n')
        
        # If any PIDs are found, terminate them
        if pids and pids[0]:
            for pid in pids:
                os.kill(int(pid), signal.SIGKILL)
        
    except subprocess.CalledProcessError:
        print("No running instance of databroker found. Starting a new instance...", flush=True)
    
    except Exception as e:
        print(f"Error: Failed to terminate existing databroker processes. {str(e)}", flush=True)
    
    # Restart the databroker app regardless of whether any instances were found
    try:
        command = "/app/databroker &"
        subprocess.Popen(command, shell=True)
        print("Databroker restarted successfully.", flush=True)
        
    except Exception as e:
        print(f"Error: Failed to start databroker. {str(e)}", flush=True)
    
def generate_vehicle_model(input_str):
    data = json.loads(input_str)
    vss_path = "/home/dev/ws/vss.json"
    with open(vss_path, 'w') as vss_file:
        json.dump(data, vss_file, indent=4)
    
    if not os.path.isfile(vss_path):
        print("Error: Couldn't find vss.json.", flush=True)
        return

    try:
        current_dir = "/home/dev/python-packages/vehicle"
        if os.path.exists(current_dir):
            shutil.rmtree(current_dir)
        input_unit_file_path_list = ["/home/dev/python-packages/vehicle_signal_specification/spec/units.yaml"]
        language = "python"
        target_folder = "/home/dev/ws/gen_model"
        name = "vehicle"
        strict = True
        include_dir = "/home/dev/python-packages/vehicle_signal_specification/spec"

        generate_model( vss_path,
                        input_unit_file_path_list,
                        language,
                        target_folder,
                        name,
                        strict,
                        include_dir)
        
        # on parent class, ensure using the right class name
        correct_parent_class_in_vehicle_model(f"{target_folder}/vehicle/__init__.py")

        
        shutil.move(f"{target_folder}/vehicle", "/home/dev/python-packages/")
        restart_databroker()
    
    except Exception as e:
        print(f"..Error occured when generating vehicle model: {e}.", flush=True)  

def revert_vehicle_model():
    current_dir = "/home/dev/python-packages/vehicle"
    if os.path.exists(current_dir):
        shutil.rmtree(current_dir)
    # The std_vehicle directory is included in the Dockerfile so it will always
    # be here unless it get removed during runtime.
    old_dir = "/home/dev/python-packages/std_vehicle"
    shutil.copytree(old_dir, current_dir)

    # restore default vss.json
    copy_and_override("/home/dev/ws/default_vss.json", "/home/dev/ws/vss.json")
    restart_databroker()
    print("Reverted back to standard vehicle model")

def copy_and_override(source_file, destination_file):
    """Copies source_file to destination_file, overwriting if it exists."""
    try:
        shutil.copyfile(source_file, destination_file)
        print(f"File '{source_file}' copied to '{destination_file}' successfully.")
    except FileNotFoundError:
        print(f"Error: Source file '{source_file}' not found.")
    except Exception as e:
        print("An error occurred:", e)