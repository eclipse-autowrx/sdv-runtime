# CI/CD Automated Testing

Automated test suite for C++ compilation service designed for GitHub Actions and other CI/CD systems.

## Files

- `automated-test-suite.js` - Comprehensive Node.js test suite
- `run-tests.sh` - Shell script for CI/CD environments  
- `cpp-compilation-test.yml` - GitHub Actions workflow
- `README.md` - This file

## Quick Usage

### GitHub Actions
The workflow runs automatically on push/PR to main branch.

### Local Testing
```bash
# Start container first
docker run -d -p 3090:3090 --name sdv-runtime-container sdv-runtime-production:latest

# Run automated tests
cd test/ci
./run-tests.sh

# Or run Node.js suite directly
node automated-test-suite.js
```

### CI/CD Integration
```bash
# Custom server URL and timeout
SDV_SERVER_URL=http://localhost:3090 TEST_TIMEOUT=30000 ./run-tests.sh
```

## Test Coverage

### Automated Test Suite (`automated-test-suite.js`)
- ✅ Connection Test
- ✅ Basic Compilation 
- ✅ Multi-File Projects
- ✅ Complex Automotive Algorithms
- ✅ Error Handling (negative tests)
- ✅ Performance Benchmarks

### Individual Tests
- Connection verification
- Simple C++ compilation
- Multi-file project compilation
- Complex automotive examples
- Executable generation validation

## Exit Codes
- `0` - All tests passed
- `1` - One or more tests failed

## Environment Variables
- `SDV_SERVER_URL` - Server URL (default: http://localhost:3090)
- `TEST_TIMEOUT` - Timeout in ms (default: 60000)

## GitHub Actions Features
- Automatic container build and startup
- Service health checks
- Test result reporting
- Artifact validation
- Proper cleanup on failure

## Performance Requirements
- Connection: < 10 seconds
- Basic compilation: < 30 seconds  
- Multi-file projects: < 45 seconds
- Complex examples: < 60 seconds
- Overall suite: < 5 minutes