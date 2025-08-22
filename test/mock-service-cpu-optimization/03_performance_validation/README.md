# Test 03: Performance Validation

This test validates the CPU usage improvements and performance characteristics of the optimized mock service.

## Purpose

Measures and validates:
- CPU usage reduction during idle periods
- Response time when exiting idle mode
- Sleep interval behavior in different states
- Overall performance impact of the optimization

## Test Cases

1. **Sleep Interval Validation**: Verify correct sleep durations are used
2. **Idle Mode CPU Impact**: Measure polling frequency reduction
3. **Response Time**: Test how quickly service exits idle mode
4. **Performance Metrics**: Compare before/after optimization behavior
5. **Load Testing**: Verify performance under different activity levels

## How to Run

### Automated Test
```bash
cd test/mock-service-cpu-optimization/03_performance_validation
python3 test_performance.py
```

### Manual Performance Test
```bash
cd test/mock-service-cpu-optimization/03_performance_validation
python3 manual_performance_test.py
```

### CPU Usage Monitoring Test
```bash
# This test requires the service to be running
cd test/mock-service-cpu-optimization/03_performance_validation
./monitor_cpu_usage.sh
```

## Expected Results

### Before Optimization
- Constant 0.1s sleep interval
- ~10 Hz polling frequency
- CPU usage remains constant regardless of activity

### After Optimization  
- 0.1s sleep when active, 1.0s when idle (10x reduction)
- ~10 Hz when active, ~1 Hz when idle
- Significant CPU usage reduction during idle periods
- Immediate response when activity detected

## Performance Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Idle polling frequency | 10 Hz | 1 Hz | 90% reduction |
| Sleep interval (idle) | 0.1s | 1.0s | 10x longer |
| CPU usage (idle) | High | Low | ~80-90% reduction |
| Response time | N/A | <1 cycle | Immediate |

## Files

- `test_performance.py`: Automated performance tests
- `manual_performance_test.py`: Interactive performance monitoring
- `monitor_cpu_usage.sh`: CPU usage monitoring script
- `README.md`: This documentation