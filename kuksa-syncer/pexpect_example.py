import pexpect
import asyncio
from typing import Optional, Callable

async def run_with_pexpect(
    cmd: str,
    master_id: str,
    stdout_callback: Optional[Callable[[str, str], None]] = None,
    stderr_callback: Optional[Callable[[str, str], None]] = None,
    finished_callback: Optional[Callable[[str, int], None]] = None
):
    """
    Run a subprocess using pexpect with real-time output streaming.
    
    Args:
        cmd: Command to execute
        master_id: Identifier for the process
        stdout_callback: Callback for stdout lines (master_id, line)
        stderr_callback: Callback for stderr lines (master_id, line)
        finished_callback: Callback when process finishes (master_id, return_code)
    """
    
    def run_in_executor():
        """Run pexpect in a thread executor to avoid blocking"""
        child = pexpect.spawn(cmd, encoding='utf-8', logfile=None)
        
        while True:
            try:
                # Read from the process
                index = child.expect(['\n', pexpect.EOF, pexpect.TIMEOUT], timeout=0.1)
                
                if index == 0:  # New line
                    line = child.before.strip()
                    if line and stdout_callback:
                        # Run callback in event loop
                        asyncio.create_task(stdout_callback(master_id, line))
                
                elif index == 1:  # EOF - process finished
                    # Get any remaining output
                    remaining = child.before.strip()
                    if remaining and stdout_callback:
                        asyncio.create_task(stdout_callback(master_id, remaining))
                    break
                
                elif index == 2:  # Timeout - continue
                    continue
                    
            except pexpect.EOF:
                break
            except Exception as e:
                if stderr_callback:
                    asyncio.create_task(stderr_callback(master_id, f"Error: {str(e)}"))
                break
        
        child.close()
        return child.exitstatus
    
    # Run in executor to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    return_code = await loop.run_in_executor(None, run_in_executor)
    
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
# asyncio.create_task(run_with_pexpect(
#     cmd='python -u main.py',
#     master_id=data["request_from"],
#     stdout_callback=my_stdout_callback,
#     stderr_callback=my_stderr_callback,
#     finished_callback=process_done
# )) 