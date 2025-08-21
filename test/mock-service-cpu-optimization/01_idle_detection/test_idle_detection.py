#!/usr/bin/env python3
"""
Automated tests for mock service idle detection functionality.
"""

import os
import sys
import time
import unittest.mock as mock

# Add the mock directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../mock'))

# Set test environment variables
os.environ.setdefault('MOCK_IDLE_THRESHOLD', '2.0')  # 2 seconds for faster testing
os.environ.setdefault('MOCK_BASE_SLEEP', '0.1')
os.environ.setdefault('MOCK_IDLE_SLEEP', '0.5')

class TestIdleDetection:
    """Test class for idle detection functionality."""
    
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
    
    def test_initial_state(self):
        """Test that service initializes in correct state."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            assert not mock_service._is_idle, "Service should not be idle initially"
            assert mock_service._idle_threshold == 2.0, f"Expected threshold 2.0, got {mock_service._idle_threshold}"
            assert mock_service._base_sleep_duration == 0.1, f"Expected base sleep 0.1, got {mock_service._base_sleep_duration}"
            assert mock_service._idle_sleep_duration == 0.5, f"Expected idle sleep 0.5, got {mock_service._idle_sleep_duration}"
    
    def test_idle_threshold_detection(self):
        """Test that service enters idle mode after threshold."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Simulate time passage by setting last activity time in the past
            mock_service._last_activity_time = time.perf_counter() - 3.0  # 3 seconds ago
            
            # Check idle state
            is_idle = mock_service._check_idle_state()
            assert is_idle, "Service should be idle after threshold"
            assert mock_service._is_idle, "Service internal state should be idle"
    
    def test_activity_detection(self):
        """Test that service exits idle mode when activity is detected."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Set service to idle state
            mock_service._is_idle = True
            
            # Simulate activity
            mock_service._update_activity_timestamp()
            
            assert not mock_service._is_idle, "Service should exit idle mode after activity"
    
    def test_has_active_animations_method(self):
        """Test that _has_active_animations method exists and works."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Method should exist
            assert hasattr(mock_service, '_has_active_animations'), "Should have _has_active_animations method"
            
            # Should return False when no datapoints
            assert not mock_service._has_active_animations(), "Should return False with no datapoints"
    
    def test_environment_configuration(self):
        """Test that environment variables configure the service properly."""
        # Set custom environment variables
        os.environ['MOCK_IDLE_THRESHOLD'] = '5.0'
        os.environ['MOCK_BASE_SLEEP'] = '0.2'
        os.environ['MOCK_IDLE_SLEEP'] = '2.0'
        
        # Re-import to get updated env vars
        import importlib
        import mockservice
        importlib.reload(mockservice)
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = mockservice.MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            assert mock_service._idle_threshold == 5.0, f"Expected 5.0, got {mock_service._idle_threshold}"
            assert mock_service._base_sleep_duration == 0.2, f"Expected 0.2, got {mock_service._base_sleep_duration}"
            assert mock_service._idle_sleep_duration == 2.0, f"Expected 2.0, got {mock_service._idle_sleep_duration}"
        
        # Reset environment for other tests
        os.environ['MOCK_IDLE_THRESHOLD'] = '2.0'
        os.environ['MOCK_BASE_SLEEP'] = '0.1'
        os.environ['MOCK_IDLE_SLEEP'] = '0.5'
    
    def run_all_tests(self):
        """Run all idle detection tests."""
        print("=== Mock Service Idle Detection Tests ===")
        
        tests = [
            ("Initial State", self.test_initial_state),
            ("Idle Threshold Detection", self.test_idle_threshold_detection),
            ("Activity Detection", self.test_activity_detection),
            ("Active Animations Method", self.test_has_active_animations_method),
            ("Environment Configuration", self.test_environment_configuration),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        print(f"\n=== Results ===")
        print(f"Passed: {passed}/{len(tests)}")
        
        if passed == len(tests):
            print("🎉 All idle detection tests passed!")
            return True
        else:
            print("❌ Some idle detection tests failed!")
            return False

if __name__ == "__main__":
    tester = TestIdleDetection()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)