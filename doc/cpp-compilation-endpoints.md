# C++ Compilation WebSocket Endpoints

## Overview
C++ compilation service for SDV Runtime Kit-Manager. Compile and run C++ code in real-time using hierarchical tree structure format.

## Endpoint: `compile_cpp`

### Request Format

The `compile_cpp` endpoint uses **tree structure format**:
```javascript
socket.emit('compile_cpp', {
    files: [
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
                            content: "Header file..."
                        }
                    ]
                }
            ]
        }
    ],
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

### Multi-file Project (Tree Structure)
```javascript
const files = [
    {
        type: "folder",
        name: "project",
        items: [
            {
                type: "file",
                name: "main.cpp",
                content: `#include "vehicle/Vehicle.h"
int main() {
    Vehicle car("SDV-001");
    car.start();
    return 0;
}`
            },
            {
                type: "folder",
                name: "vehicle", 
                items: [
                    {
                        type: "file",
                        name: "Vehicle.h",
                        content: `#pragma once
#include <string>
class Vehicle {
    std::string id;
public:
    Vehicle(const std::string& id);
    void start();
};`
                    },
                    {
                        type: "file", 
                        name: "Vehicle.cpp",
                        content: `#include "Vehicle.h"
#include <iostream>
Vehicle::Vehicle(const std::string& id) : id(id) {}
void Vehicle::start() {
    std::cout << "Vehicle " << id << " started!" << std::endl;
}`
                    }
                ]
            }
        ]
    }
];

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

Use the comprehensive test suite in `/test/` directory for progressive learning:

### Basic Tests
- `/test/01-hello-world/` - Simple Hello World (tree format)
- `/test/02-tree-format/` - Tree structure demonstration
- `/test/03-multi-file-tree/` - Multi-file project (tree format)
- `/test/04-multi-file-tree/` - Multi-file with nested folders

### Advanced Tests  
- `/test/06-automotive-basic/` - Vehicle simulation with classes
- `/test/08-stl-containers/` - STL containers and algorithms

### Edge Cases
- `/test/09-error-handling/` - Compilation error scenarios

### Running Tests
```bash
# Run all tests
node test/run-all-tests.js

# Run specific category
node test/run-all-tests.js --category=basic
node test/run-all-tests.js --category=advanced
node test/run-all-tests.js --category=edge

# Run single test
node test/run-all-tests.js 01-hello-world
```

## Tree Structure Format

The Kit-Manager uses hierarchical tree structure format for better project organization:

### Structure Requirements
- Root array containing folder/file objects
- Each object must have `type` property (`"file"` or `"folder"`)
- Files require `name` and `content` properties
- Folders require `name` and `items` array

### Conversion Process
1. Tree structure is parsed recursively
2. Files are flattened with proper path separators
3. Compilation proceeds with CMake auto-detection
4. Headers and sources automatically linked

### Example Tree Structure Patterns
```javascript
// Pattern 1: Single root folder
[{type: "folder", name: "src", items: [...]}]

// Pattern 2: Direct file array 
[{type: "file", name: "main.cpp", content: "..."}]

// Pattern 3: Mixed structure
[
    {type: "file", name: "main.cpp", content: "..."},
    {type: "folder", name: "utils", items: [...]}
]
```

## Notes
- **Tree Structure Only**: Only hierarchical format supported
- **Path Handling**: Automatic nested path creation from tree structure
- All Python endpoints (`messageToKit`) remain unchanged
- CMake automatically finds headers and sources
- Executables saved to output directory
- Real-time streaming for live feedback