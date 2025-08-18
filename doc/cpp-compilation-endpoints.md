# C++ Compilation WebSocket Endpoints

## Overview
New C++ compilation service added to SDV Runtime Kit-Manager. Compile and run C++ code in real-time with multi-file support.

## Endpoint: `compile_cpp`

### Request Format
```javascript
socket.emit('compile_cpp', {
    files: {
        'main.cpp': 'C++ source code...',
        'utils/helper.h': 'Header file...',
        'vehicle/Vehicle.cpp': 'More source...'
    },
    app_name: 'MyApp',
    run: true  // optional: run after compilation
})
```

### Response Format
```javascript
socket.on('compile_cpp_reply', (response) => {
    // response.status: compilation phase
    // response.result: output text
    // response.isDone: true when finished
    // response.code: exit code (0 = success)
})
```

## Response Status Values

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

## Example Usage

### Simple Hello World
```javascript
const files = {
    'main.cpp': `
#include <iostream>
int main() {
    std::cout << "Hello SDV!" << std::endl;
    return 0;
}
`
}

socket.emit('compile_cpp', {
    files: files,
    app_name: 'HelloWorld',
    run: true
})
```

### Multi-file Project
```javascript
const files = {
    'main.cpp': `
#include "vehicle/Vehicle.h"
int main() {
    Vehicle car("SDV-001");
    car.start();
    return 0;
}
`,
    'vehicle/Vehicle.h': `
#pragma once
#include <string>
class Vehicle {
    std::string id;
public:
    Vehicle(const std::string& id);
    void start();
};
`,
    'vehicle/Vehicle.cpp': `
#include "Vehicle.h"
#include <iostream>
Vehicle::Vehicle(const std::string& id) : id(id) {}
void Vehicle::start() {
    std::cout << "Vehicle " << id << " started!" << std::endl;
}
`
}

socket.emit('compile_cpp', { files, app_name: 'VehicleApp', run: true })
```

## Frontend Implementation Tips

### Basic Output Display
```javascript
const [output, setOutput] = useState([])
const [isCompiling, setIsCompiling] = useState(false)

useEffect(() => {
    socket.on('compile_cpp_reply', (msg) => {
        setOutput(prev => [...prev, msg])
        
        if (msg.isDone) {
            setIsCompiling(false)
        }
    })
}, [])

const handleCompile = () => {
    setIsCompiling(true)
    setOutput([])
    socket.emit('compile_cpp', { files, app_name: 'Test', run: true })
}
```

### Progress Tracking
```javascript
const getPhase = (status) => {
    if (status.includes('configure')) return 'Configuring'
    if (status.includes('build')) return 'Building'
    if (status.includes('run')) return 'Running'
    return 'Preparing'
}

const isError = (status) => 
    status.includes('failed') || status.includes('err')
```

## Error Handling

### Common Errors
- `err: invalid` - Missing files or app_name
- `err-copy-folder` - File system error
- `err_write_files` - Cannot write source files
- `configure-failed` - CMake configuration failed
- `err_build` - General build error

### Error Response Example
```javascript
{
    status: "configure-failed",
    result: "CMake configuration failed with code 1\r\n",
    cmd: "compile_cpp",
    isDone: true,
    code: 1
}
```

## Testing the Endpoint

Use the test files in `/test/` directory for incremental learning:
- `/test/01-basic/` - Simple Hello World
- `/test/02-multi-file/` - Multi-file projects  
- `/test/03-complex/` - Advanced features

## Notes
- All Python endpoints (`messageToKit`) remain unchanged
- Files support subdirectories (e.g., `utils/helper.h`)
- CMake automatically finds headers and sources
- Executables saved to output directory
- Real-time streaming for live feedback