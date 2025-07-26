# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

"""
Pexpect utility for subprocess management with real-time stdout/stderr streaming.
Drop-in replacement for subpiper functionality.
"""

import pexpect
import asyncio
import threading
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

class PexpectProcess:
    """Pexpect-based process wrapper with real-time output streaming"""
    
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
        timeout: float = 30.0,
        maxread: int = 2000,
        searchwindowsize: int = None,
        logfile: Any = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ):
        """
        Initialize PexpectProcess
        
        Args:
            cmd: Command to execute (string or list)
            master_id: Unique identifier for the process
            stdout_callback: Callback for stdout lines (master_id, line)
            stderr_callback: Callback for stderr lines (master_id, line)
            finished_callback: Callback when process finishes (master_id, return_code)
            add_path_list: Additional paths to add to PATH
            hide_console: Hide console window (Windows)
            silent: Don't print to console
            timeout: Timeout for expect operations
            maxread: Maximum bytes to read at once
            searchwindowsize: Size of search window for expect
            logfile: Log file for pexpect output
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
        self.timeout = timeout
        self.maxread = maxread
        self.searchwindowsize = searchwindowsize
        self.logfile = logfile
        self.cwd = cwd
        self.env = env
        
        # Process state
        self.process_info = ProcessInfo(
            master_id=master_id,
            cmd=" ".join(self.cmd)
        )
        
        # Internal state
        self._child: Optional[pexpect.spawn] = None
        self._running = False
        self._killed = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
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
    
    def _create_pexpect_child(self) -> pexpect.spawn:
        """Create and configure pexpect child process"""
        # Prepare environment
        env = self._prepare_environment()
        
        # Create pexpect spawn
        child = pexpect.spawn(
            self.cmd[0],
            args=self.cmd[1:] if len(self.cmd) > 1 else [],
            timeout=self.timeout,
            maxread=self.maxread,
            searchwindowsize=self.searchwindowsize,
            logfile=self.logfile,
            cwd=self.cwd,
            env=env,
            encoding='utf-8',
            codec_errors='replace'
        )
        
        return child
    
    def _run_process(self):
        """Run the process in a separate thread"""
        try:
            self._child = self._create_pexpect_child()
            self.process_info.pid = self._child.pid
            self.process_info.start_time = time.time()
            self.process_info.state = ProcessState.RUNNING
            self._running = True
            
            # Read output in real-time
            while not self._stop_event.is_set():
                try:
                    # Try to read a line with timeout
                    index = self._child.expect(['\n', pexpect.EOF, pexpect.TIMEOUT], timeout=0.1)
                    
                    if index == 0:  # New line
                        line = self._child.before.strip()
                        if line:
                            self.process_info.stdout_buffer.append(line)
                            if self.stdout_callback:
                                # Use asyncio.run_coroutine_threadsafe for thread safety
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        asyncio.run_coroutine_threadsafe(
                                            self.stdout_callback(self.master_id, line), loop
                                        )
                                    else:
                                        # Fallback: just call the callback directly
                                        self.stdout_callback(self.master_id, line)
                                except RuntimeError:
                                    # No event loop, call directly
                                    self.stdout_callback(self.master_id, line)
                            if not self.silent:
                                print(f"[{self.master_id}] STDOUT: {line}", file=sys.stdout)
                    
                    elif index == 1:  # EOF - process finished
                        # Get any remaining output
                        remaining = self._child.before.strip()
                        if remaining:
                            self.process_info.stdout_buffer.append(remaining)
                            if self.stdout_callback:
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        asyncio.run_coroutine_threadsafe(
                                            self.stdout_callback(self.master_id, remaining), loop
                                        )
                                    else:
                                        self.stdout_callback(self.master_id, remaining)
                                except RuntimeError:
                                    self.stdout_callback(self.master_id, remaining)
                            if not self.silent:
                                print(f"[{self.master_id}] STDOUT: {remaining}", file=sys.stdout)
                        break
                    
                    elif index == 2:  # Timeout - continue
                        continue
                        
                except pexpect.EOF:
                    break
                except Exception as e:
                    error_msg = f"Error reading process output: {str(e)}"
                    self.process_info.stderr_buffer.append(error_msg)
                    if self.stderr_callback:
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.run_coroutine_threadsafe(
                                    self.stderr_callback(self.master_id, error_msg), loop
                                )
                            else:
                                self.stderr_callback(self.master_id, error_msg)
                        except RuntimeError:
                            self.stderr_callback(self.master_id, error_msg)
                    if not self.silent:
                        print(f"[{self.master_id}] STDERR: {error_msg}", file=sys.stderr)
                    break
            
            # Process finished
            self._child.close()
            self.process_info.return_code = self._child.exitstatus
            self.process_info.end_time = time.time()
            
            if self._killed:
                self.process_info.state = ProcessState.KILLED
            else:
                self.process_info.state = ProcessState.FINISHED
            
            self._running = False
            
            # Call finished callback
            if self.finished_callback:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.finished_callback(self.master_id, self.process_info.return_code), loop
                        )
                    else:
                        self.finished_callback(self.master_id, self.process_info.return_code)
                except RuntimeError:
                    self.finished_callback(self.master_id, self.process_info.return_code)
                
        except Exception as e:
            error_msg = f"Failed to start process: {str(e)}"
            self.process_info.stderr_buffer.append(error_msg)
            self.process_info.state = ProcessState.ERROR
            self.process_info.end_time = time.time()
            self._running = False
            
            if self.stderr_callback:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.stderr_callback(self.master_id, error_msg), loop
                        )
                    else:
                        self.stderr_callback(self.master_id, error_msg)
                except RuntimeError:
                    self.stderr_callback(self.master_id, error_msg)
            if not self.silent:
                print(f"[{self.master_id}] STDERR: {error_msg}", file=sys.stderr)
    
    def start(self) -> 'PexpectProcess':
        """Start the process"""
        if self._running:
            raise RuntimeError("Process is already running")
        
        self._thread = threading.Thread(target=self._run_process, daemon=True)
        self._thread.start()
        return self
    
    def kill(self, signal: int = None) -> bool:
        """Kill the process"""
        if not self._running or not self._child:
            return False
        
        try:
            self._killed = True
            self._stop_event.set()
            
            if signal:
                self._child.kill(signal)
            else:
                self._child.terminate()
                
            # Wait a bit for graceful termination
            time.sleep(0.1)
            
            # Force kill if still running
            if self._child.isalive():
                self._child.kill()
            
            return True
        except Exception as e:
            if not self.silent:
                print(f"[{self.master_id}] Error killing process: {str(e)}", file=sys.stderr)
            return False
    
    def terminate(self) -> bool:
        """Terminate the process gracefully"""
        return self.kill()
    
    def is_alive(self) -> bool:
        """Check if process is still running"""
        return self._running and self._child and self._child.isalive()
    
    def wait(self, timeout: Optional[float] = None) -> Optional[int]:
        """Wait for process to finish"""
        if not self._thread:
            return None
        
        self._thread.join(timeout)
        return self.process_info.return_code
    
    def get_info(self) -> ProcessInfo:
        """Get process information"""
        return self.process_info

def pexpect_subpiper(
    cmd: Union[str, List[str]],
    master_id: str,
    stdout_callback: Optional[Callable[[str, str], None]] = None,
    stderr_callback: Optional[Callable[[str, str], None]] = None,
    add_path_list: List[str] = None,
    finished_callback: Optional[Callable[[str, int], None]] = None,
    hide_console: bool = True,
    silent: bool = False,
    **kwargs
) -> PexpectProcess:
    """
    Drop-in replacement for subpiper function.
    
    Args:
        cmd: Command to execute
        master_id: Unique identifier for the process
        stdout_callback: Callback for stdout lines (master_id, line)
        stderr_callback: Callback for stderr lines (master_id, line)
        add_path_list: Additional paths to add to PATH
        finished_callback: Callback when process finishes (master_id, return_code)
        hide_console: Hide console window (Windows)
        silent: Don't print to console
        **kwargs: Additional arguments passed to PexpectProcess
        
    Returns:
        PexpectProcess instance
    """
    process = PexpectProcess(
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
    
    return process.start()

# Convenience function for backward compatibility
def subpiper(*args, **kwargs):
    """Alias for pexpect_subpiper for backward compatibility"""
    return pexpect_subpiper(*args, **kwargs)

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
        print(f"FINISHED [{master_id}]: Process finished with code {return_code}")
    
    async def test():
        # Test basic functionality
        print("Testing pexpect_subpiper...")
        
        process = pexpect_subpiper(
            cmd="python3 -c 'import time; print(\"Hello from Python\"); time.sleep(1); print(\"Goodbye\"); exit(0)'",
            master_id="test1",
            stdout_callback=test_stdout_callback,
            stderr_callback=test_stderr_callback,
            finished_callback=test_finished_callback
        )
        
        # Wait for process to finish
        return_code = process.wait()
        print(f"Process finished with return code: {return_code}")
        
        # Test process info
        info = process.get_info()
        print(f"Process info: {info}")
    
    # Run test
    asyncio.run(test()) 