# Copyright (c) 2025 Eclipse Foundation.
#
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import mmap
import os
import struct
import json

# Constants
SHM_NAME = "/my_shm"
MAX_VARS = 10
VAR_NAME_SIZE = 32  # Max length of variable name
VAR_VALUE_SIZE = 64 # Max length of variable value (as string)
METADATA_SIZE = 4 # To store number of variables

# Total size of one variable entry: name + value
ENTRY_SIZE = VAR_NAME_SIZE + VAR_VALUE_SIZE

# Total size of the shared memory
SHM_SIZE = METADATA_SIZE + (MAX_VARS * ENTRY_SIZE)


def create_shared_memory():
    """Creates or opens a shared memory block."""
    try:
        # Using shm_open for POSIX shared memory
        fd = os.open(f"/dev/shm{SHM_NAME}", os.O_CREAT | os.O_TRUNC | os.O_RDWR)
        os.ftruncate(fd, SHM_SIZE)
        shm = mmap.mmap(fd, SHM_SIZE, mmap.MAP_SHARED)
        os.close(fd)
        return shm
    except Exception as e:
        print(f"Error creating shared memory: {e}")
        return None

def open_shared_memory():
    """Opens an existing shared memory block."""
    try:
        fd = os.open(f"/dev/shm{SHM_NAME}", os.O_RDWR)
        shm = mmap.mmap(fd, SHM_SIZE, mmap.MAP_SHARED)
        os.close(fd)
        return shm
    except Exception as e:
        print(f"Error opening shared memory: {e}")
        return None

def write_to_shm(shm, watch_vars):
    """
    Writes variable names to shared memory.
    The C++ app will read these names and write back the values.
    """
    if not shm:
        return

    var_list = [v.strip() for v in watch_vars.split(',') if v.strip()]
    num_vars = len(var_list)

    # Write number of variables
    shm[0:METADATA_SIZE] = struct.pack('I', num_vars)

    for i, var_name in enumerate(var_list):
        if i >= MAX_VARS:
            break
        offset = METADATA_SIZE + i * ENTRY_SIZE
        
        # Pack variable name
        packed_name = var_name.encode('utf-8').ljust(VAR_NAME_SIZE, b'\0')
        shm[offset:offset + VAR_NAME_SIZE] = packed_name

def read_from_shm(shm):
    """Reads variable names and values from shared memory."""
    if not shm:
        return {}

    try:
        # Read number of variables
        num_vars_bytes = shm[0:METADATA_SIZE]
        num_vars = struct.unpack('I', num_vars_bytes)[0]

        values = {}
        for i in range(num_vars):
            offset = METADATA_SIZE + i * ENTRY_SIZE
            
            # Unpack variable name
            name_bytes = shm[offset:offset + VAR_NAME_SIZE]
            var_name = name_bytes.split(b'\0', 1)[0].decode('utf-8')

            # Unpack variable value
            value_bytes = shm[offset + VAR_NAME_SIZE : offset + ENTRY_SIZE]
            var_value_str = value_bytes.split(b'\0', 1)[0].decode('utf-8')

            if var_name:
                values[var_name] = var_value_str
        return values
    except Exception as e:
        print(f"Error reading from shared memory: {e}")
        return {}

def set_variable_in_shm(shm, var_name, new_value):
    """Sets a new value for a variable in shared memory."""
    if not shm:
        return False, "Shared memory not available."

    try:
        num_vars = struct.unpack('I', shm[0:METADATA_SIZE])[0]
        for i in range(num_vars):
            offset = METADATA_SIZE + i * ENTRY_SIZE
            name_bytes = shm[offset:offset + VAR_NAME_SIZE]
            current_var_name = name_bytes.split(b'\0', 1)[0].decode('utf-8')

            if current_var_name == var_name:
                value_offset = offset + VAR_NAME_SIZE
                
                # The C++ app will have to handle this.
                value_to_write = f"SET:{new_value}"
                
                packed_value = value_to_write.encode('utf-8').ljust(VAR_VALUE_SIZE, b'\0')
                shm[value_offset : value_offset + VAR_VALUE_SIZE] = packed_value
                return True, f"Set request for {var_name} written to shared memory."
        
        return False, f"Variable '{var_name}' not found in shared memory."
    except Exception as e:
        return False, f"Error setting variable in shared memory: {e}"

def cleanup_shared_memory():
    """Unlinks the shared memory segment."""
    try:
        os.unlink(f"/dev/shm{SHM_NAME}")
        print(f"Shared memory file /dev/shm{SHM_NAME} removed.")
    except FileNotFoundError:
        pass # It's ok if it doesn't exist
    except Exception as e:
        print(f"Error cleaning up shared memory: {e}")
