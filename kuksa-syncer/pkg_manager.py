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

USERNAME = os.environ.get('USER', os.environ.get('USERNAME'))

async def installPkg(pkg_str):
    response = []
    try:
        command = f"pip install --target /home/{USERNAME}/python-packages {pkg_str}"
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
        command = f"pip freeze --path /home/{USERNAME}/python-packages > /home/{USERNAME}/pkg.txt"
        subprocess.run(command,shell=True)
        with open(f"/home/{USERNAME}/pkg.txt",'r') as file:
            pkgs = file.read()
            return pkgs
    except FileNotFoundError:
        print("File not found")
    except IOError as e:
        print(e)