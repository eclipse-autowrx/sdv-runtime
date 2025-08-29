# C++ Debugger Utility

This utility allows you to debug running C++ applications by reading global variable values in real-time using GDB (GNU Debugger).

## Features

- **Real-time Debugging**: Monitor global variables while your C++ application is running
- **Process Attachment**: GDB attaches to running child processes for live variable reading
- **Global Variable Reading**: Extract current values of global variables from runtime memory
- **Global Variable Setting**: **NEW!** Remotely modify global variable values while the app is running
- **Periodic Reporting**: Continuously monitor variables at configurable intervals
- **Process Tracking**: Automatically track and manage processes by client ID
- **Output Capture**: Capture and forward application stdout/stderr to clients
- **Client Isolation**: Each client's processes are tracked separately

## Prerequisites

### System Requirements
- Linux operating system
- GDB (GNU Debugger) installed
- Python 3.7+ with asyncio support
- C++ compiler (g++ or clang++)

### Security Requirements
**⚠️ Ptrace Permissions Required**

This utility uses GDB to attach to running processes, which requires ptrace permissions.

#### System Configuration
```bash
# Check current ptrace scope
cat /proc/sys/kernel/yama/ptrace_scope

# If ptrace_scope = 1, temporarily allow ptrace (requires sudo)
sudo sysctl kernel.yama.ptrace_scope=0

# To make permanent, add to /etc/sysctl.conf
echo "kernel.yama.ptrace_scope=0" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### How It Works
- **GDB attaches** to running child processes using `attach {pid}`
- **Live memory reading** - reads global variables from the running process
- **Continuous monitoring** - periodically checks variable values
- **Process tracking** - maintains registry of all client processes

## Usage

### Basic Usage
```python
from cpp_debugger_util import compile_cpp, get_global_variables

# Compile your C++ application
success, message = await compile_cpp()
if success:
    print("Compilation successful")
    
    # Read global variables (PID required)
    values, error = await get_global_variables("counter,globalValue", pid)
    # print(f"Global variables: {values}")
```

### Periodic Monitoring
```python
from cpp_debugger_util import periodic_global_var_report

# Monitor variables every 0.5 seconds (PID and from_id required)
await periodic_global_var_report(
    interval=0.5,
    sio=socketio_instance,
    client_id="client123",
    watch_vars="counter,globalValue",
    pid=process_pid,
    from_id="client_identifier"
)
```

### Process Management
```python
# Start monitoring and output capture for a client
proc, pid, run_msg = await cpp_debugger_util.run_binary()

if proc is not None and pid is not None:
    # Start periodic monitoring
    asyncio.create_task(cpp_debugger_util.periodic_global_var_report(
        0.5, sio, CLIENT_ID, watch_vars, pid, from_id
    ))
    
    # Start output capture
    asyncio.create_task(capture_app_output(proc, from_id))
```

### Remote Variable Setting
```python
# Set a global variable remotely while the app is running
socket.emit('messageToKit', {
    cmd: 'set_global_variable',
    var_name: 'counter',
    new_value: '100',
    request_from: 'client123'
});

# Set multiple variables
socket.emit('messageToKit', {
    cmd: 'set_global_variable',
    var_name: 'globalValue',
    new_value: '42.5',
    request_from: 'client123'
});
```

## Docker Considerations

### ⚠️ Docker Security Configuration Required

Since this utility attaches to running processes, Docker containers need special security settings.

#### Docker Run with Ptrace Capabilities
```bash
docker run --cap-add=SYS_PTRACE \
           --security-opt seccomp:unconfined \
           your-app-image
```

#### Docker Compose Configuration
```yaml
version: '3.8'
services:
  cpp-debugger:
    image: your-app-image
    cap_add:
      - SYS_PTRACE
    security_opt:
      - seccomp:unconfined
    volumes:
      - ./app:/app
```

#### Dockerfile Considerations
```dockerfile
# Install GDB and set ptrace permissions
RUN apt-get update && apt-get install -y gdb

# Ensure proper permissions for debugging
USER root
# Note: Container must be run with --cap-add=SYS_PTRACE
```

### Alternative: Privileged Container
```bash
docker run --privileged your-app-image
```

## Process Tracking System

### Automatic Process Management
The utility automatically tracks all processes started by each client:

```python
# Process registry structure
cpp_processes = {
    "client_id_1": [
        {
            "proc": subprocess.Popen_object,
            "pid": 12345,
            "type": "cpp",
            "start_time": 1640995200.0
        }
    ],
    "client_id_2": [...]
}
```

### Process Lifecycle
1. **Start**: Process automatically registered when client runs app
2. **Monitor**: Global variables and output continuously captured
3. **Stop**: All processes for a client stopped together
4. **Cleanup**: Process registry automatically maintained

### Stopping Processes
```python
# Stop all processes for a specific client
await stop_client_processes(from_id)

# Commands available:
# - "stop_python_app" - stops all processes for client
# - "stop_cpp_app" - stops all C++ processes for client
```

## Troubleshooting

### Common Issues

#### 1. "Could not attach to process" (ptrace error)
**Cause**: Insufficient ptrace permissions
**Solution**: 
```bash
# Check ptrace scope
cat /proc/sys/kernel/yama/ptrace_scope

# Allow ptrace (temporary)
sudo sysctl kernel.yama.ptrace_scope=0

