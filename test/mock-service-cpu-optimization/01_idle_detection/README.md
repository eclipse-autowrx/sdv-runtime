# Test 01: Idle Detection

This test verifies the idle detection mechanism works correctly.

## Purpose

Validates that the mock service can:
- Detect when it should enter idle mode based on inactivity threshold
- Exit idle mode when activity is detected
- Properly configure idle parameters from environment variables

## Test Cases

1. **Initial State**: Service starts in non-idle state
2. **Idle Threshold**: Service enters idle mode after configured inactivity period
3. **Activity Detection**: Service exits idle mode when activity occurs
4. **Environment Configuration**: Idle parameters are correctly read from environment variables
5. **State Transitions**: Proper logging of idle mode transitions

## How to Run

### Automated Test
```bash
cd test/mock-service-cpu-optimization/01_idle_detection
python3 test_idle_detection.py
```

### Manual Test
```bash
# Set fast idle threshold for testing
export MOCK_IDLE_THRESHOLD=3.0
export MOCK_BASE_SLEEP=0.1  
export MOCK_IDLE_SLEEP=0.5

cd test/mock-service-cpu-optimization/01_idle_detection
python3 manual_idle_test.py
```

## Expected Results

- ✅ Service initializes in non-idle state
- ✅ Service enters idle mode after threshold period
- ✅ Idle mode transition is logged
- ✅ Service exits idle mode when activity detected
- ✅ Environment variables properly configure behavior
- ✅ Activity timestamp updates correctly

## Files

- `test_idle_detection.py`: Automated unit tests
- `manual_idle_test.py`: Interactive manual test script
- `README.md`: This documentation