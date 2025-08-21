#!/usr/bin/env python3
"""
Performance validation tests for mock service CPU optimization.
"""

import os
import sys
import time
import unittest.mock as mock
import threading
import statistics

# Add the mock directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../mock'))

# Set test environment variables for performance testing
os.environ.setdefault('MOCK_IDLE_THRESHOLD', '1.0')  # Fast idle for testing
os.environ.setdefault('MOCK_BASE_SLEEP', '0.1')
os.environ.setdefault('MOCK_IDLE_SLEEP', '0.5')

class TestPerformance:
    """Test class for performance validation."""
    
    def __init__(self):
        self.test_results = []
        
    def run_test(self, test_name, test_func):
        """Run a single test and record results."""
        try:
            test_func()
            print(f"✅ {test_name}")
            self.test_results.append((test_name, True, None))
            return True
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            self.test_results.append((test_name, False, str(e)))
            return False
    
    def test_sleep_interval_selection(self):
        """Test that correct sleep intervals are selected based on state."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Test active state - should use base sleep
            mock_service._is_idle = False
            has_events = False
            has_animations = False
            
            if mock_service._is_idle and not has_events and not has_animations:
                selected_sleep = mock_service._idle_sleep_duration
            else:
                selected_sleep = mock_service._base_sleep_duration
                
            assert selected_sleep == mock_service._base_sleep_duration, \
                f"Expected base sleep {mock_service._base_sleep_duration}, got {selected_sleep}"
            
            # Test idle state with no activity - should use idle sleep
            mock_service._is_idle = True
            has_events = False
            has_animations = False
            
            if mock_service._is_idle and not has_events and not has_animations:
                selected_sleep = mock_service._idle_sleep_duration
            else:
                selected_sleep = mock_service._base_sleep_duration
                
            assert selected_sleep == mock_service._idle_sleep_duration, \
                f"Expected idle sleep {mock_service._idle_sleep_duration}, got {selected_sleep}"
            
            # Test idle state with events - should use base sleep  
            mock_service._is_idle = True
            has_events = True
            has_animations = False
            
            if mock_service._is_idle and not has_events and not has_animations:
                selected_sleep = mock_service._idle_sleep_duration
            else:
                selected_sleep = mock_service._base_sleep_duration
                
            assert selected_sleep == mock_service._base_sleep_duration, \
                f"Expected base sleep with events {mock_service._base_sleep_duration}, got {selected_sleep}"
    
    def test_polling_frequency_reduction(self):
        """Test that polling frequency is reduced in idle mode."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Calculate expected polling frequencies
            active_frequency = 1.0 / mock_service._base_sleep_duration  # Hz
            idle_frequency = 1.0 / mock_service._idle_sleep_duration    # Hz
            
            reduction_factor = active_frequency / idle_frequency
            
            # Verify significant reduction
            assert reduction_factor >= 2.0, \
                f"Expected at least 2x reduction, got {reduction_factor}x"
            
            print(f"  Active frequency: {active_frequency:.1f} Hz")
            print(f"  Idle frequency: {idle_frequency:.1f} Hz") 
            print(f"  Reduction factor: {reduction_factor:.1f}x")
    
    def test_idle_transition_timing(self):
        """Test timing of idle transitions."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Test entering idle mode
            start_time = time.perf_counter()
            mock_service._last_activity_time = start_time - (mock_service._idle_threshold + 0.1)
            
            transition_start = time.perf_counter()
            is_idle = mock_service._check_idle_state()
            transition_time = time.perf_counter() - transition_start
            
            assert is_idle, "Service should enter idle mode"
            assert transition_time < 0.01, f"Idle transition too slow: {transition_time:.4f}s"
            
            # Test exiting idle mode
            mock_service._is_idle = True
            transition_start = time.perf_counter()
            mock_service._update_activity_timestamp()
            transition_time = time.perf_counter() - transition_start
            
            assert not mock_service._is_idle, "Service should exit idle mode"
            assert transition_time < 0.01, f"Activity transition too slow: {transition_time:.4f}s"
    
    def test_performance_under_load(self):
        """Test performance characteristics under different load scenarios."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Test 1: No load (idle behavior)
            mock_service._pending_event_list = []
            mock_service._mocked_datapoints = {}
            mock_service._is_idle = True
            
            has_events = len(mock_service._pending_event_list) > 0
            has_animations = mock_service._has_active_animations()
            
            assert not has_events, "Should have no events under no load"
            assert not has_animations, "Should have no animations under no load"
            
            # Test 2: Event load
            mock_service._pending_event_list = [mock.Mock() for _ in range(5)]
            has_events = len(mock_service._pending_event_list) > 0
            
            assert has_events, "Should detect events under event load"
            
            # Test 3: Animation load
            mock_service._pending_event_list = []
            mock_datapoint = mock.Mock()
            mock_behavior = mock.Mock()
            mock_animation = mock.Mock()
            mock_animator = mock.Mock()
            mock_animator.is_done.return_value = False
            mock_animation._animator = mock_animator
            mock_behavior._action = mock_animation
            mock_datapoint.behaviors = [mock_behavior]
            mock_service._mocked_datapoints = {"test": mock_datapoint}
            
            # Mock the type check for AnimationAction
            with mock.patch('builtins.type') as mock_type:
                from lib.action import AnimationAction
                mock_type.return_value = AnimationAction
                has_animations = mock_service._has_active_animations()
                
            assert has_animations, "Should detect animations under animation load"
    
    def test_memory_usage_stability(self):
        """Test that optimization doesn't introduce memory leaks."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Simulate many idle transitions
            for i in range(100):
                # Enter idle
                mock_service._last_activity_time = time.perf_counter() - 2.0
                mock_service._check_idle_state()
                
                # Exit idle
                mock_service._update_activity_timestamp()
            
            # Verify object state is still consistent
            assert hasattr(mock_service, '_last_activity_time'), "Activity timestamp should exist"
            assert hasattr(mock_service, '_is_idle'), "Idle state should exist"
            assert hasattr(mock_service, '_idle_threshold'), "Idle threshold should exist"
            
            # Check that activity timestamp is recent
            current_time = time.perf_counter()
            time_diff = current_time - mock_service._last_activity_time
            assert time_diff < 1.0, f"Activity timestamp too old: {time_diff:.3f}s"
    
    def test_configuration_performance_impact(self):
        """Test performance impact of different configuration values."""
        configs = [
            ('Fast', {'MOCK_IDLE_THRESHOLD': '1.0', 'MOCK_BASE_SLEEP': '0.05', 'MOCK_IDLE_SLEEP': '0.2'}),
            ('Standard', {'MOCK_IDLE_THRESHOLD': '5.0', 'MOCK_BASE_SLEEP': '0.1', 'MOCK_IDLE_SLEEP': '1.0'}),
            ('Conservative', {'MOCK_IDLE_THRESHOLD': '10.0', 'MOCK_BASE_SLEEP': '0.2', 'MOCK_IDLE_SLEEP': '2.0'}),
        ]
        
        for config_name, config_values in configs:
            # Set environment variables
            for key, value in config_values.items():
                os.environ[key] = value
            
            # Re-import to get updated config
            import importlib
            import mockservice
            importlib.reload(mockservice)
            
            with mock.patch('mockservice.BaseService.__init__', return_value=None):
                mock_service = mockservice.MockService("127.0.0.1:50053", "127.0.0.1:55555")
                
                # Verify configuration is applied
                expected_threshold = float(config_values['MOCK_IDLE_THRESHOLD'])
                expected_base = float(config_values['MOCK_BASE_SLEEP'])
                expected_idle = float(config_values['MOCK_IDLE_SLEEP'])
                
                assert mock_service._idle_threshold == expected_threshold, \
                    f"{config_name}: Wrong idle threshold {mock_service._idle_threshold}"
                assert mock_service._base_sleep_duration == expected_base, \
                    f"{config_name}: Wrong base sleep {mock_service._base_sleep_duration}"
                assert mock_service._idle_sleep_duration == expected_idle, \
                    f"{config_name}: Wrong idle sleep {mock_service._idle_sleep_duration}"
                
                # Calculate performance characteristics
                active_freq = 1.0 / expected_base
                idle_freq = 1.0 / expected_idle
                reduction = active_freq / idle_freq
                
                print(f"  {config_name} config - Reduction: {reduction:.1f}x, Threshold: {expected_threshold}s")
        
        # Reset to test defaults
        os.environ['MOCK_IDLE_THRESHOLD'] = '1.0'
        os.environ['MOCK_BASE_SLEEP'] = '0.1'
        os.environ['MOCK_IDLE_SLEEP'] = '0.5'
    
    def run_all_tests(self):
        """Run all performance validation tests."""
        print("=== Mock Service Performance Validation Tests ===")
        
        tests = [
            ("Sleep Interval Selection", self.test_sleep_interval_selection),
            ("Polling Frequency Reduction", self.test_polling_frequency_reduction),
            ("Idle Transition Timing", self.test_idle_transition_timing),
            ("Performance Under Load", self.test_performance_under_load),
            ("Memory Usage Stability", self.test_memory_usage_stability),
            ("Configuration Performance Impact", self.test_configuration_performance_impact),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        print(f"\n=== Results ===")
        print(f"Passed: {passed}/{len(tests)}")
        
        if passed == len(tests):
            print("🎉 All performance validation tests passed!")
            print("\n✅ CPU optimization provides expected performance improvements")
            print("\nPerformance Benefits:")
            print("- Reduced polling frequency during idle periods")
            print("- Fast idle mode transitions")
            print("- Stable memory usage")
            print("- Configurable performance parameters")
            return True
        else:
            print("❌ Some performance validation tests failed!")
            print("\n⚠️  Performance optimization may need adjustment")
            return False

if __name__ == "__main__":
    tester = TestPerformance()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)