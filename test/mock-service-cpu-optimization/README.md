# Mock Service CPU Optimization Tests

This test suite verifies the CPU optimization implementation for the mock service (Issue #29).

## Overview

The optimization introduces idle detection and dynamic sleep intervals to reduce CPU usage when the mock service is not actively processing events or animations.

## Test Structure

- **01_idle_detection/**: Tests for the idle detection mechanism
- **02_functionality_verification/**: Tests to ensure existing functionality remains intact
- **03_performance_validation/**: Performance and CPU usage validation tests

## Environment Variables

The following environment variables can be used to configure the mock service behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_IDLE_THRESHOLD` | 30.0 | Seconds of inactivity before entering idle mode |
| `MOCK_BASE_SLEEP` | 0.1 | Sleep duration in seconds when active |
| `MOCK_IDLE_SLEEP` | 1.0 | Sleep duration in seconds when idle |

## Quick Test Run

To run all tests:

```bash
cd test/mock-service-cpu-optimization
./run_all_tests.sh
```

To run individual test categories:

```bash
cd 01_idle_detection && python3 test_idle_detection.py
cd 02_functionality_verification && python3 test_functionality.py  
cd 03_performance_validation && python3 test_performance.py
```

## Expected Behavior

### Before Optimization
- Mock service runs continuous loop with 0.1s sleep
- CPU usage remains constant regardless of activity
- ~10 Hz polling frequency

### After Optimization
- Service enters idle mode after 30s of inactivity (configurable)
- Sleep interval increases to 1.0s when idle (~1 Hz polling)
- Immediately exits idle mode when activity detected
- Maintains full responsiveness during active periods

## Implementation Details

The optimization adds:
- Activity timestamp tracking
- Idle state detection
- Dynamic sleep interval adjustment
- Activity detection for events, animations, and datapoint updates