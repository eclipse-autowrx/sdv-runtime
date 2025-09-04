# Test: String Array Serialization

This test verifies the string array quote escaping fix (Issue #1).

## Purpose

Validates that string arrays are properly serialized without extra quotes during JSON encoding.

## Background

**Issue #1 - String Array Quote Escaping**
- **Reporter**: Stoehr Frederik (BEG/EVC3-Wi)
- **Problem**: String arrays getting double-quoted during serialization
- **Input**: `['test','test']`
- **Before Fix**: `["\"test\"","\"test\""]` (extra escape quotes)
- **After Fix**: `["test","test"]` (correct)

## Test Cases

1. **Frederik's Specific Issue**: Direct reproduction of the reported problem
2. **Various String Scenarios**: Different string content types
3. **Backward Compatibility**: Ensures numeric arrays still work
4. **Edge Cases**: Empty strings, special characters, single elements

## How to Run

### Automated Test
```bash
cd test/vss-array-support/string-array-serialization
python3 test_string_array_serialization.py
```

### Manual Test
```bash
cd test/vss-array-support/string-array-serialization  
python3 manual_string_array_test.py
```

## Expected Results

- ✅ Frederik's exact scenario works correctly
- ✅ String arrays serialize without extra quotes
- ✅ Backward compatibility with numeric arrays maintained
- ✅ Various string scenarios handled properly
- ✅ Edge cases work as expected

## Implementation Details

The fix modifies the `ArrayJSONEncoder` in:
- `mock/lib/json_array_patch.py`
- `kuksa-syncer/json_array_patch.py`

Key changes:
- Added 'string' to array type detection
- Implemented quote removal for string values
- Enhanced protobuf-style string parsing

## Test Environment

The test simulates:
- Mock protobuf array objects with `.values` attribute
- Protobuf-style string representation parsing
- Global JSON module patching behavior
- Real-world usage scenarios

## Files

- `test_string_array_serialization.py`: Automated unit tests
- `manual_string_array_test.py`: Interactive manual test script  
- `README.md`: This documentation