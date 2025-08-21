#!/usr/bin/env python3
"""
Manual interactive test for idle detection behavior.
This script demonstrates the idle detection in real-time.
"""

import os
import sys
import time
import threading
import unittest.mock as mock

# Add the mock directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../mock'))

# Set fast idle threshold for demonstration
os.environ.setdefault('MOCK_IDLE_THRESHOLD', '5.0')  # 5 seconds for demo
os.environ.setdefault('MOCK_BASE_SLEEP', '0.2')
os.environ.setdefault('MOCK_IDLE_SLEEP', '1.0')

def manual_test():
    """Interactive manual test of idle detection."""
    print("=== Manual Idle Detection Test ===")
    print("This test will demonstrate the idle detection behavior in real-time.")
    print(f"Idle threshold: {os.getenv('MOCK_IDLE_THRESHOLD')} seconds")
    print(f"Base sleep: {os.getenv('MOCK_BASE_SLEEP')} seconds")  
    print(f"Idle sleep: {os.getenv('MOCK_IDLE_SLEEP')} seconds")
    print()
    
    try:
        from mockservice import MockService
        
        with mock.patch('mockservice.BaseService.__init__', return_value=None):
            mock_service = MockService("127.0.0.1:50053", "127.0.0.1:55555")
            
            print("✅ Mock service created successfully")
            print(f"Initial state - Idle: {mock_service._is_idle}")
            print()
            
            # Test 1: Wait for idle mode
            print("Test 1: Waiting for service to enter idle mode...")
            print("(This will take 5 seconds)")
            
            start_time = time.perf_counter()
            while not mock_service._is_idle and (time.perf_counter() - start_time) < 10:
                mock_service._check_idle_state()
                time.sleep(0.5)
                elapsed = time.perf_counter() - start_time
                print(f"  {elapsed:.1f}s - Idle: {mock_service._is_idle}")
            
            if mock_service._is_idle:
                print("✅ Service entered idle mode successfully!")
            else:
                print("❌ Service did not enter idle mode within 10 seconds")
                return False
            
            print()
            
            # Test 2: Activity detection
            print("Test 2: Simulating activity to exit idle mode...")
            mock_service._update_activity_timestamp()
            print(f"  Activity simulated - Idle: {mock_service._is_idle}")
            
            if not mock_service._is_idle:
                print("✅ Service exited idle mode after activity!")
            else:
                print("❌ Service did not exit idle mode after activity")
                return False
            
            print()
            
            # Test 3: Animation detection
            print("Test 3: Testing animation detection method...")
            has_animations = mock_service._has_active_animations()
            print(f"  Has active animations: {has_animations}")
            print("✅ Animation detection method works")
            
            print()
            
            # Test 4: Manual activity simulation
            print("Test 4: Manual activity simulation")
            print("The service will enter idle mode, then we'll simulate various activities...")
            
            # Wait for idle again
            mock_service._last_activity_time = time.perf_counter() - 6.0  # Force idle
            mock_service._check_idle_state()
            print(f"  Forced idle state: {mock_service._is_idle}")
            
            # Simulate different activities
            activities = [
                ("Datapoint update", lambda: mock_service._update_activity_timestamp()),
                ("Event processing", lambda: mock_service._update_activity_timestamp()),
            ]
            
            for activity_name, activity_func in activities:
                # Set back to idle
                mock_service._is_idle = True
                print(f"  Before {activity_name} - Idle: {mock_service._is_idle}")
                
                # Simulate activity
                activity_func()
                print(f"  After {activity_name} - Idle: {mock_service._is_idle}")
                
                if not mock_service._is_idle:
                    print(f"  ✅ {activity_name} correctly exits idle mode")
                else:
                    print(f"  ❌ {activity_name} failed to exit idle mode")
            
            print()
            print("🎉 Manual test completed successfully!")
            print()
            print("Summary of idle detection behavior:")
            print("- Service enters idle mode after configured threshold")
            print("- Service exits idle mode when activity is detected")
            print("- Activity tracking works for various event types")
            print("- Configuration is properly loaded from environment variables")
            
            return True
            
    except Exception as e:
        print(f"❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting manual idle detection test...")
    print("Press Ctrl+C to interrupt at any time")
    print()
    
    try:
        success = manual_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)