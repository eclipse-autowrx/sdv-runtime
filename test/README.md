# C++ Compilation Test Suite

A comprehensive test suite for the SDV Runtime C++ compilation service using **tree structure** input format with progressive complexity.

## Test Structure Overview

```
test/
├── 01-hello-world/          # Basic Hello World (tree format)
├── 02-tree-format/          # Tree structure demonstration
├── 03-multi-file-tree/      # Multi-file project (tree format)
├── 06-automotive-basic/     # Basic automotive example
├── 08-stl-containers/       # STL usage (vectors, maps, etc.)
├── 09-error-handling/       # Compilation error scenarios
└── utils/                   # Shared utilities
```

## Quick Start

### 1. Start SDV Runtime Container
```bash
# Create output directory
mkdir -p output && chmod 777 output

# Run container with tree structure support
docker run -d \
  --name sdv-runtime-test \
  --user root \
  -p 3090:3090 \
  -p 55555:55555 \
  -v "$(pwd)/output:/home/dev/data/output:rw" \
  sdv-runtime-production:latest

# Wait for services to start
sleep 20

# Verify Kit-Manager is running
docker logs sdv-runtime-test | grep "Kit Manager"
```

### 2. Install Dependencies
```bash
npm install socket.io-client
```

### 3. Run Tests

#### Individual Tests
```bash
# Start simple
cd 01-hello-world && node test.js

# Try tree format
cd 02-tree-format && node test.js

# Multi-file examples
cd 03-multi-file-flat && node test.js
cd 04-multi-file-tree && node test.js
```

#### All Tests
```bash
# Run complete test suite
node run-all-tests.js

# Run specific category
node run-all-tests.js --category basic     # Tests 01-04
node run-all-tests.js --category advanced  # Tests 05-08
node run-all-tests.js --category edge      # Tests 09-10
```

## Test Categories

### **Basic Tests (01-03)**
- **Learning Goal**: Understand tree structure format
- **Complexity**: Single to multi-file projects
- **Focus**: Tree format usage, basic compilation

### **Advanced Tests (06-08)**
- **Learning Goal**: Real-world C++ features
- **Complexity**: Multiple files with dependencies
- **Focus**: Include paths, STL usage, automotive domain

### **Edge Cases (09)**
- **Learning Goal**: Error handling
- **Complexity**: Compilation errors, debugging
- **Focus**: Error reporting, troubleshooting

## Test Format Standards

Each test folder contains:
- **`test.js`** - Node.js test runner
- **`README.md`** - Test-specific documentation
- **`*.cpp`, `*.h`** - Source files
- **`expected-output.txt`** - Expected program output (optional)

### Test Script Template
```javascript
const io = require('socket.io-client');
const testConfig = require('../utils/test-config');

const TEST_NAME = 'Test Name';
const FILES = [
  // Tree structure format
];

testConfig.runTest({
  testName: TEST_NAME,
  files: FILES,
  appName: 'TestApp',
  run: true,
  timeout: 30000
});
```

## Input Format Examples

### Tree Structure Format
```javascript
const files = [
  {
    type: "folder",
    name: "src",
    items: [
      {
        type: "file",
        name: "main.cpp",
        content: "C++ code..."
      },
      {
        type: "folder",
        name: "utils",
        items: [
          {
            type: "file",
            name: "helper.h",
            content: "Header content..."
          },
          {
            type: "file",
            name: "helper.cpp", 
            content: "Implementation..."
          }
        ]
      }
    ]
  }
];
```

## Expected Outputs

All compiled binaries are saved to the `output/` directory with format:
```
output/app_SOCKET_ID
```

### Verification Commands
```bash
# List generated binaries
ls -la output/

# Check binary type
file output/app_*

# Execute binary (if compatible)
./output/app_XXXXX

# Copy for analysis
cp output/app_* /path/to/analysis/
```

## Container Management

```bash
# Check logs
docker logs sdv-runtime-test

# Stop and remove
docker stop sdv-runtime-test && docker rm sdv-runtime-test

# Restart fresh
docker rm -f sdv-runtime-test
docker run -d --name sdv-runtime-test --user root \
  -p 3090:3090 -p 55555:55555 \
  -v "$(pwd)/output:/home/dev/data/output:rw" \
  sdv-runtime-production:latest
```

## Troubleshooting

### Common Issues

#### 1. Container Not Starting
```bash
# Remove existing container
docker rm -f sdv-runtime-test

# Pull fresh image
docker pull ghcr.io/eclipse-autowrx/sdv-runtime:cpp-test-latest
```

#### 2. Permission Errors
```bash
# Fix output directory permissions
chmod 777 output

# Ensure container runs as root
docker run --user root ...
```

#### 3. Test Timeouts
```bash
# Increase wait time
sleep 30

# Check Kit-Manager status
docker logs sdv-runtime-test | grep "listening on port"
```

#### 4. Connection Failures
```bash
# Test WebSocket connectivity
curl -s "http://localhost:3090/socket.io/?EIO=4&transport=polling"

# Expected: JSON response with session ID
```

## Performance Expectations

| Test | Files | Build Time | Binary Size |
|------|-------|------------|-------------|
| 01-02 | 1 | < 1s | ~20KB |
| 03-04 | 3-5 | 1-2s | ~25KB |
| 05-06 | 5-8 | 2-3s | ~30KB |
| 07-08 | 8-12 | 3-5s | ~40KB |
| 09-10 | 15+ | 5-10s | ~50KB+ |

## Development Notes

- **Tree Structure**: Hierarchical organization for better project structure
- **Path Handling**: Automatic nested path creation from tree structure
- **CMake Integration**: Automatically finds headers and sources
- **Error Reporting**: Real-time streaming of compilation output
- **Format Requirement**: Tree structure format is required for all projects

---

**Next Steps**: Start with `01-hello-world` and progress through the numbered tests to learn tree structure format and C++ compilation features.