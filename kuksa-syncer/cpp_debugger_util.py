import os
import subprocess
import asyncio
import re
import datetime

APP_DIR = os.path.join(os.path.dirname(__file__), 'app')
CPP_FILE = os.path.join(APP_DIR, 'main.cpp')
BINARY_FILE = os.path.join(APP_DIR, 'main_bin')

async def compile_cpp():
    """Compile main.cpp in the app directory."""
    if not os.path.exists(CPP_FILE):
        return False, 'main.cpp not found.'
    # Detect architecture from environment or default to arm64 for Apple Silicon, x86_64 for Intel
    arch = os.environ.get('CPP_ARCH')
    if not arch:
        import platform
        machine = platform.machine()
        if machine == 'arm64' or machine == 'aarch64':
            arch = 'arm64'
        else:
            arch = 'x86_64'
    proc = await asyncio.create_subprocess_exec(
        'g++', CPP_FILE, '-g', '-O0', '-arch', arch, '-o', BINARY_FILE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return False, stderr.decode()
    return True, 'Compiled successfully.'

async def run_binary():
    """Run the compiled binary in the background and return the process and its PID."""
    if not os.path.exists(BINARY_FILE):
        return None, None, 'Binary not found.'
    proc = await asyncio.create_subprocess_exec(
        BINARY_FILE,
        cwd=APP_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.sleep(0.2)  # Give process time to start
    pid = proc.pid
    return proc, pid, 'Started.'

async def get_global_variables(watch_vars, pid):
    """Use gdb to extract only the specified watch_vars and their values from the running process (by PID)."""
    values = {}
    import platform
    is_macos = platform.system() == 'Darwin'
    for var in [v.strip() for v in watch_vars.split(',') if v.strip()]:
        if is_macos:
            # Use LLDB to attach and print global variable using 'frame variable ::var'
            lldb_cmd = (
                f"lldb -b -o 'process attach --pid {pid}' "
                f"-o 'frame variable ::{var}' -o 'process detach' -o 'quit' {BINARY_FILE}"
            )
            proc_val = await asyncio.create_subprocess_shell(
                lldb_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            out_val, err_val = await proc_val.communicate()
            if proc_val.returncode != 0:
                values[var] = f"Error: {err_val.decode().strip()}"
                continue
            # Match output like: (int) counter = 42
            match = re.search(r'\(\w+\)\s+' + re.escape(var) + r'\s*=\s*(.+)', out_val.decode())
            if match:
                values[var] = match.group(1).strip() if match.lastindex == 1 else match.group(2).strip()
            else:
                values[var] = "N/A"
        else:
            # Use GDB for non-macOS
            gdb_cmd = f"gdb -q --batch -ex 'file {BINARY_FILE}' -ex 'attach {pid}' -ex 'print {var}' -ex detach -ex quit"
            proc_val = await asyncio.create_subprocess_shell(
                gdb_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            out_val, err_val = await proc_val.communicate()
            if proc_val.returncode != 0:
                values[var] = f"Error: {err_val.decode().strip()}"
                continue
            match = re.search(r'\$\d+ = (.+)', out_val.decode())
            if match:
                values[var] = match.group(1).strip()
            else:
                values[var] = "N/A"
    return values, None

async def periodic_global_var_report(interval, sio, client_id, watch_vars, pid):
    """Periodically send global variable values to the client via sio.emit, from the running process."""
    first = True
    while True:
        if first:
            await asyncio.sleep(2)  # Wait 2 seconds before first GDB attach
            first = False
        else:
            await asyncio.sleep(interval)
        values, err = await get_global_variables(watch_vars, pid)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if values is not None:
            print(f"[{timestamp}] Global variables: {values}", flush=True)
            await sio.emit("cpp_debugger_global_vars", {
                "kit_id": client_id,
                "globals": values
            })
        else:
            print(f"[{timestamp}] Error getting global variables: {err}", flush=True)
            await sio.emit("cpp_debugger_global_vars", {
                "kit_id": client_id,
                "error": err
            })
