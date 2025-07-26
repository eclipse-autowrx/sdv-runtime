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
        # Replace \n with \r\n for proper line breaks in client rendering
        stdout_text = stdout.decode().strip().replace('\n', '\r\n')
        stderr_text = stderr.decode().strip().replace('\n', '\r\n')
        response.append(stdout_text)
        response.append(stderr_text)

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
            # Replace \n with \r\n for proper line breaks in client rendering
            return result.stdout.replace('\n', '\r\n')
        else:
            return f"Error listing packages: {result.stderr.replace('\n', '\r\n')}"
            
    except Exception as e:
        return f"Error: {str(e)}"