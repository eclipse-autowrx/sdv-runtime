# Syncer C++ Compilation Feature

## Overview

This feature adds C++ compilation support to the syncer.py middleware layer, enabling production web frontends to compile and execute C++ code through the SDV Runtime architecture.

## Architecture

```
Web Frontend → syncer.py (port 55555) → Kit-Manager (port 3090) → C++ Compilation
```

### Communication Flow

1. **Web Frontend** sends `messageToKit` event with `compile_cpp_app` command
2. **syncer.py** receives command, validates request, forwards to Kit-Manager
3. **Kit-Manager** processes C++ compilation using existing tree structure format
4. **Kit-Manager** streams compilation status back to syncer.py
5. **syncer.py** forwards status updates back to Web Frontend

## Command Format

### Request (Web Frontend → syncer.py)

```javascript
{
  cmd: "compile_cpp_app",
  request_from: "unique-client-id",
  data: {
    files: [
      // Tree structure format (same as direct Kit-Manager)
      {
        type: "folder",
        name: "src", 
        items: [
          {
            type: "file",
            name: "main.cpp",
            content: "C++ source code..."
          },
          {
            type: "folder",
            name: "utils",
            items: [
              {
                type: "file", 
                name: "helper.h",
                content: "Header content..."
              }
            ]
          }
        ]
      }
    ],
    app_name: "MyApplication",
    run: true  // optional: execute after compilation
  }
}
```

### Response (syncer.py → Web Frontend)

```javascript
{
  kit_id: "RunTime-MyRuntime",
  request_from: "unique-client-id", 
  cmd: "compile_cpp_app",
  status: "compile-start|build-done|run-done|...",
  result: "compilation output...",
  data: "",
  isDone: false|true,
  code: 0|1
}
```

## Status Values

| Status | Description | isDone |
|--------|-------------|---------|
| `compile-start` | Compilation started | false |
| `file-written` | File written to container | false |
| `configure-stdout` | CMake configuration output | false |
| `configure-stderr` | CMake configuration errors | false |
| `configure-failed` | CMake failed | true |
| `build-stdout` | Make build output | false |
| `build-stderr` | Make build errors | false |
| `build-done` | Build completed | true/false* |
| `run-stdout` | Program output | false |
| `run-stderr` | Program errors | false |
| `run-done` | Program finished | true |

*`build-done` isDone is false if `run: true` was requested

## Implementation Details

### syncer.py Changes

1. **New imports**: socketio client for Kit-Manager connection
2. **Global variables**: 
   - `kit_manager_sio`: Socket connection to Kit-Manager
   - `KIT_MANAGER_URL`: Kit-Manager endpoint (http://127.0.0.1:3090)

3. **New functions**:
   - `send_cpp_compile_reply()`: Format and send responses back to web client
   - `compile_cpp_app` handler in `messageToKit()`: Process C++ compilation requests

4. **Connection management**: Lazy initialization of Kit-Manager socket connection

### Error Handling

- **Invalid request**: Missing files or app_name
- **Connection errors**: Failed to connect to Kit-Manager
- **Compilation errors**: Forwarded from Kit-Manager
- **Runtime errors**: Exception handling with meaningful messages

## Testing

### Validation Results ✅

1. **Direct Function Test**: `messageToKit()` processes requests successfully
2. **Kit-Manager Integration**: Successfully connects and forwards requests
3. **Compilation Success**: C++ code compiles and generates executables
4. **Execution Verification**: Compiled binaries run with expected output

### Test Files Created

```
test/syncer-cpp-tests/
├── utils/
│   ├── syncer-test-config.js     # Test utilities
│   ├── mock-kit-server.js        # Mock server for testing
│   └── direct-test-in-container.py  # Direct validation script
├── 01-basic-hello/               # Basic hello world test
├── 02-multi-file/                # Multi-file project test  
├── 03-error-handling/            # Error scenario test
└── run-all-tests.js              # Test suite runner
```

### Running Tests

```bash
# Direct validation (inside container)
python3 /tmp/direct-test-in-container.py

# Full test suite (requires specific syncer configuration)  
node test/syncer-cpp-tests/run-all-tests.js
```

## Configuration

### Environment Variables

- `SYNCER_SERVER_URL`: Kit server URL (default: https://kit.digitalauto.tech)
- `RUNTIME_NAME`: Runtime identifier (default: MyRuntime)
- `KIT_MANAGER_PORT`: Kit-Manager port (default: 3090)

### Dependencies

- `python3-socketio`: For Kit-Manager communication
- Existing Kit-Manager with C++ compilation support
- CMake, Make, GCC/G++ (already available in container)

## Production Usage

### Frontend Integration

```javascript
// Connect to syncer.py
const socket = io('http://your-runtime:55555');

// Send compilation request
socket.emit('messageToKit', {
  cmd: 'compile_cpp_app',
  request_from: 'web-client-123',
  data: {
    files: treeStructureFiles,
    app_name: 'UserApp', 
    run: true
  }
});

// Listen for responses
socket.on('messageToKit-kitReply', (response) => {
  if (response.cmd === 'compile_cpp_app' && response.request_from === 'web-client-123') {
    console.log(`[${response.status}] ${response.result}`);
    
    if (response.isDone) {
      const success = response.code === 0;
      console.log(`Compilation ${success ? 'succeeded' : 'failed'}`);
    }
  }
});
```

### Docker Deployment

The feature is now integrated into the standard SDV Runtime container:

```bash
docker run -d \
  --name sdv-runtime \
  -p 55555:55555 \
  -p 3090:3090 \
  -v "./output:/home/dev/data/output:rw" \
  sdv-runtime-production:latest
```

## Security Considerations

- **Input validation**: Tree structure format validated before processing
- **Resource limits**: Compilation runs in isolated container environment  
- **Output isolation**: Compiled binaries saved to mounted output directory
- **Network isolation**: Kit-Manager communication remains internal

## Benefits

1. **Production Ready**: Web frontends can use C++ compilation in production
2. **Consistent API**: Same tree structure format as direct Kit-Manager access
3. **Real-time Feedback**: Streaming compilation status updates
4. **Error Handling**: Comprehensive error reporting and recovery
5. **Resource Management**: Proper connection handling and cleanup

## Migration Notes

- **Existing Python workflows**: Unchanged, continue to work as before
- **Direct Kit-Manager access**: Still supported for testing/development
- **Tree structure format**: Identical to direct Kit-Manager implementation
- **Response format**: Enhanced with syncer-specific fields (kit_id, etc.)

---

**Status**: ✅ **Feature Complete and Tested**  
**Branch**: `feature/syncer-cpp-compilation`  
**Integration**: Ready for merge to main