# /********************************************************************************
# * Copyright (c) 2023 Contributors to the Eclipse Foundation
# *
# * See the NOTICE file(s) distributed with this work for additional
# * information regarding copyright ownership.
# *
# * This program and the accompanying materials are made available under the
# * terms of the Apache License 2.0 which is available at
# * http://www.apache.org/licenses/LICENSE-2.0
# *
# * SPDX-License-Identifier: Apache-2.0
# ********************************************************************************/

from typing import Any, Optional, Callable, List, Union
import logging
import json

from kuksa_client.grpc import DataType


log = logging.getLogger("datapoint")


def json_serialize_safe(obj):
    """JSON serialization with automatic array conversion support."""
    def convert_arrays(value):
        """Recursively convert array-like objects to JSON-serializable format."""
        # Handle protobuf array objects (like Uint32Array, Int32Array, etc.)
        if hasattr(value, 'values') and hasattr(value.values, '__iter__'):
            try:
                return list(value.values)
            except Exception:
                pass
        
        # Handle array-like objects (including typed arrays)
        if hasattr(value, 'tolist') and callable(value.tolist):
            try:
                return value.tolist()
            except Exception:
                pass
        
        # Handle Python array.array objects and similar
        if hasattr(value, '__iter__') and hasattr(value, '__len__') and not isinstance(value, (str, bytes, dict)):
            try:
                return list(value)
            except Exception:
                pass
        
        # Handle dictionaries recursively
        if isinstance(value, dict):
            return {k: convert_arrays(v) for k, v in value.items()}
        
        # Handle lists recursively
        if isinstance(value, list):
            return [convert_arrays(item) for item in value]
        
        # Return unchanged for other types
        return value
    
    try:
        converted_obj = convert_arrays(obj)
        return json.dumps(converted_obj)
    except Exception as e:
        log.error(f"Failed to JSON serialize object: {e}")
        # Fallback to string representation
        return json.dumps(str(obj))


def is_array_type(data_type: DataType) -> bool:
    """Check if the given DataType is an array type."""
    return data_type in {
        DataType.BOOLEAN_ARRAY,
        DataType.FLOAT_ARRAY,
        DataType.DOUBLE_ARRAY,
        DataType.INT8_ARRAY,
        DataType.UINT8_ARRAY,
        DataType.INT16_ARRAY,
        DataType.UINT16_ARRAY,
        DataType.INT32_ARRAY,
        DataType.UINT32_ARRAY,
        DataType.INT64_ARRAY,
        DataType.UINT64_ARRAY,
        DataType.STRING_ARRAY,
        DataType.TIMESTAMP_ARRAY,
    }


def convert_array_value(value: Any, data_type: DataType) -> Any:
    """Convert array values to JSON-serializable format."""
    if not is_array_type(data_type):
        return value
    
    if value is None:
        return None
    
    # Handle protobuf array objects (e.g., kuksa.val.v1.types_pb2.Uint32Array)
    if hasattr(value, 'values') and hasattr(value.values, '__iter__'):
        try:
            return list(value.values)
        except Exception as e:
            log.warning(f"Failed to convert protobuf array value to list: {e}")
    
    # Handle numpy arrays or other array-like objects that aren't JSON serializable
    if hasattr(value, 'tolist'):
        try:
            return value.tolist()
        except Exception as e:
            log.warning(f"Failed to convert array value to list: {e}")
    
    # Handle typed arrays (like Uint32Array) that may not be directly iterable
    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        try:
            # Try to convert to list by iterating
            return list(value)
        except (TypeError, ValueError) as e:
            log.warning(f"Failed to convert iterable array value to list: {e}")
            # If direct iteration fails, try accessing individual elements
            try:
                if hasattr(value, '__len__') and hasattr(value, '__getitem__'):
                    result = [value[i] for i in range(len(value))]
                    log.debug(f"Successfully converted typed array to list: {result}")
                    return result
            except Exception as e2:
                log.warning(f"Failed to convert array by indexing: {e2}")
    
    # Handle protobuf-style array representations
    if hasattr(value, '__str__') and 'values:' in str(value):
        try:
            str_value = str(value)
            lines = str_value.strip().split('\n')
            result = []
            for line in lines:
                if line.strip().startswith('values:'):
                    val_str = line.split(':', 1)[1].strip()
                    try:
                        # Try to parse as integer first
                        result.append(int(val_str))
                    except ValueError:
                        try:
                            # Try to parse as float
                            result.append(float(val_str))
                        except ValueError:
                            # Keep as string
                            result.append(val_str)
            if result:
                log.debug(f"Converted protobuf-style array: {value} -> {result}")
                return result
        except Exception as e:
            log.warning(f"Failed to parse protobuf-style array: {e}")
    
    # If it's already a list, return as-is
    if isinstance(value, list):
        return value
    
    # Handle string representations of arrays (fallback)
    if isinstance(value, str):
        try:
            # Try to parse as JSON array
            import json
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Try to convert other types to list as last resort
    try:
        if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
            return list(value)
        else:
            return [value]
    except (TypeError, ValueError) as e:
        log.warning(f"Failed to convert array value to list: {e}")
        return value


class DataPoint:
    def __init__(
        self,
        path: str,
        data_type: DataType,
        value: Any,
        value_listener: Optional[Callable[[Any], None]] = None,
    ):
        self.path = path
        self.data_type = data_type
        self.value = convert_array_value(value, data_type)
        self.value_listener = value_listener

    def has_discrete_value_type(self):
        """Return if the datapoint has a discrete value type."""
        return (self.data_type == DataType.BOOLEAN 
                or self.data_type == DataType.STRING
                or self.data_type == DataType.BOOLEAN_ARRAY
                or self.data_type == DataType.STRING_ARRAY)

    def set_value(self, new_value):
        """Set the value of the datapoint."""
        converted_value = convert_array_value(new_value, self.data_type)
        if self.value != converted_value:
            self.value = converted_value
            if self.value_listener is not None:
                self.value_listener(self)
    
    def get_json_serializable_value(self):
        """Get the value in a JSON-serializable format."""
        return convert_array_value(self.value, self.data_type)

    def __eq__(self, other):
        return (
            isinstance(other, DataPoint)
            and self.path == other.path
            and self.data_type == other.data_type
            and self.value == other.value
        )

    def __ne__(self, other):
        return not self.__eq__(other)
