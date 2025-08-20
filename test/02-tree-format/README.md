# Test 02: Hello World (Tree Structure Format)

## Purpose
Same functionality as Test 01 but using **tree structure format** to demonstrate format compatibility.

## What This Tests
- Tree structure format input (array with type/items)
- Automatic format detection and conversion
- Same compilation result as flat format
- Backward compatibility verification

## Format Comparison
**Test 01 (Flat):**
```javascript
{'main.cpp': 'content'}
```

**Test 02 (Tree):**
```javascript
[{type: "folder", name: "project", items: [{type: "file", name: "main.cpp", content: "content"}]}]
```

## Expected Behavior
1. Kit-Manager detects tree structure
2. Automatically converts to flat format
3. Compiles identically to Test 01
4. Same performance and output

## Learning Objectives
- Understand tree structure format
- See automatic format conversion
- Compare with flat format results
- Verify no performance impact

## Run Test
```bash
cd 02-tree-format
node test.js
```

## Expected Output
```
Hello from Tree Structure!
Tree format compilation works!
```

## Success Criteria
- Same build time as Test 01
- Same binary size as Test 01
- Kit-Manager logs show format conversion