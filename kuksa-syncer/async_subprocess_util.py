# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

"""
Async subprocess utility for subprocess management with real-time stdout/stderr streaming.
Drop-in replacement for subpiper functionality using only standard library.
"""

import asyncio
import subprocess
import time
import os
import sys
import shlex
from typing import Optional, Callable, Union, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class ProcessState(Enum):
    """Process state enumeration"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    FINISHED = "finished"
    KILLED = "killed"
    ERROR = "error"

@dataclass
class ProcessInfo:
    """Process information container"""
    master_id: str
    cmd: str
    pid: Optional[int] = None
    state: ProcessState = ProcessState.INITIALIZED
    return_code: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    stdout_buffer: List[str] = None
    stderr_buffer: List[str] = None
    
    def __post_init__(self):
        if self.stdout_buffer is None:
            self.stdout_buffer = []
        if self.stderr_buffer is None:
            self.stderr_buffer = []

class AsyncSubprocessProcess:
    """Async subprocess wrapper with real-time output streaming"""
    
    def __init__(
        self,
        cmd: Union[str, List[str]],
        master_id: str = "0",
        stdout_callback: Optional[Callable[[str, str], None]] = None,
        stderr_callback: Optional[Callable[[str, str], None]] = None,
        finished_callback: Optional[Callable[[str, int], None]] = None,
        add_path_list: List[str] = None,
        hide_console: bool = True,
        silent: bool = False,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ):
        """
        Initialize AsyncSubprocessProcess
        
        Args:
            cmd: Command to execute (string or list)
            master_id: Unique identifier for the process
            stdout_callback: Callback for stdout lines (master_id, line)
            stderr_callback: Callback for stderr lines (master_id, line)
            finished_callback: Callback when process finishes (master_id, return_code)
            add_path_list: Additional paths to add to PATH
            hide_console: Hide console window (Windows)
            silent: Don't print to console
            cwd: Working directory
            env: Environment variables
        """
        self.cmd = cmd if isinstance(cmd, list) else shlex.split(cmd, posix=False)
        self.master_id = master_id
        self.stdout_callback = stdout_callback
        self.stderr_callback = stderr_callback
        self.finished_callback = finished_callback
        self.add_path_list = add_path_list or []
        self.hide_console = hide_console
        self.silent = silent
        self.cwd = cwd
        self.env = env
        
        # Process state
        self.process_info = ProcessInfo(
            master_id=master_id,
            cmd=" ".join(self.cmd)
        )
        
        # Internal state
        self._process: Optional[asyncio.subprocess.Process] = None
        self._running = False
        self._killed = False
        self._task: Optional[asyncio.Task] = None
        
    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables"""
        env = os.environ.copy()
        
        # Add custom paths to PATH
        if self.add_path_list:
            path_sep = os.pathsep
            custom_path = path_sep.join(self.add_path_list)
            env["PATH"] = f"{custom_path}{path_sep}{env.get('PATH', '')}"
        
        # Add custom environment variables
        if self.env:
            env.update(self.env)
            
        return env
    
    async def _run_process(self):
        """Run the process asynchronously"""
        try:
            # Prepare environment
            env = self._prepare_environment()
            
            # Create subprocess
            self._process = await asyncio.create_subprocess_exec(
                *self.cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.cwd
            )
            
            self.process_info.pid = self._process.pid
            self.process_info.start_time = time.time()
            self.process_info.state = ProcessState.RUNNING
            self._running = True
            
            # Create tasks for reading stdout and stderr
            stdout_task = asyncio.create_task(self._read_stream(self._process.stdout, self.stdout_callback, "STDOUT"))
            stderr_task = asyncio.create_task(self._read_stream(self._process.stderr, self.stderr_callback, "STDERR"))
            
            # Wait for process to complete
            return_code = await self._process.wait()
            
            # Wait for streams to finish reading
            await stdout_task
            await stderr_task
            
            # Update process info
            self.process_info.return_code = return_code
            self.process_info.end_time = time.time()
            
            if self._killed:
                self.process_info.state = ProcessState.KILLED
            else:
                self.process_info.state = ProcessState.FINISHED
            
            self._running = False
            
            # Call finished callback
            if self.finished_callback:
                await self.finished_callback(self.master_id, return_code)
                
        except Exception as e:
            error_msg = f"Failed to start process: {str(e)}"
            self.process_info.stderr_buffer.append(error_msg)
            self.process_info.state = ProcessState.ERROR
            self.process_info.end_time = time.time()
            self._running = False
            
            if self.stderr_callback:
                await self.stderr_callback(self.master_id, error_msg)
            if not self.silent:
                print(f"[{self.master_id}] STDERR: {error_msg}", file=sys.stderr)
    
    async def _read_stream(self, stream, callback, stream_name):
        """Read from stream and call callback for each line"""
        if stream is None:
            return
            
        while True:
            line = await stream.readline()
            if not line:
                break
                
            line_str = line.decode('utf-8', errors='replace').rstrip()
            if line_str:
                if stream_name == "STDOUT":
                    self.process_info.stdout_buffer.append(line_str)
                else:
                    self.process_info.stderr_buffer.append(line_str)
                
                if callback:
                    await callback(self.master_id, line_str)
                if not self.silent:
                    print(f"[{self.master_id}] {stream_name}: {line_str}", file=sys.stdout if stream_name == "STDOUT" else sys.stderr)
    
    async def start(self) -> 'AsyncSubprocessProcess':
        """Start the process"""
        if self._running:
            raise RuntimeError("Process is already running")
        
        self._task = asyncio.create_task(self._run_process())
        return self
    
    async def kill(self, signal: int = None) -> bool:
        """Kill the process"""
        if not self._running or not self._process:
            return False
        
        try:
            self._killed = True
            
            if signal:
                self._process.send_signal(signal)
            else:
                self._process.terminate()
                
            # Wait a bit for graceful termination
            await asyncio.sleep(0.1)
            
            # Force kill if still running
            if self._process.returncode is None:
                self._process.kill()
            
            return True
        except Exception as e:
            if not self.silent:
                print(f"[{self.master_id}] Error killing process: {str(e)}", file=sys.stderr)
            return False
    
    async def terminate(self) -> bool:
        """Terminate the process gracefully"""
        return await self.kill()
    
    def is_alive(self) -> bool:
        """Check if process is still running"""
        return self._running and self._process and self._process.returncode is None
    
    async def wait(self, timeout: Optional[float] = None) -> Optional[int]:
        """Wait for process to finish"""
        if not self._task:
            return None
        
        try:
            await asyncio.wait_for(self._task, timeout=timeout)
            return self.process_info.return_code
        except asyncio.TimeoutError:
            return None
    
    def get_info(self) -> ProcessInfo:
        """Get process information"""
        return self.process_info

