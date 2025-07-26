import subprocess
import asyncio
import threading
from typing import Optional, Callable

async def run_with_subprocess_run(
    cmd: str,
    master_id: str,
    stdout_callback: Optional[Callable[[str, str], None]] = None,
    stderr_callback: Optional[Callable[[str, str], None]] = None,
    finished_callback: Optional[Callable[[str, int], None]] = None
):
    """
    Run a subprocess using subprocess.run with real-time output streaming.
    
    Args:
        cmd: Command to execute
        master_id: Identifier for the process
        stdout_callback: Callback for stdout lines (master_id, line)
        stderr_callback: Callback for stderr lines (master_id, line)
        finished_callback: Callback when process finishes (master_id, return_code)
    """
    
    def run_in_thread():
        """Run subprocess in a thread to avoid blocking"""
        process = subprocess.Popen(
            cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Read stdout and stderr in real-time
        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            
            if stdout_line:
                line = stdout_line.rstrip()
                if stdout_callback:
                    # Schedule callback in event loop
                    asyncio.create_task(stdout_callback(master_id, line))
            
            if stderr_line:
                line = stderr_line.rstrip()
                if stderr_callback:
                    # Schedule callback in event loop
                    asyncio.create_task(stderr_callback(master_id, line))
            
            # Check if process has finished
            if process.poll() is not None:
                # Read any remaining output
                remaining_stdout, remaining_stderr = process.communicate()
                
                for line in remaining_stdout.splitlines():
                    if line and stdout_callback:
                        asyncio.create_task(stdout_callback(master_id, line))
                
                for line in remaining_stderr.splitlines():
                    if line and stderr_callback:
                        asyncio.create_task(stderr_callback(master_id, line))
                
                return process.returncode
    
    # Run in executor to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    return_code = await loop.run_in_executor(None, run_in_thread)
    
    if finished_callback:
        await finished_callback(master_id, return_code)
    
    return return_code

# Example usage:
async def my_stdout_callback(master_id: str, line: str):
    await send_app_run_reply(master_id, False, 0, line + '\r\n')

async def my_stderr_callback(master_id: str, line: str):
    await send_app_run_reply(master_id, False, 0, line + '\r\n')

async def process_done(master_id: str, retcode: int):
    await send_app_run_reply(master_id, True, retcode, "")

# Usage:
# asyncio.create_task(run_with_subprocess_run(
#     cmd='python -u main.py',
#     master_id=data["request_from"],
#     stdout_callback=my_stdout_callback,
#     stderr_callback=my_stderr_callback,
#     finished_callback=process_done
# )) 