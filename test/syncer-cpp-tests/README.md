# Syncer C++ Compilation Test Suite

Test suite for validating C++ compilation through the syncer.py middleware layer.

## Architecture Being Tested

```
Web Client → syncer.py (port 55555) → Kit-Manager (port 3090)
```

This tests the production communication flow where:
1. Web frontend sends `compile_cpp_app` commands to syncer.py
2. syncer.py forwards to Kit-Manager's `compile_cpp` endpoint  
3. Kit-Manager processes and streams results back through syncer.py
4. syncer.py forwards results to web client

## Test Structure

```
test/syncer-cpp-tests/
├── 01-basic-hello/          # Basic Hello World through syncer
├── 02-multi-file/           # Multi-file project through syncer  
├── 03-error-handling/       # Error scenarios through syncer
├── 04-concurrent/           # Multiple simultaneous requests
└── utils/                   # Shared test utilities
```

## Running Tests

### Method 1: Mock Kit Server (Recommended)

This method properly tests the production architecture by simulating the external kit server:

```bash
# Install dependencies
npm install socket.io socket.io-client

# Run the mock kit server test
cd test/syncer-cpp-tests
node mock-server-test.js
```

**How it works:**
1. Starts a mock kit server on port 3091
2. Launches SDV runtime container configured to connect to the mock server
3. syncer.py connects to mock server instead of kit.digitalauto.tech
4. Sends C++ compilation commands through the mock server
5. Receives real-time compilation status back from syncer.py

### Method 2: Direct Function Testing

For quick validation during development:

```bash
# Start regular SDV runtime container
docker run -d --name sdv-runtime-test --user root \
  -p 3090:3090 -p 55555:55555 \
  -v "$(pwd)/output:/home/dev/data/output:rw" \
  sdv-runtime-production:latest

# Copy and run direct test script inside container
docker cp test/syncer-cpp-tests/utils/direct-test-in-container.py sdv-runtime-test:/tmp/
docker exec sdv-runtime-test python3 /tmp/direct-test-in-container.py

# Cleanup
docker stop sdv-runtime-test && docker rm sdv-runtime-test
```

### Integration Test

```bash
node test/syncer-cpp-tests/integration-test.js
```

## Key Differences from Direct Kit-Manager Tests

- **Architecture**: Mock Kit Server → syncer.py → Kit-Manager (not direct to Kit-Manager)
- **Command**: Uses `messageToKit` event with `compile_cpp_app` command
- **Response**: Receives `messageToKit-kitReply` events with compilation status
- **Configuration**: syncer.py configured with mock server URL via environment variable
- **Testing**: Validates production middleware layer instead of direct compilation service

## Test Data Format

```javascript
// Message sent to syncer.py
{
  cmd: "compile_cpp_app",
  request_from: "test-client-123", 
  data: {
    files: [/* tree structure */],
    app_name: "TestApp",
    run: true
  }
}

// Response from syncer.py  
{
  kit_id: "runtime-kit-id",
  request_from: "test-client-123",
  cmd: "compile_cpp_app", 
  status: "compile-start|build-done|run-done|...",
  result: "compilation output...",
  isDone: false|true,
  code: 0|1
}
```