# For Docker, use proper capabilities
docker run --cap-add=SYS_PTRACE --security-opt seccomp:unconfined
```

#### 2. "Compilation failed"
**Cause**: Missing dependencies or syntax errors
**Solution**: Check C++ compiler installation and source code

#### 3. "Binary not found"
**Cause**: Compilation didn't complete successfully
**Solution**: Ensure compilation succeeds before running

#### 4. "Global variables always return 0"
**Cause**: GDB not properly attached to process
**Solution**: Ensure process is running and PID is correct

### Debug Mode
Enable debug output by uncommenting debug lines in the code:
```python
# Uncomment for debugging
# print(f"GDB output: {output}")
# print(f"GDB stderr: {stderr}")
```

## Security Best Practices

### 1. Runtime Security
- **Ptrace permissions required** for process attachment
- **User account permissions** must allow process debugging
- **Process isolation** maintained between clients

### 2. Container Security
- **SYS_PTRACE capability** required for Docker containers
- **Seccomp unconfined** or custom profile needed
- **Privileged containers** as alternative option
- **Network isolation** recommended for production

### 3. Process Management
- **Client isolation** - processes tracked separately
- **Automatic cleanup** - processes stopped when client disconnects
- **Resource monitoring** - prevent resource leaks

## Example C++ Application

```cpp
#include <iostream>
#include <chrono>
#include <thread>

// Global variables to monitor and modify
int counter = 0;
double globalValue = 3.14159;

int main() {
    std::cout << "=== Simple Counter App ===" << std::endl;
    std::cout << "Counter will increase by 1 every second" << std::endl;
    std::cout << "Global variables can be modified remotely while running!" << std::endl;
    std::cout << "Press Ctrl+C to stop\n" << std::endl;

    while (true) {
        std::cout << "Counter: " << counter << " | Global Value: " << globalValue << std::endl;
        
        // Wait for 1 second
        std::this_thread::sleep_for(std::chrono::seconds(1));
        
        // Increase counter by 1
        counter++;
        globalValue += 0.1;
    }
    return 0;
}
```

## Remote Variable Modification Examples

### JavaScript/Node.js Client
```javascript
// Set counter to a specific value
socket.emit('messageToKit', {
    cmd: 'set_global_variable',
    var_name: 'counter',
    new_value: '50',
    request_from: 'myClient'
});

// Modify global value
socket.emit('messageToKit', {
    cmd: 'set_global_variable',
    var_name: 'globalValue',
    new_value: '999.99',
    request_from: 'myClient'
});
```

### Python Client
```python
# Set variables remotely
client.send({
    'cmd': 'set_global_variable',
    'var_name': 'counter',
    'new_value': '100',
    'request_from': 'pythonClient'
})
```

### Real-time Interaction
1. **Start the C++ app** - Counter starts at 0
2. **Monitor variables** - Watch them change in real-time
3. **Modify remotely** - Set counter to 100, globalValue to 42.5
4. **See changes immediately** - App continues running with new values
5. **Reset anytime** - Set counter back to 0 or any other value

## Compilation

```bash
# Compile with debug symbols
g++ -g -O0 -o main_bin main.cpp

# Or use the utility function
python3 -c "
import asyncio
from cpp_debugger_util import compile_cpp
asyncio.run(compile_cpp())
"
```

## API Reference

### Core Functions

#### `compile_cpp()`
Compiles C++ source code in the app directory.
- **Returns**: `(success: bool, message: str)`

#### `run_binary()`
Runs the compiled binary and returns process information.
- **Returns**: `(proc: subprocess.Popen, pid: int, message: str)`

#### `get_global_variables(watch_vars: str, pid: int)`
Reads global variable values from a running process.
- **Parameters**: 
  - `watch_vars`: Comma-separated variable names
  - `pid`: Process ID to attach to
- **Returns**: `(values: dict, error: str)`

#### `set_global_variable(var_name: str, new_value: str, pid: int)`
Sets a global variable value in a running process.
- **Parameters**:
  - `var_name`: Name of the variable to set
  - `new_value`: New value to assign
  - `pid`: Process ID to attach to
- **Returns**: `(success: bool, message: str)`
- **Safety**: Includes validation for allowed variables and value ranges

#### `periodic_global_var_report(interval: float, sio, client_id: str, watch_vars: str, pid: int, from_id: str)`
Continuously monitors global variables and reports changes.
- **Parameters**:
  - `interval`: Monitoring interval in seconds
  - `sio`: SocketIO instance for client communication
  - `client_id`: Runtime identifier
  - `watch_vars`: Variables to monitor
  - `pid`: Process ID to monitor
  - `from_id`: Client identifier for process tracking

### Process Management

#### `stop_client_processes(from_id: str)`
Stops all processes belonging to a specific client.
- **Parameters**: `from_id`: Client identifier
- **Returns**: `bool`: Success status

## License

This utility is part of the SDV Runtime project. See LICENSE file for details.

## Support

For issues related to:
- **Compilation**: Check C++ compiler installation and source code
- **GDB execution**: Verify GDB is installed and binary exists
- **Ptrace permissions**: Check system ptrace scope and Docker capabilities
- **Process attachment**: Ensure process is running and PID is correct
- **Variable reading**: Check that variables are properly declared as global
- **Process tracking**: Verify client ID consistency across operations
