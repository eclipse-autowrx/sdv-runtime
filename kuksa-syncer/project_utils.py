#!/usr/bin/env python3
"""
Project utilities for kuksa-syncer.
Provides functions to parse and save project data from payloads,
and inject shared memory support into C++ code.
"""

import json
import os
import logging
import shutil
import re
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


class ProjectUtils:
    """Utility class for handling project data and file operations."""

    def __init__(self, base_path: str = None):
        """
        Initialize ProjectUtils.

        Args:
            base_path: Base path for saving projects (defaults to 'kuksa-syncer/app').
        """
        if base_path is None:
            script_dir = Path(__file__).parent
            self.base_path = script_dir / "app"
        else:
            self.base_path = Path(base_path)

        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Project base path set to: {self.base_path}")

    def _process_items(self, items: List[Dict[str, Any]], current_path: Path, watch_vars_str: str):
        """
        Recursively process project items and create files/folders.

        Args:
            items: List of items to process (files or folders).
            current_path: The directory path to create items in.
            watch_vars_str: A comma-separated string of variables to watch for injection.
        """
        for item in items:
            item_type = item.get("type")
            item_name = item.get("name", "unnamed")
            item_path = current_path / item_name

            if item_type == "folder":
                item_path.mkdir(exist_ok=True)
                logger.debug(f"Ensured folder exists: {item_path}")
                sub_items = item.get("items", [])
                if sub_items:
                    self._process_items(sub_items, item_path, watch_vars_str)
            elif item_type == "file":
                content = item.get("content", "")
                item_path.parent.mkdir(parents=True, exist_ok=True)

                # For C++ files, back up and consider for code injection.
                if item_name.endswith(('.cpp', '.h')):
                    backup_file_path = item_path.with_suffix(item_path.suffix + '.origin')
                    with open(backup_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Created backup: {backup_file_path}")
                    
                    # Inject code only if 'main' is in the filename, suggesting it's an entry point.
                    if "main" in item_name.lower() and item_name.endswith('.cpp'):
                        logger.info(f"Injecting SHM code into {item_name}")
                        content = self.inject_shm_code(content, watch_vars_str)

                with open(item_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.debug(f"Wrote file: {item_path} ({len(content)} bytes)")
            else:
                logger.warning(f"Skipping unknown item type '{item_type}' for item '{item_name}'")

    def save_from_payload(self, payload: Dict[str, Any]) -> str:
        """
        Save a project from a complete payload.

        Args:
            payload: The complete payload dictionary containing 'data.code'.

        Returns:
            The path to the app directory where files were saved.
        """
        if 'data' not in payload or 'code' not in payload['data']:
            raise KeyError("Payload must include 'data' with a 'code' key.")

        code_data_str = payload['data']['code']
        watch_vars = payload['data'].get("watch_vars", "")

        # Ensure the wrapper header is available in the app directory.
        wrapper_src = self.base_path.parent / 'shm_wrapper.h'
        wrapper_dest = self.base_path / 'shm_wrapper.h'
        if wrapper_src.exists():
            shutil.copy(wrapper_src, wrapper_dest)
            logger.info(f"Copied shm_wrapper.h to {self.base_path}")
        else:
            logger.warning(f"shm_wrapper.h not found at {wrapper_src}")

        try:
            project_items = json.loads(code_data_str)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON format in 'data.code'") from e

        # Skip the root project folder and process its contents directly in the app directory
        items_to_process = []
        for item in project_items:
            if item.get("type") == "folder" and "items" in item:
                # Extract the contents of the root folder and process them directly
                items_to_process.extend(item["items"])
                logger.info(f"Skipping root folder '{item.get('name')}' and processing its contents directly")
            else:
                # If it's not a folder or doesn't have items, process it as-is
                items_to_process.append(item)

        self._process_items(items_to_process, self.base_path, watch_vars)

        logger.info(f"Project structure successfully created in {self.base_path}")
        return str(self.base_path)

    def empty_app_directory(self) -> bool:
        """
        Remove all contents of the app directory.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if not self.base_path.exists():
                logger.info("App directory does not exist; nothing to empty.")
                return True

            logger.info(f"Emptying app directory: {self.base_path}")
            for item in self.base_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            logger.info("App directory emptied successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to empty app directory: {e}")
            return False

    def inject_shm_code(self, cpp_code: str, watch_vars_str: str) -> str:
        """
        Inject shared memory code into a C++ source string.

        Args:
            cpp_code: The original C++ code.
            watch_vars_str: A comma-separated string of variable names to watch.

        Returns:
            The modified C++ code with shared memory support.
        """
        if not watch_vars_str or not watch_vars_str.strip():
            return cpp_code

        watch_vars = [v.strip() for v in watch_vars_str.split(',') if v.strip()]

        if '#include "shm_wrapper.h"' not in cpp_code:
            cpp_code = '#include "shm_wrapper.h"\n' + cpp_code

        # First, replace existing variable declarations with atomic versions
        for var in watch_vars:
            # Look for existing variable declarations and replace them with atomic versions
            # Pattern: int varname = value; or int varname;
            pattern = rf'\b(?:int|float|double)\s+{re.escape(var)}\s*(?:=\s*[^;]+)?\s*;'
            match = re.search(pattern, cpp_code)
            if match:
                # Determine type based on the original declaration or default to int
                original_decl = match.group(0)
                if 'float' in original_decl or 'double' in original_decl:
                    var_type = "double"
                    initial_value = "0.0"
                else:
                    var_type = "int" 
                    initial_value = "0"
                
                # Replace the original declaration with atomic version
                atomic_decl = f"std::atomic<{var_type}> {var}({initial_value});"
                cpp_code = re.sub(pattern, atomic_decl, cpp_code)
                logger.info(f"Replaced variable declaration: {var} -> atomic version")

        # Regex to find main function, accommodating void or argc/argv parameters.
        main_func_match = re.search(r'int\s+main\s*\((?:void|int\s+argc,\s*char\s*\*\s*argv\[\])?\s*\)\s*{', cpp_code)
        if not main_func_match:
            logger.warning("main() function not found. Cannot inject SHM code.")
            return cpp_code

        # Find the opening brace of main function and inject initialization code
        main_body_start = main_func_match.end()

        # Inject initialization and cleanup calls inside main.
        watch_macros = []
        for var in watch_vars:
            # Simple type inference for demonstration purposes.
            var_type = "double" if any(t in var.lower() for t in ["temp", "value"]) else "int"
            watch_macros.append(f'    WATCH_VAR({var}, "{var_type}");')

        init_code = f"\n    INIT_SHM();\n" + "\n".join(watch_macros) + "\n"
        cpp_code = cpp_code[:main_body_start] + init_code + cpp_code[main_body_start:]
        cpp_code = re.sub(r'(return\s+\d+;)', r'    CLEANUP_SHM();\n    \1', cpp_code)

        return cpp_code


def main():
    """Provides an example of using ProjectUtils for testing."""
    logger.info("--- Running ProjectUtils Standalone Test ---")

    # Define the project structure as a Python object
    project_structure = [
        {
            "type": "folder", "name": "my-cpp-app", "items": [
                {"type": "file", "name": "main.cpp", "content": '#include <iostream>\n#include "math/calculator.h"\n\nint main() {\n    Calculator calc;\n    std::cout << "2+3=" << calc.add(2, 3) << std::endl;\n    return 0;\n}'},
                {"type": "file", "name": "README.md", "content": "Test App"},
                {
                    "type": "folder", "name": "math", "items": [
                        {"type": "file", "name": "calculator.h", "content": "class Calculator { public: int add(int a, int b); };"},
                        {"type": "file", "name": "calculator.cpp", "content": '#include "calculator.h"\nint Calculator::add(int a, int b) { return a + b; }'}
                    ]
                }
            ]
        }
    ]

    # Example payload for a multi-file project.
    example_payload = {
        'data': {
            'code': json.dumps(project_structure),
            'watch_vars': 'counter,temperature'
        }
    }
    
    utils = ProjectUtils()
    
    logger.info("Step 1: Cleaning the app directory.")
    utils.empty_app_directory()
    
    try:
        logger.info("Step 2: Saving project from payload.")
        app_path = utils.save_from_payload(example_payload)
        logger.info(f"Project files saved to: {app_path}")
        
        # Verify file creation - files should now be directly in app directory
        main_cpp_path = Path(app_path) / "main.cpp"
        if main_cpp_path.exists():
            logger.info(f"✓ {main_cpp_path} created successfully.")
            injected_content = main_cpp_path.read_text()
            if 'std::atomic<int> counter(0);' in injected_content and 'INIT_SHM();' in injected_content:
                logger.info("✓ SHM code injected successfully into main.cpp.")
            else:
                logger.error("✗ SHM code injection failed.")
        else:
            logger.error(f"✗ {main_cpp_path} was not created.")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

    logger.info("--- Test Complete ---")


if __name__ == "__main__":
    main()
