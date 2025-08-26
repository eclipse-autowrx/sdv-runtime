# Project Utils for kuksa-syncer

This module provides utilities to parse and save project data from payloads into the file system.

## Overview

The `ProjectUtils` class can parse JSON payloads containing project structure information and automatically create the corresponding folder and file structure directly in the `/kuksa-syncer/app` directory, skipping the two-layer structure (data.name + first folder name).

## Features

- Parse JSON payloads with nested folder/file structures
- Automatically create directories and files
- Handle complex project hierarchies
- Provide utility methods for project management
- Comprehensive logging and error handling
- Empty app directory while preserving the directory structure

## Usage

### Basic Usage

```python
from project_utils import ProjectUtils

# Initialize the utility
utils = ProjectUtils()

# Save a project from a payload
payload = {
    'data': {
        'code': '[{"type":"folder","name":"my-project","items":[...]}',
        'name': 'ProjectName'
    }
}

app_path = utils.save_from_payload(payload)
print(f"Files saved to app directory: {app_path}")
```

### Advanced Usage

```python
# Parse project data manually
code_data = '[{"type":"folder","name":"cpp-project","items":[...]}]'
project_items = utils.parse_project_data(code_data)

# Save project (project name is ignored, kept for compatibility)
app_path = utils.save_project(project_items)

# List all items in app directory
items = utils.list_projects()
print(f"Available items: {items}")

# Check if item exists
if utils.project_exists("CMakeLists.txt"):
    app_path = utils.get_project_path("CMakeLists.txt")
    print(f"App directory: {app_path}")

# Empty the app directory
success = utils.empty_app_directory()
if success:
    print("App directory emptied successfully")
```

## Payload Structure

The expected payload structure is:

```json
{
    "data": {
        "code": "[{\"type\":\"folder\",\"name\":\"project-name\",\"items\":[...]}]",
        "name": "ProjectDisplayName"
    }
}
```

Where `code` is a JSON string containing an array of project items:

- **Folders**: `{"type": "folder", "name": "folder-name", "items": [...]}`
- **Files**: `{"type": "file", "name": "filename.ext", "content": "file content"}`

## Example Project Structure

The utility successfully handles complex project structures and places them directly under the app directory:

```
app/
├── CMakeLists.txt
├── README.md
├── include/
│   ├── utils.h
│   └── calculator.h
└── src/
    ├── main.cpp
    ├── utils.cpp
    └── calculator.cpp
```

**Note**: The root folder name (`cpp-project`) from the payload is ignored, and all children are placed directly under `/kuksa-syncer/app/`.

## File Locations

- **Base directory**: `/kuksa-syncer/app/`
- **Files and folders**: Placed directly under `/kuksa-syncer/app/`
- **Generated structure**: Follows the exact structure defined in the payload, but skips the root folder wrapper

## Error Handling

The utility provides comprehensive error handling:

- JSON parsing errors
- File system permission issues
- Invalid payload structures
- Missing required fields

All errors are logged and appropriate exceptions are raised.

## Testing

Run the utility directly to test functionality:

```bash
cd kuksa-syncer
python3 project_utils.py
```

This will test the utility with example data and show the created structure directly under the app directory.
