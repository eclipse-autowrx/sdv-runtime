# C++ Compilation Testing Guide

Frontend developers: Use these incremental tests to learn and experiment with the new C++ compilation endpoints.

## Test Structure

```
test/
├── 01-basic/          # Start here - Simple C++ compilation
├── 02-multi-file/     # Multi-file C++ projects
├── 03-complex/        # Advanced automotive examples  
└── scripts/           # Ready-to-use test scripts
```

## Quick Start

```bash
# 1. Start container (see main README)
docker run -d -p 3090:3090 sdv-runtime-production:latest

# 2. Install dependencies
npm install socket.io-client

# 3. Run basic test
cd test/scripts
node basic-test.js
```

## Learning Path

1. **01-basic/** - Learn endpoint basics with Hello World
2. **02-multi-file/** - Understand multi-file compilation  
3. **03-complex/** - Explore automotive C++ features
4. **scripts/** - Copy and modify for your frontend

Each folder contains:
- `README.md` - Quick guide
- `*.cpp`, `*.h` - Source files to send
- `test-*.js` - Working WebSocket examples