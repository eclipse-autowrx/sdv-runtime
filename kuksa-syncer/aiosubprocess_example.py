import asyncio
from aiosubprocess import Process
from typing import Optional, Callable

async def run_with_aiosubprocess(
    cmd: str,
    master_id: str,
    stdout_callback: Optional[Callable[[str, str], None]] = None,
    stderr_callback: Optional[Callable[[str, str], None]] = None,
    finished_callback: Optional[Callable[[str, int], None]] = None
):
    """
    Run a subprocess using aiosubprocess with real-time output streaming.
    
    Args:
        cmd: Command to execute
        master_id: Identifier for the process
        stdout_callback: Callback for stdout lines (master_id, line)
        stderr_callback: Callback for stderr lines (master_id, line)
        finished_callback: Callback when process finishes (master_id, return_code)
    """
    
    # Create the process
    process = await Process.create(
        *cmd.split(),
        stdout=Process.PIPE,
        stderr=Process.PIPE,
        text=True
    )
    
    async def read_stream(stream, callback, stream_name):
        """Read from stream and call callback for each line"""
        async for line in stream:
            line = line.rstrip()
            if callback:
                await callback(master_id, line)
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
# asyncio.create_task(run_with_aiosubprocess(
#     cmd='python -u main.py',
#     master_id=data["request_from"],
#     stdout_callback=my_stdout_callback,
#     stderr_callback=my_stderr_callback,
#     finished_callback=process_done
# )) 