# Copyright (c) 2025 Eclipse Foundation.
# 
# This program and the accompanying materials are made available under the
# terms of the MIT License which is available at
# https://opensource.org/licenses/MIT.
#
# SPDX-License-Identifier: MIT

"""
Global JSON serialization patch for VSS array types.

This module patches the default JSON encoder to handle protobuf array objects
like Uint32Array, Int32Array, etc. that are not natively JSON serializable.
"""

import json
import logging
from typing import Any

log = logging.getLogger("json_array_patch")


class ArrayJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles protobuf array objects."""
    
    def default(self, obj):
        # Handle protobuf array objects
        if hasattr(obj, 'values') and hasattr(obj.values, '__iter__'):
            try:
                values = list(obj.values)
                # For string arrays, ensure strings are not double-encoded
                # The values might already be properly formatted strings
                return values
            except Exception as e:
                log.debug(f"Failed to convert protobuf array to list: {e}")
        
        # Handle typed arrays with tolist method (numpy-like)
        if hasattr(obj, 'tolist'):
            try:
                return obj.tolist()
            except Exception as e:
                log.debug(f"Failed to convert array with tolist: {e}")
        
        # Handle other iterable array-like objects
        if hasattr(obj, '__iter__') and hasattr(obj, '__len__') and not isinstance(obj, (str, bytes, dict)):
            try:
                return list(obj)
            except Exception as e:
                log.debug(f"Failed to convert iterable to list: {e}")
        
        # Handle protobuf-style objects by examining their string representation
        if hasattr(obj, '__str__'):
            str_repr = str(obj)
            if 'values:' in str_repr and any(array_type in str(type(obj)).lower() for array_type in ['array', 'uint', 'int', 'string']):
                try:
                    # Parse protobuf-style string representation
                    lines = str_repr.strip().split('\n')
                    result = []
                    for line in lines:
                        if line.strip().startswith('values:'):
                            val_str = line.split(':', 1)[1].strip()
                            # Remove surrounding quotes for strings if present
                            if val_str.startswith('"') and val_str.endswith('"'):
                                result.append(val_str[1:-1])
                            else:
                                try:
                                    result.append(int(val_str))
                                except ValueError:
                                    try:
                                        result.append(float(val_str))
                                    except ValueError:
                                        result.append(val_str)
                    if result:
                        return result
                except Exception as e:
                    log.debug(f"Failed to parse protobuf-style array: {e}")
        
        # Fallback: try to convert to string instead of failing
        try:
            return str(obj)
        except Exception:
            return f"<non-serializable: {type(obj).__name__}>"


def patch_json_module():
    """Patch the global json module to use our custom encoder by default."""
    
    # Store original functions
    original_dumps = json.dumps
    original_dump = json.dump
    
    def patched_dumps(obj, **kwargs):
        """Patched json.dumps with array support."""
        # Use our custom encoder if no encoder is specified
        if 'cls' not in kwargs:
            kwargs['cls'] = ArrayJSONEncoder
        return original_dumps(obj, **kwargs)
    
    def patched_dump(obj, fp, **kwargs):
        """Patched json.dump with array support."""
        # Use our custom encoder if no encoder is specified
        if 'cls' not in kwargs:
            kwargs['cls'] = ArrayJSONEncoder
        return original_dump(obj, fp, **kwargs)
    
    # Apply patches
    json.dumps = patched_dumps
    json.dump = patched_dump
    
    log.debug("Global JSON module patched with array support")


def apply_global_patch():
    """Apply the global JSON patch. Call this at startup."""
    try:
        patch_json_module()
        
        # Also patch engineio.json which is used by socketio
        try:
            import engineio.json
            engineio.json.dumps = json.dumps
            engineio.json.dump = json.dump  
            log.debug("Patched engineio.json module")
        except ImportError:
            pass
            
        log.info("Successfully applied global JSON array serialization patch")
    except Exception as e:
        log.error(f"Failed to apply global JSON patch: {e}")