# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import os
import signal
import subprocess
import time

import re

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


def restartMockProvider():
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

        time.sleep(0.5)

        print("Restarting the script...", flush=True)
        subprocess.Popen(["python", "/home/dev/ws/mock/mockprovider.py"])
        print("Script restarted.", flush=True)
    else:
        print(f"mockprovider pid file at '{pid_file}' does not exist. Starting the script directly.", flush=True)
        # If the .pid file doesn't exist, just start the script
        subprocess.Popen(["python", "/home/dev/ws/mock/mockprovider.py"])
        print("Script started.", flush=True) 