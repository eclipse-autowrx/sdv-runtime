# Test 03: Multi-file Project (Tree Structure Format)

## Purpose
Test multi-file C++ project compilation using tree structure format with proper include paths and dependencies.

## What This Tests
- Multiple source files (.cpp)
- Header files (.h) 
- Cross-file dependencies
- Include path resolution
- Class implementations across files
- CMake automatic source discovery

## Project Structure
```
main.cpp                 # Entry point
math/calculator.h        # Calculator class declaration  
math/calculator.cpp      # Calculator implementation
utils/logger.h           # Logger class declaration
utils/logger.cpp         # Logger implementation
```

## Features Demonstrated
- **Object-Oriented Design**: Calculator and Logger classes
- **Header/Implementation Separation**: .h/.cpp file pairs
- **Directory Organization**: math/ and utils/ folders
- **Cross-Module Dependencies**: main.cpp uses both modules
- **Static Methods**: Logger utility functions

## Learning Objectives
- Understand multi-file project structure  
- See how tree structure converts to proper paths
- Learn C++ class organization patterns
- Verify CMake handles complex builds

## Run Test
```bash
cd 03-multi-file-tree
node test.js
```

## Expected Build Process
1. All 5 files written to container
2. CMake finds headers and sources automatically
3. Builds executable with proper linking
4. Runs and displays calculation result

## Expected Output
```
[INFO] Multi-file project starting
10 + 5 = 15
[INFO] Multi-file project completed
```

## Success Criteria
- All files compile without errors
- Include paths resolve correctly
- Classes instantiate and methods work
- Logger outputs appear in correct format