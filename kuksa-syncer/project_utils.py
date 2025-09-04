import os
import json
import shutil
import base64

def _create_items(items, current_dir):
    for item in items:
        item_name = item["name"]
        item_type = item["type"]
        item_path = os.path.join(current_dir, item_name)

        if item_type == "folder":
            os.makedirs(item_path, exist_ok=True)
            if "items" in item:
                _create_items(item["items"], item_path)
        elif item_type == "file":
            content = item.get("content", "")
            is_base64 = item.get("isBase64", False)

            if is_base64:
                # Decode base64 content and write as binary
                with open(item_path, 'wb') as f:
                    f.write(base64.b64decode(content))
            else:
                # Write content as text
                with open(item_path, 'w') as f:
                    f.write(content)

def _filter_macosx(items):
    """Recursively filter out '__MACOSX' directories."""
    if not isinstance(items, list):
        return items
    
    # Use a list comprehension to build the new list, excluding '__MACOSX'
    filtered_items = [item for item in items if item.get("name") != "__MACOSX"]
    
    # Recurse into sub-folders
    for item in filtered_items:
        if item.get("type") == "folder" and "items" in item:
            item["items"] = _filter_macosx(item["items"])
            
    return filtered_items

def create_project_from_json(json_string, base_dir="app"):
    """
    Creates a project structure from a JSON string.
    The JSON should be a list of dictionaries, where each dictionary
    represents a file or a folder.
    """
    # print("create_project_from_json: json_string", json_string)
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    
    data = json.loads(json_string)
    
    # Filter out __MACOSX directories first
    data = _filter_macosx(data)

    # If the root consists of a single folder, treat its contents as the project root.
    if len(data) == 1 and data[0].get("type") == "folder" and "items" in data[0]:
        data = data[0]["items"]

    os.makedirs(base_dir, exist_ok=True)
    _create_items(data, base_dir)
