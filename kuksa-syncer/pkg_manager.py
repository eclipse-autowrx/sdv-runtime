# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

import os
import subprocess
import json
import asyncio
import tempfile

USERNAME = os.environ.get('USER', os.environ.get('USERNAME'))

async def installPkg(pkg_str):
    response = []
    try:
        # Use a more flexible approach for package installation
        command = f"pip3 install --user --break-system-packages {pkg_str}"
        proc = await asyncio.create_subprocess_shell(
            command, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        response.append(stdout.decode().strip())
        response.append(stderr.decode().strip())

    except subprocess.CalledProcessError as e:
        print("An error occured while installing Python packages.",flush=True)
        print(e.stderr, flush=True)
        response.append(e.stderr)
    
    return response

def listPkg():
    try:
        # Use a temporary file for the package list
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Get the list of installed packages
        command = f"pip3 list --format=freeze"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error listing packages: {result.stderr}"
            
    except Exception as e:
        return f"Error: {str(e)}"