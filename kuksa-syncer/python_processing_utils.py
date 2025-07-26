# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

"""
Python processing utilities for syncer_lite.
Handles code analysis, global variable monitoring, and related functionality.
"""

import ast
import json
import time
import threading
import sys
import asyncio
from typing import List, Dict, Optional


def extract_global_variables(code: str) -> List[str]:
    """Extract global variable names from Python code using AST parsing"""
    try:
        tree = ast.parse(code)
        global_vars = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_vars.append(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                global_vars.append(node.target.id)
        
        # Remove duplicates and filter out common names
        filtered_vars = []
        common_names = {'i', 'j', 'k', 'temp', 'tmp', 'var', 'val', 'data', 'result', 'output'}
        for var in set(global_vars):
            if var not in common_names and not var.startswith('_'):
                filtered_vars.append(var)
        
        return filtered_vars
    except Exception as e:
        print(f"Error extracting variables: {e}", flush=True)
        return []


def create_monitoring_code(global_vars: List[str]) -> str:
    """Create code to monitor global variables in real-time"""
    if not global_vars:
        return ""
    
    monitoring_code = f"""
import json
import time
import threading
import sys

# Global variable monitoring
_monitored_vars = {global_vars}
_monitoring_active = True

def _monitor_globals():
    while _monitoring_active:
        try:
            globals_data = {{}}
            for var_name in _monitored_vars:
                if var_name in globals():
                    value = globals()[var_name]
                    try:
                        # Try to serialize the value
                        if isinstance(value, (int, float, str, bool, list, dict, tuple)):
                            globals_data[var_name] = value
                        else:
                            globals_data[var_name] = str(type(value).__name__) + ': ' + str(value)[:100]
                    except:
                        globals_data[var_name] = str(type(value).__name__)
                else:
                    globals_data[var_name] = "undefined"
            
            # Print in a format that can be captured by pexpect
            print(f"GLOBALS_UPDATE: {{json.dumps(globals_data)}}", flush=True)
        except Exception as e:
            print(f"GLOBALS_ERROR: {{str(e)}}", flush=True)
        
        time.sleep(1)  # Update every second

# Start monitoring in a separate thread
_monitor_thread = threading.Thread(target=_monitor_globals, daemon=True)
_monitor_thread.start()

# Function to stop monitoring
def stop_global_monitoring():
    global _monitoring_active
    _monitoring_active = False
"""
    
    return monitoring_code


def write_code_with_monitoring(code: str, filename: str = "main.py") -> List[str]:
    """Write code to a file with global variable monitoring injected"""
    # Extract global variables from the code
    global_vars = extract_global_variables(code)
    
    # Create monitoring code
    monitoring_code = create_monitoring_code(global_vars)
    
    # Combine original code with monitoring
    enhanced_code = monitoring_code + "\n" + code
    
    with open(filename, "w+") as f:
        f.write(enhanced_code)
    
    return global_vars


def create_stdout_callback_factory(loop, send_app_run_reply_func):
    """Create stdout callback factory with event loop"""
    def my_stdout_callback(master_id: str, line: str):
        print(f"stdout: {line}", flush=True)
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply_func(master_id, False, 0, line + '\r\n'), loop
            )
        else:
            print(f"[{master_id}] STDOUT: {line}", flush=True)
    return my_stdout_callback


def create_stderr_callback_factory(loop, send_app_run_reply_func):
    """Create stderr callback factory with event loop"""
    def my_stderr_callback(master_id: str, line: str):
        print(f"stderr: {line}", flush=True)
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply_func(master_id, False, 0, line + '\r\n'), loop
            )
        else:
            print(f"[{master_id}] STDERR: {line}", flush=True)
    return my_stderr_callback


def create_globals_callback_factory(loop, send_globals_update_func):
    """Create globals callback factory with event loop"""
    def my_globals_callback(master_id: str, line: str):
        """Callback for global variable updates"""
        if line.startswith("GLOBALS_UPDATE: "):
            try:
                # Extract the JSON data
                json_data = line[16:]  # Remove "GLOBALS_UPDATE: " prefix
                globals_data = json.loads(json_data)
                
                # Send global variables update to client
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        send_globals_update_func(master_id, globals_data), loop
                    )
            except Exception as e:
                print(f"Error parsing globals data: {str(e)}", flush=True)
        elif line.startswith("GLOBALS_ERROR: "):
            error_msg = line[15:]  # Remove "GLOBALS_ERROR: " prefix
            print(f"Globals monitoring error: {error_msg}", flush=True)
    return my_globals_callback


def create_finished_callback_factory(loop, send_app_run_reply_func):
    """Create finished callback factory with event loop"""
    def process_done(master_id: str, retcode: int):
        """Callback when process finishes"""
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                send_app_run_reply_func(master_id, True, retcode, ""), loop
            )
        else:
            print(f"[{master_id}] FINISHED: Process completed with return code {retcode}", flush=True)
    return process_done


def remove_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    import re
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


def validate_python_code(code: str) -> Dict[str, any]:
    """Validate Python code syntax and return validation result"""
    try:
        ast.parse(code)
        return {
            "valid": True,
            "error": None
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "error": f"Syntax error at line {e.lineno}: {e.text.strip() if e.text else str(e)}"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation error: {str(e)}"
        }


def get_code_statistics(code: str) -> Dict[str, any]:
    """Get statistics about the Python code"""
    try:
        tree = ast.parse(code)
        
        # Count different types of nodes
        stats = {
            "total_lines": len(code.splitlines()),
            "assignments": 0,
            "function_defs": 0,
            "class_defs": 0,
            "imports": 0,
            "calls": 0,
            "variables": set()
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                stats["assignments"] += 1
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        stats["variables"].add(target.id)
            elif isinstance(node, ast.FunctionDef):
                stats["function_defs"] += 1
            elif isinstance(node, ast.ClassDef):
                stats["class_defs"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                stats["imports"] += 1
            elif isinstance(node, ast.Call):
                stats["calls"] += 1
        
        # Convert set to list for JSON serialization
        stats["variables"] = list(stats["variables"])
        
        return stats
    except Exception as e:
        return {
            "error": f"Error analyzing code: {str(e)}"
        } 