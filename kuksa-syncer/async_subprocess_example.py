import asyncio
import subprocess
from typing import Optional, Callable

async def run_async_subprocess(
    cmd: str,
    master_id: str,
    stdout_callback: Optional[Callable[[str, str], None]] = None,
    stderr_callback: Optional[Callable[[str, str], None]] = None,
    finished_callback: Optional[Callable[[str, int], None]] = None
):
    """
    Run a subprocess asynchronously with real-time stdout/stderr streaming.
    
    Args:
        cmd: Command to execute
        master_id: Identifier for the process
        stdout_callback: Callback for stdout lines (master_id, line)
        stderr_callback: Callback for stderr lines (master_id, line)
        finished_callback: Callback when process finishes (master_id, return_code)
    """
    
    # Create the subprocess
    process = await asyncio.create_subprocess_exec(
        *cmd.split(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        universal_newlines=True,
        bufsize=1  # Line buffered
    )
    
    async def read_stream(stream, callback, stream_name):
        """Read from stream and call callback for each line"""
        while True:
            line = await stream.readline()
            if not line:
                break
            line = line.rstrip()
            if callback:
                callback(master_id, line)
            print(f"{stream_name}: {line}")
    
    # Create tasks for reading stdout and stderr
    stdout_task = asyncio.create_task(read_stream(process.stdout, stdout_callback, "STDOUT"))
    stderr_task = asyncio.create_task(read_stream(process.stderr, stderr_callback, "STDERR"))
    
    # Wait for the process to complete
    return_code = await process.wait()
    
    # Wait for streams to finish reading
    await stdout_task
    await stderr_task
    
    if finished_callback:
        finished_callback(master_id, return_code)
    
    return return_code

# Example usage in your syncer.py context:
async def my_stdout_callback(master_id: str, line: str):
    await send_app_run_reply(master_id, False, 0, line + '\r\n')

async def my_stderr_callback(master_id: str, line: str):
    await send_app_run_reply(master_id, False, 0, line + '\r\n')

async def process_done(master_id: str, retcode: int):
    await send_app_run_reply(master_id, True, retcode, "")

# In your messageToKit handler, replace subpiper with:
async def run_python_app_async(data):
    # ... your existing code ...
    
    # Instead of subpiper, use:
    asyncio.create_task(run_async_subprocess(
        cmd='python -u main.py',
        master_id=data["request_from"],
        stdout_callback=my_stdout_callback,
        stderr_callback=my_stderr_callback,
        finished_callback=process_done
    )) 