async def async_subprocess_subpiper(
    cmd: Union[str, List[str]],
    master_id: str,
    stdout_callback: Optional[Callable[[str, str], None]] = None,
    stderr_callback: Optional[Callable[[str, str], None]] = None,
    add_path_list: List[str] = None,
    finished_callback: Optional[Callable[[str, int], None]] = None,
    hide_console: bool = True,
    silent: bool = False,
    **kwargs
) -> AsyncSubprocessProcess:
    """
    Drop-in replacement for subpiper function using async subprocess.
    
    Args:
        cmd: Command to execute
        master_id: Unique identifier for the process
        stdout_callback: Callback for stdout lines (master_id, line)
        stderr_callback: Callback for stderr lines (master_id, line)
        add_path_list: Additional paths to add to PATH
        finished_callback: Callback when process finishes (master_id, return_code)
        hide_console: Hide console window (Windows)
        silent: Don't print to console
        **kwargs: Additional arguments passed to AsyncSubprocessProcess
        
    Returns:
        AsyncSubprocessProcess instance
    """
    process = AsyncSubprocessProcess(
        cmd=cmd,
        master_id=master_id,
        stdout_callback=stdout_callback,
        stderr_callback=stderr_callback,
        finished_callback=finished_callback,
        add_path_list=add_path_list,
        hide_console=hide_console,
        silent=silent,
        **kwargs
    )
    
    return await process.start()

# Utility functions
def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running"""
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
        return True
    except OSError:
        return False

def kill_process_tree(pid: int) -> bool:
    """Kill a process and all its children"""
    try:
        import psutil
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            child.terminate()
        
        # Wait for children to terminate
        gone, alive = psutil.wait_procs(children, timeout=3)
        
        # Force kill remaining children
        for child in alive:
            child.kill()
        
        # Kill parent
        parent.terminate()
        parent.wait(timeout=3)
        
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        return False
    except ImportError:
        # Fallback without psutil
        try:
            os.kill(pid, 9)  # SIGKILL
            return True
        except OSError:
            return False

# Example usage and testing
if __name__ == "__main__":
    async def test_stdout_callback(master_id: str, line: str):
        print(f"STDOUT [{master_id}]: {line}")
    
    async def test_stderr_callback(master_id: str, line: str):
        print(f"STDERR [{master_id}]: {line}")
    
    async def test_finished_callback(master_id: str, return_code: int):
        print(f"FINISHED [{master_id}]: Process completed with return code {return_code}")
    
    async def test():
        # Test basic functionality
        print("Testing async_subprocess_subpiper...")
        
        process = await async_subprocess_subpiper(
            cmd="python -c 'import time; print(\"Hello from Python\"); time.sleep(1); print(\"Goodbye\"); exit(0)'",
            master_id="test1",
            stdout_callback=test_stdout_callback,
            stderr_callback=test_stderr_callback,
            finished_callback=test_finished_callback
        )
        
        # Wait for process to finish
        return_code = await process.wait()
        print(f"Process finished with return code: {return_code}")
        
        # Test process info
        info = process.get_info()
        print(f"Process info: {info}")
    
    # Run test
    asyncio.run(test()) 