# Syncer Lite

A simplified version of the syncer that focuses only on core functionality: receiving remote commands and executing Python applications with real-time output reporting.

## Features

- ✅ **Real-time stdout/stderr streaming** - Get output as soon as it's generated
- ✅ **Remote command execution** - Execute Python apps from remote server
- ✅ **Process management** - Start, stop, and monitor processes
- ✅ **Automatic cleanup** - Clean up old processes automatically
- ✅ **Error handling** - Robust error handling and reporting
- ✅ **Lightweight** - Minimal dependencies and simple architecture

## Architecture

```
Remote Server (Socket.IO) 
    ↓
syncer_lite.py (receives commands)
    ↓
pexpect_util.py (executes processes)
    ↓
Python Process (your app)
    ↓
Real-time output → Remote Server
```

## Components

### 1. `syncer_lite.py`
The main lite syncer that:
- Connects to Socket.IO server
- Receives remote commands
- Manages Python process execution
- Reports real-time output back to server

### 2. `pexpect_util.py`
A comprehensive utility that:
- Wraps pexpect for subprocess management
- Provides real-time stdout/stderr streaming
- Handles process lifecycle (start, stop, monitor)
- Drop-in replacement for the original `subpiper`

## Usage

### Basic Usage

```bash
# Run the lite syncer
python syncer_lite.py
```

### Environment Variables

```bash
# Server URL (default: https://kit.digitalauto.tech)
export SYNCER_SERVER_URL="https://your-server.com"

# Runtime name (default: LiteRuntime)
export RUNTIME_NAME="MyLiteRuntime"
```

### Testing

```bash
# Test the functionality locally
python test_syncer_lite.py
```

## Supported Commands

### 1. `run_python_app`
Execute a Python application with real-time output.

**Request:**
```json
{
  "cmd": "run_python_app",
  "request_from": "client123",
  "data": {
    "code": "print('Hello World')\nfor i in range(5):\n    print(f'Count: {i}')",
    "name": "MyApp"
  }
}
```

**Response (real-time):**
```json
{
  "kit_id": "LiteRuntime-MyLiteRuntime",
  "request_from": "client123",
  "cmd": "run_python_app",
  "isDone": false,
  "result": "Starting MyApp...\r\n",
  "code": 0
}
```

### 2. `stop_python_app`
Stop a running Python application.

**Request:**
```json
{
  "cmd": "stop_python_app",
  "request_from": "client123"
}
```

### 3. `get-runtime-info`
Get information about running processes.

**Request:**
```json
{
  "cmd": "get-runtime-info",
  "request_from": "client123"
}
```

**Response:**
```json
{
  "kit_id": "LiteRuntime-MyLiteRuntime",
  "request_from": "client123",
  "cmd": "get-runtime-info",
  "data": {
    "lsOfRunner": [
      {
        "appName": "MyApp",
        "request_from": "client123",
        "from": 1640995200.0,
        "pid": 12345,
        "state": "running"
      }
    ],
    "total_runners": 1
  }
}
```

## Key Differences from Full Syncer

| Feature | Full Syncer | Lite Syncer |
|---------|-------------|-------------|
| Python app execution | ✅ | ✅ |
| Real-time output | ✅ | ✅ |
| Process management | ✅ | ✅ |
| Mock signals | ✅ | ❌ |
| Vehicle model generation | ✅ | ❌ |
| Package management | ✅ | ❌ |
| Binary app execution | ✅ | ❌ |
| API subscription | ✅ | ❌ |
| Complex VSS integration | ✅ | ❌ |

## Installation

### Dependencies

```bash
pip install pexpect socketio-client
```

### Optional Dependencies

```bash
# For process tree killing (optional)
pip install psutil
```

## Configuration

### Timeouts

```python
# In syncer_lite.py
TIME_TO_KEEP_RUNNER_ALIVE = 3 * 60  # 3 minutes
```

### Process Limits

The lite syncer automatically cleans up processes that have been running for more than 3 minutes.

## Error Handling

The lite syncer includes comprehensive error handling:

- **Process start failures** - Reported back to server
- **Process execution errors** - Captured and reported
- **Network disconnections** - Automatic reconnection attempts
- **Process cleanup** - Automatic cleanup of orphaned processes

## Security Considerations

- **Code execution** - Only executes Python code from trusted sources
- **Process isolation** - Each process runs in its own environment
- **Resource limits** - Automatic cleanup prevents resource exhaustion
- **Network security** - Uses secure Socket.IO connections

## Performance

The lite syncer is optimized for:

- **Low latency** - Real-time output streaming
- **Low memory usage** - Minimal overhead
- **High concurrency** - Multiple processes can run simultaneously
- **Fast startup** - Minimal initialization time

## Troubleshooting

### Common Issues

1. **Connection failed**
   - Check `SYNCER_SERVER_URL` environment variable
   - Verify network connectivity

2. **Process not starting**
   - Check Python installation
   - Verify code syntax

3. **Output not streaming**
   - Ensure `-u` flag is used with Python
   - Check pexpect installation

### Debug Mode

Add debug logging:

```python
# In syncer_lite.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 