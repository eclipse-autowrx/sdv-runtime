# VSS Array Support Tests

This test suite verifies the VSS (Vehicle Signal Specification) array support implementation that resolves issues with array datatype serialization and handling.

## Overview

The VSS array support implementation addresses critical issues with array datatypes in the SDV runtime environment, enabling proper serialization and handling of various array types including:

- Numeric arrays (uint8[], int32[], float[], etc.)
- String arrays (string[])
- Mixed array support
- Protobuf array object serialization

## Test Structure

- **string-array-serialization/**: Tests for string array quote escaping fix (Issue #1)

## Related Issues

- **Issue #26**: VSS arrays not being supported blocks implementation
- **Issue #1**: String array quote escaping problem

## Implementation Files

The array support is implemented in:
- `mock/lib/json_array_patch.py` - JSON serialization patch for mock service
- `kuksa-syncer/json_array_patch.py` - JSON serialization patch for kuksa syncer
- `mock/mockprovider.py` - Array datatype support in mock provider

## Quick Test Run

To run all VSS array support tests:

```bash
cd test/vss-array-support
./run_all_tests.sh
```

To run individual test categories:

```bash
cd string-array-serialization && python3 test_string_array_serialization.py
```

## Expected Behavior

### Before Array Support
- Array datatypes not supported (TypeError: Object of type Uint32Array is not JSON serializable)
- String arrays double-quoted: `["\"test\"","\"test\""]`
- VSS array controls blocked

### After Array Support
- All array datatypes properly supported
- String arrays correctly serialized: `["test","test"]`
- Priority-based actuator control working: `Vehicle.Body.Horn.HornControl.set([1,125])`

## Implementation Details

The array support adds:
- Custom JSON encoder for protobuf array objects
- Global JSON module patching
- String quote escaping fix
- Backward compatibility with existing code
- Support for engineio.json (socketio)