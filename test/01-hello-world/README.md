# Test 01: Hello World (Tree Structure Format)

## Purpose
Basic C++ compilation test using **tree structure format** to verify fundamental functionality.

## What This Tests
- Basic C++ compilation
- Tree structure format input with nested folder/file objects
- Simple program execution
- Output verification

## Files
- `main.cpp` - Simple Hello World program

## Tree Structure Format
```javascript
[{
  type: "folder",
  name: "src",
  items: [
    {type: "file", name: "main.cpp", content: "..."}
  ]
}]
```

## Expected Behavior
1. Kit-Manager detects tree structure format
2. Converts to internal flat format
3. Compiles successfully
4. Creates executable in `output/` directory
5. Runs program and displays greeting
6. Completes with exit code 0

## Learning Objectives
- Understand tree structure format
- See automatic format conversion
- Verify C++ toolchain works with new format

## Run Test
```bash
cd 01-hello-world
node test.js
```

## Expected Output
```
Hello from SDV Runtime!
Basic C++ compilation works!
```