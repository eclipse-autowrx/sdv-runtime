#!/usr/bin/env python3
"""
Project utilities for kuksa-syncer
Provides functions to parse and save project data from payloads
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectUtils:
    """Utility class for handling project data and file operations"""
    
    def __init__(self, base_path: str = None):
        """
        Initialize ProjectUtils
        
        Args:
            base_path: Base path for saving projects (defaults to kuksa-syncer/app)
        """
        if base_path is None:
            # Get the directory where this script is located
            script_dir = Path(__file__).parent
            self.base_path = script_dir / "app"
        else:
            self.base_path = Path(base_path)
        
        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Project base path: {self.base_path}")
    
    def parse_project_data(self, code_data: str) -> List[Dict[str, Any]]:
        """
        Parse the code data from payload
        
        Args:
            code_data: JSON string containing project structure
            
        Returns:
            List of project items (folders/files)
            
        Raises:
            json.JSONDecodeError: If code_data is not valid JSON
        """
        try:
            # Parse the JSON string
            project_items = json.loads(code_data)
            logger.info(f"Successfully parsed project data with {len(project_items)} root items")
            return project_items
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data: {e}")
            raise
    
    def save_project(self, project_items: List[Dict[str, Any]], project_name: str = None) -> str:
        """
        Save project items to the file system
        
        Args:
            project_items: List of project items from parse_project_data
            project_name: Optional name for the project folder (ignored, kept for compatibility)
            
        Returns:
            Path to the created project
        """
        if not project_items:
            raise ValueError("No project items to save")
        
        # Skip the two-layer structure and put children directly under app directory
        # Find the first folder and extract its children
        children_items = []
        for item in project_items:
            if item.get("type") == "folder":
                children_items = item.get("items", [])
                logger.info(f"Found root folder '{item['name']}', extracting {len(children_items)} children")
                break
        
        if not children_items:
            logger.warning("No children found in root folder, using items as-is")
            children_items = project_items
        
        # Process and save all children directly under base_path (app directory)
        self._process_items(children_items, self.base_path)
        
        logger.info(f"Project children saved successfully to {self.base_path}")
        return str(self.base_path)
    
    def _process_items(self, items: List[Dict[str, Any]], current_path: Path) -> None:
        """
        Recursively process project items and create files/folders
        
        Args:
            items: List of items to process
            current_path: Current directory path
        """
        for item in items:
            item_type = item.get("type")
            item_name = item.get("name", "unnamed")
            
            if item_type == "folder":
                # Create folder
                folder_path = current_path / item_name
                folder_path.mkdir(exist_ok=True)
                logger.debug(f"Created folder: {folder_path}")
                
                # Process sub-items if they exist
                sub_items = item.get("items", [])
                if sub_items:
                    self._process_items(sub_items, folder_path)
                    
            elif item_type == "file":
                # Create file
                file_path = current_path / item_name
                content = item.get("content", "")
                
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.debug(f"Created file: {file_path} ({len(content)} characters)")
                
            else:
                logger.warning(f"Unknown item type '{item_type}' for item '{item_name}'")
    
    def save_from_payload(self, payload: Dict[str, Any]) -> str:
        """
        Convenience method to save project from a complete payload
        
        Args:
            payload: Complete payload dictionary containing 'data.code'
            
        Returns:
            Path to the app directory where files were saved
            
        Raises:
            KeyError: If payload doesn't contain required data
            ValueError: If code data is invalid
        """
        if 'data' not in payload:
            raise KeyError("Payload missing 'data' key")
        
        data = payload['data']
        if 'code' not in data:
            raise KeyError("Payload data missing 'code' key")
        
        code_data = data['code']
        
        # Parse the project data
        project_items = self.parse_project_data(code_data)
        
        # Save the project (project_name is ignored now)
        return self.save_project(project_items)
    
    def list_projects(self) -> List[str]:
        """
        List all items in the app directory
        
        Returns:
            List of item names (files and folders)
        """
        items = []
        if self.base_path.exists():
            for item in self.base_path.iterdir():
                items.append(item.name)
        return sorted(items)
    
    def get_project_path(self, project_name: str) -> Path:
        """
        Get the full path to a specific item in the app directory
        
        Args:
            project_name: Name of the item (kept for compatibility)
            
        Returns:
            Path to the app directory
        """
        return self.base_path
    
    def project_exists(self, project_name: str) -> bool:
        """
        Check if an item exists in the app directory
        
        Args:
            project_name: Name of the item (kept for compatibility)
            
        Returns:
            True if item exists, False otherwise
        """
        return (self.base_path / project_name).exists()
    
    def empty_app_directory(self) -> bool:
        """
        Empty the app directory by removing all files and subdirectories
        while keeping the app directory itself
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.base_path.exists():
                logger.warning("App directory does not exist, nothing to empty")
                return True
            
            # Get all items in the app directory
            items = list(self.base_path.iterdir())
            
            if not items:
                logger.info("App directory is already empty")
                return True
            
            logger.info(f"Emptying app directory: {self.base_path}")
            logger.info(f"Found {len(items)} items to remove")
            
            # Remove all files and subdirectories
            for item in items:
                if item.is_file():
                    item.unlink()
                    logger.debug(f"Removed file: {item}")
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
                    logger.debug(f"Removed directory: {item}")
            
            logger.info("App directory emptied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to empty app directory: {e}")
            return False


def main():
    """Example usage and testing"""
    # Example payload (you can replace this with actual payload)
    example_payload = {
        'request_from': '80SiX4I87RIUd4JZAaD3',
        'cmd': 'run_python_app',
        'to_kit_id': 'RunTime-CPP',
        'usedAPIs': [],
        'data': {
            'code': '[{"type":"folder","name":"test-project","items":[{"type":"file","name":"README.md","content":"# Test Project\\nThis is a test project."}]}]',
            'name': 'TestProject'
        }
    }
    
    # Initialize ProjectUtils
    utils = ProjectUtils()
    
    try:
        # Save project from payload
        app_path = utils.save_from_payload(example_payload)
        print(f"Files saved to app directory: {app_path}")
        
        # List all items in app directory
        items = utils.list_projects()
        print(f"Available items: {items}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
