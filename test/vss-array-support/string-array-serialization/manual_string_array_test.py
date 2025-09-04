#!/usr/bin/env python3
"""
Manual interactive test for string array serialization fix.

This script allows manual testing and demonstration of the string array
serialization behavior before and after the fix.
"""

import json
import os
import sys
import time

# Add the mock and kuksa-syncer directories to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../mock/lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../kuksa-syncer'))


class MockStringArray:
    """Mock string array for demonstration purposes."""
    
    def __init__(self, values):
        self.values = values
    
    def __str__(self):
        lines = []
        for value in self.values:
            lines.append(f'values: "{value}"')
        return '\n'.join(lines)


def demonstrate_issue():
    """Demonstrate the string array serialization issue and fix."""
    print("🔧 String Array Serialization Fix Demonstration")
    print("=" * 60)
    print()
    
    print("📋 Background - Issue #1:")
    print("  Reporter: Stoehr Frederik (BEG/EVC3-Wi)")
    print("  Problem: String arrays getting extra quotes during JSON serialization")
    print()
    
    # Create test data
    test_input = ['test', 'test']
    print(f"📝 Test Input: {test_input}")
    print()
    
    # Show what the broken output looked like
    broken_output = '["\\\"test\\\"", "\\\"test\\\""]'
    print(f"❌ Before Fix (broken): {broken_output}")
    print("   ^ Extra escape quotes making strings unusable")
    print()
    
    # Apply the fix and show correct output
    try:
        from json_array_patch import apply_global_patch
        apply_global_patch()
        print("✅ Applied JSON array serialization patch")
        
        mock_array = MockStringArray(test_input)
        print(f"🔄 Protobuf String Representation:")
        print(f"   {str(mock_array).replace(chr(10), chr(10) + '   ')}")
        print()
        
        result = json.dumps(mock_array)
        expected = '["test", "test"]'
        
        print(f"✅ After Fix (correct): {result}")
        print("   ^ Clean strings without extra quotes")
        print()
        
        if result == expected:
            print("🎉 SUCCESS: Fix is working correctly!")
        else:
            print(f"❌ FAIL: Expected {expected}, got {result}")
            
    except ImportError as e:
        print(f"❌ Error importing json_array_patch: {e}")
        return False
    
    return True


def interactive_test():
    """Interactive test allowing user to input custom string arrays."""
    print("\n" + "=" * 60)
    print("🔍 Interactive String Array Test")
    print("=" * 60)
    print()
    
    try:
        from json_array_patch import apply_global_patch
        apply_global_patch()
        
        while True:
            print("Enter string values separated by commas (or 'quit' to exit):")
            user_input = input("> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
                
            try:
                # Parse user input
                values = [s.strip().strip('"\'') for s in user_input.split(',')]
                print(f"📝 Input values: {values}")
                
                # Test serialization
                mock_array = MockStringArray(values)
                result = json.dumps(mock_array)
                
                print(f"📤 JSON Output: {result}")
                print(f"✅ Successfully serialized {len(values)} string(s)")
                print()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                print()
                
    except ImportError as e:
        print(f"❌ Error importing json_array_patch: {e}")


def performance_test():
    """Simple performance test for the serialization."""
    print("\n" + "=" * 60)
    print("⚡ Performance Test")
    print("=" * 60)
    print()
    
    try:
        from json_array_patch import apply_global_patch
        apply_global_patch()
        
        # Test with various array sizes
        test_sizes = [10, 100, 1000]
        
        for size in test_sizes:
            test_array = [f"test_value_{i}" for i in range(size)]
            mock_array = MockStringArray(test_array)
            
            start_time = time.time()
            result = json.dumps(mock_array)
            end_time = time.time()
            
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            print(f"📊 Array size {size:4d}: {duration:6.2f}ms")
        
        print("✅ Performance test completed")
        
    except ImportError as e:
        print(f"❌ Error importing json_array_patch: {e}")


def main():
    """Main function for manual testing."""
    print("String Array Serialization - Manual Test")
    print("Testing Issue #1 Fix")
    print()
    
    # Demonstrate the fix
    if not demonstrate_issue():
        sys.exit(1)
    
    # Interactive testing
    interactive_test()
    
    # Performance testing
    performance_test()
    
    print("\n" + "=" * 60)
    print("✅ Manual testing completed!")
    print("👉 For automated tests, run: python3 test_string_array_serialization.py")


if __name__ == "__main__":
    main()