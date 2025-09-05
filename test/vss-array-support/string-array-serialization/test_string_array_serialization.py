#!/usr/bin/env python3
"""
Automated tests for string array serialization fix (Issue #1).

This test suite verifies that string arrays are properly serialized 
without extra quotes during JSON encoding.
"""

import json
import os
import sys

# Add the mock and kuksa-syncer directories to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../mock/lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../kuksa-syncer'))


class MockProtobufStringArray:
    """Mock protobuf-style string array with values attribute."""
    
    def __init__(self, values):
        self.values = values


class MockStringArrayRepresentation:
    """Mock string array that simulates protobuf string representation parsing."""
    
    def __init__(self, values):
        self.values = values
    
    def __str__(self):
        # Simulate protobuf string representation that was causing the issue
        lines = []
        for value in self.values:
            lines.append(f'values: "{value}"')
        return '\n'.join(lines)


class TestStringArraySerialization:
    """Test class for string array serialization functionality."""
    
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
    
    def test_import_json_patch(self):
        """Test that json_array_patch module can be imported."""
        try:
            from json_array_patch import ArrayJSONEncoder, apply_global_patch
            assert callable(apply_global_patch), "apply_global_patch should be callable"
            assert ArrayJSONEncoder is not None, "ArrayJSONEncoder should be available"
        except ImportError as e:
            raise AssertionError(f"Failed to import json_array_patch: {e}")
    
    def test_frederiks_specific_issue(self):
        """Test Frederik's exact reported scenario."""
        from json_array_patch import apply_global_patch
        
        # Apply the global patch
        apply_global_patch()
        
        # Simulate the problematic input that Frederik reported
        input_array = ['test', 'test']
        mock_protobuf_array = MockStringArrayRepresentation(input_array)
        
        # Test JSON serialization
        result = json.dumps(mock_protobuf_array)
        
        # Expected correct output
        expected = '["test", "test"]'
        
        # What Frederik was getting before the fix
        broken_output = '["\\\"test\\\"", "\\\"test\\\""]'
        
        assert result == expected, f"Expected {expected}, got {result}. Should not be broken output: {broken_output}"
    
    def test_protobuf_style_array(self):
        """Test protobuf-style array with values attribute."""
        from json_array_patch import ArrayJSONEncoder
        
        encoder = ArrayJSONEncoder()
        mock_array = MockProtobufStringArray(['test', 'test'])
        result = encoder.default(mock_array)
        expected = ['test', 'test']
        
        assert result == expected, f"Expected {expected}, got {result}"
    
    def test_various_string_scenarios(self):
        """Test various string array scenarios."""
        from json_array_patch import apply_global_patch
        
        apply_global_patch()
        
        test_cases = [
            (['hello', 'world'], '["hello", "world"]'),
            (['', 'test', ''], '["", "test", ""]'),
            (['test@example.com', 'user-123'], '["test@example.com", "user-123"]'),
            (['single'], '["single"]'),
            (['test with spaces'], '["test with spaces"]'),
        ]
        
        for input_values, expected in test_cases:
            mock_array = MockStringArrayRepresentation(input_values)
            result = json.dumps(mock_array)
            assert result == expected, f"For input {input_values}: expected {expected}, got {result}"
    
    def test_backward_compatibility_numeric(self):
        """Test that numeric arrays still work correctly."""
        from json_array_patch import apply_global_patch
        
        apply_global_patch()
        
        class MockUint32Array:
            def __init__(self, values):
                self.values = values
        
        class MockIntArrayFromString:
            def __str__(self):
                return "values: 1\nvalues: 2\nvalues: 3"
        
        # Test numeric array with values attribute
        uint_array = MockUint32Array([1, 2, 3])
        result = json.dumps(uint_array)
        expected = '[1, 2, 3]'
        assert result == expected, f"Numeric array: expected {expected}, got {result}"
        
        # Test numeric array from string parsing
        int_array = MockIntArrayFromString()
        result = json.dumps(int_array)
        expected = '[1, 2, 3]'
        assert result == expected, f"Numeric string parsing: expected {expected}, got {result}"
    
    def test_mixed_content_arrays(self):
        """Test arrays with mixed content."""
        from json_array_patch import apply_global_patch
        
        apply_global_patch()
        
        mock_array = MockProtobufStringArray(['test', '123', 'hello'])
        result = json.dumps(mock_array)
        expected = '["test", "123", "hello"]'
        
        assert result == expected, f"Mixed content: expected {expected}, got {result}"
    
    def test_empty_array(self):
        """Test empty array handling."""
        from json_array_patch import apply_global_patch
        
        apply_global_patch()
        
        mock_array = MockProtobufStringArray([])
        result = json.dumps(mock_array)
        expected = '[]'
        
        assert result == expected, f"Empty array: expected {expected}, got {result}"
    
    def run_all_tests(self):
        """Run all tests and return summary."""
        print("String Array Serialization Test Suite")
        print("=" * 60)
        print("Testing Issue #1: String Array Quote Escaping Fix")
        print()
        
        tests = [
            ("Import JSON Patch Module", self.test_import_json_patch),
            ("Frederik's Specific Issue", self.test_frederiks_specific_issue),
            ("Protobuf Style Array", self.test_protobuf_style_array),
            ("Various String Scenarios", self.test_various_string_scenarios),
            ("Backward Compatibility - Numeric", self.test_backward_compatibility_numeric),
            ("Mixed Content Arrays", self.test_mixed_content_arrays),
            ("Empty Array", self.test_empty_array),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        print()
        print("=" * 60)
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! String array serialization fix is working correctly!")
            return True
        else:
            print(f"❌ {total - passed} tests failed. String array serialization needs attention.")
            print()
            print("Failed tests:")
            for test_name, success, error in self.test_results:
                if not success:
                    print(f"  - {test_name}: {error}")
            return False


if __name__ == "__main__":
    tester = TestStringArraySerialization()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)