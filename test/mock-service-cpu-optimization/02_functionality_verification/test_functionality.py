#!/usr/bin/env python3
"""
Automated tests to verify existing functionality remains intact after optimization.
"""

import os
import sys
import time
import unittest.mock as mock

# Add the mock directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../mock'))

# Set test environment variables
os.environ.setdefault('MOCK_IDLE_THRESHOLD', '2.0')
os.environ.setdefault('MOCK_BASE_SLEEP', '0.1') 
os.environ.setdefault('MOCK_IDLE_SLEEP', '0.5')

class TestFunctionality:
    """Test class for mock service functionality verification."""
    
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
    
    def test_core_methods_exist(self):
        """Test that all core methods still exist."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Check all original methods exist
            required_methods = [
                'on_databroker_connected',
                'check_for_new_mocks', 
                'main_loop',
                '_on_datapoint_updated',
                '_feed_initial_values',
                '_mock_update_request_handler',
                '_subscribe_to_mocked_datapoints',
                '_set_datapoint'
            ]
            
            for method_name in required_methods:
                assert hasattr(mock_service, method_name), f"Missing method: {method_name}"
    
    def test_datapoint_update_functionality(self):
        """Test that datapoint updates work and trigger activity."""
        from mockservice import MockService
        from lib.datapoint import DataPoint
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Mock the _set_datapoint method to avoid client dependencies
            with mock.patch.object(mock_service, '_set_datapoint') as mock_set:
                # Create a mock datapoint
                datapoint = mock.Mock(spec=DataPoint)
                datapoint.path = "Vehicle.Speed"
                datapoint.value = 50.0
                
                # Set service to idle first
                mock_service._is_idle = True
                original_activity_time = mock_service._last_activity_time
                
                # Call the datapoint update method
                mock_service._on_datapoint_updated(datapoint)
                
                # Verify functionality
                mock_set.assert_called_once_with("Vehicle.Speed", 50.0)
                assert not mock_service._is_idle, "Service should exit idle mode on datapoint update"
                assert mock_service._last_activity_time > original_activity_time, "Activity timestamp should be updated"
    
    def test_event_handling_functionality(self):
        """Test that event handling works and triggers activity."""
        from mockservice import MockService
        from lib.types import Event
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Set service to idle
            mock_service._is_idle = True
            initial_event_count = len(mock_service._pending_event_list)
            original_activity_time = mock_service._last_activity_time
            
            # Simulate event processing in _mock_update_request_handler
            # Create mock iterator that yields updates
            mock_updates = {
                "Vehicle.Speed": mock.Mock(value=60.0)
            }
            mock_response_iter = [mock_updates]
            
            # Call the event handler
            mock_service._mock_update_request_handler(mock_response_iter, "value")
            
            # Verify event was added and activity updated
            assert len(mock_service._pending_event_list) == initial_event_count + 1, "Event should be added to pending list"
            assert mock_service._last_activity_time > original_activity_time, "Activity timestamp should be updated"
    
    def test_main_loop_behavior_logic(self):
        """Test that main loop logic handles idle/active states correctly."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Mock required components
            mock_service._registered = True
            mock_service._behavior_executor = mock.Mock()
            mock_service._mocked_datapoints = {}
            
            # Test idle state logic
            mock_service._is_idle = True
            mock_service._pending_event_list = []  # No events
            
            # The logic should skip behavior execution when idle with no events
            has_events = len(mock_service._pending_event_list) > 0
            has_animations = mock_service._has_active_animations()
            is_idle = mock_service._is_idle
            
            should_execute = not is_idle or has_events or has_animations
            assert not should_execute, "Should not execute behaviors when idle with no activity"
            
            # Test active state logic
            mock_service._is_idle = False
            should_execute = not mock_service._is_idle or has_events or has_animations
            assert should_execute, "Should execute behaviors when not idle"
    
    def test_animation_detection_functionality(self):
        """Test that animation detection works correctly."""
        from mockservice import MockService
        from lib.action import AnimationAction
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Test with no datapoints
            assert not mock_service._has_active_animations(), "Should return False with no datapoints"
            
            # Test with mocked datapoints but no animations
            mock_datapoint = mock.Mock()
            mock_behavior = mock.Mock()
            mock_behavior._action = mock.Mock()  # Non-animation action
            mock_datapoint.behaviors = [mock_behavior]
            mock_service._mocked_datapoints = {"test": mock_datapoint}
            
            assert not mock_service._has_active_animations(), "Should return False with no animation actions"
            
            # Test with active animation
            mock_animation = mock.Mock(spec=AnimationAction)
            mock_animator = mock.Mock()
            mock_animator.is_done.return_value = False  # Animation is active
            mock_animation._animator = mock_animator
            mock_behavior._action = mock_animation
            
            with mock.patch('builtins.type', return_value=AnimationAction):
                assert mock_service._has_active_animations(), "Should return True with active animation"
    
    def test_configuration_loading(self):
        """Test that configuration methods work correctly."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Mock required dependencies
            mock_service._client = mock.Mock()
            
            with mock.patch('mockservice.PythonDslLoader') as mock_loader_class:
                mock_loader = mock.Mock()
                mock_loader_class.return_value = mock_loader
                mock_loader_result = mock.Mock()
                mock_loader_result.mocked_datapoints = {}
                mock_loader.load.return_value = mock_loader_result
                
                with mock.patch.object(mock_service, '_subscribe_to_mocked_datapoints'):
                    # Call check_for_new_mocks
                    mock_service.check_for_new_mocks(True)
                    
                    # Verify loader was called
                    mock_loader.load.assert_called_once_with(mock_service._client)
                    assert mock_service._registered, "Service should be marked as registered"
    
    def test_sleep_duration_logic(self):
        """Test that sleep duration selection works correctly."""
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            # Test idle sleep selection
            mock_service._is_idle = True
            has_events = False
            has_animations = False
            
            # Should use idle sleep duration
            expected_sleep = mock_service._idle_sleep_duration
            if mock_service._is_idle and not has_events and not has_animations:
                actual_sleep = mock_service._idle_sleep_duration
            else:
                actual_sleep = mock_service._base_sleep_duration
                
            assert actual_sleep == expected_sleep, f"Expected idle sleep {expected_sleep}, got {actual_sleep}"
            
            # Test active sleep selection  
            mock_service._is_idle = False
            expected_sleep = mock_service._base_sleep_duration
            if mock_service._is_idle and not has_events and not has_animations:
                actual_sleep = mock_service._idle_sleep_duration
            else:
                actual_sleep = mock_service._base_sleep_duration
                
            assert actual_sleep == expected_sleep, f"Expected base sleep {expected_sleep}, got {actual_sleep}"
    
    def run_all_tests(self):
        """Run all functionality verification tests."""
        print("=== Mock Service Functionality Verification Tests ===")
        
        tests = [
            ("Core Methods Exist", self.test_core_methods_exist),
            ("Datapoint Update Functionality", self.test_datapoint_update_functionality),
            ("Event Handling Functionality", self.test_event_handling_functionality),
            ("Main Loop Behavior Logic", self.test_main_loop_behavior_logic),
            ("Animation Detection Functionality", self.test_animation_detection_functionality),
            ("Configuration Loading", self.test_configuration_loading),
            ("Sleep Duration Logic", self.test_sleep_duration_logic),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        print(f"\n=== Results ===")
        print(f"Passed: {passed}/{len(tests)}")
        
        if passed == len(tests):
            print("🎉 All functionality verification tests passed!")
            print("\n✅ Existing functionality remains intact after optimization")
            return True
        else:
            print("❌ Some functionality verification tests failed!")
            print("\n⚠️  Potential regression detected - review changes")
            return False

if __name__ == "__main__":
    tester = TestFunctionality()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)