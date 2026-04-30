"""
Agent Skill: File Manager
This skill allows Claude Code to manage files in the AI Employee system
"""
import json
from pathlib import Path
from datetime import datetime
import shutil


def move_file(source_path: str, destination_folder: str) -> dict:
    """
    Move a file from source to destination folder

    Args:
        source_path (str): Path to the source file
        destination_folder (str): Name of the destination folder

    Returns:
        dict: Result of the move operation
    """
    source = Path(source_path)
    project_root = Path(__file__).parent.parent  # Go up to project root

    # Validate source file exists
    if not source.exists():
        return {
            "status": "error",
            "message": f"Source file does not exist: {source_path}",
            "timestamp": datetime.now().isoformat()
        }

    # Map destination folder name to actual path
    folder_map = {
        "inbox": project_root / "inbox",
        "needs_action": project_root / "needs_action",
        "done": project_root / "done",
        "pending_approval": project_root / "pending_approval",
        "plans": project_root / "plans"
    }

    if destination_folder.lower() not in folder_map:
        return {
            "status": "error",
            "message": f"Invalid destination folder: {destination_folder}. Valid options: {list(folder_map.keys())}",
            "timestamp": datetime.now().isoformat()
        }

    dest_folder = folder_map[destination_folder.lower()]
    dest_folder.mkdir(exist_ok=True)

    # Create destination file path
    dest_path = dest_folder / source.name

    try:
        # Handle if destination file already exists
        if dest_path.exists():
            # Add timestamp to avoid overwriting
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_path = dest_folder / f"{source.stem}_{timestamp}{source.suffix}"

        # Perform the move
        shutil.move(str(source), str(dest_path))

        return {
            "status": "success",
            "message": f"File moved from {source_path} to {dest_path}",
            "original_path": source_path,
            "new_path": str(dest_path),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error moving file: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def create_file(folder_name: str, filename: str, content: str, file_type: str = "md") -> dict:
    """
    Create a new file in the specified folder

    Args:
        folder_name (str): Name of the folder to create file in
        filename (str): Name of the file (without extension)
        content (str): Content to write to the file
        file_type (str): Type of file to create (default: md)

    Returns:
        dict: Result of the file creation
    """
    project_root = Path(__file__).parent.parent

    # Map folder name to actual path
    folder_map = {
        "inbox": project_root / "inbox",
        "needs_action": project_root / "needs_action",
        "done": project_root / "done",
        "pending_approval": project_root / "pending_approval",
        "plans": project_root / "plans",
        "logs": project_root / "logs"
    }

    if folder_name.lower() not in folder_map:
        return {
            "status": "error",
            "message": f"Invalid folder name: {folder_name}. Valid options: {list(folder_map.keys())}",
            "timestamp": datetime.now().isoformat()
        }

    folder_path = folder_map[folder_name.lower()]
    folder_path.mkdir(exist_ok=True)

    # Create the file path
    if file_type.startswith('.'):
        file_type = file_type[1:]  # Remove leading dot if present

    file_path = folder_path / f"{filename}.{file_type}"

    try:
        # If file exists, add timestamp to avoid overwriting
        if file_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = folder_path / f"{filename}_{timestamp}.{file_type}"

        # Write content to file
        file_path.write_text(content, encoding='utf-8')

        return {
            "status": "success",
            "message": f"File created: {file_path}",
            "file_path": str(file_path),
            "content_length": len(content),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating file: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def read_file(file_path: str) -> dict:
    """
    Read the content of a file

    Args:
        file_path (str): Path to the file to read

    Returns:
        dict: Content of the file
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "status": "error",
            "message": f"File does not exist: {file_path}",
            "timestamp": datetime.now().isoformat()
        }

    try:
        content = path.read_text(encoding='utf-8')

        return {
            "status": "success",
            "file_path": str(path),
            "content": content,
            "size": len(content),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading file: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def list_files(folder_name: str) -> dict:
    """
    List all files in the specified folder

    Args:
        folder_name (str): Name of the folder to list files from

    Returns:
        dict: List of files in the folder
    """
    project_root = Path(__file__).parent.parent

    # Map folder name to actual path
    folder_map = {
        "inbox": project_root / "inbox",
        "needs_action": project_root / "needs_action",
        "done": project_root / "done",
        "pending_approval": project_root / "pending_approval",
        "plans": project_root / "plans",
        "logs": project_root / "logs"
    }

    if folder_name.lower() not in folder_map:
        return {
            "status": "error",
            "message": f"Invalid folder name: {folder_name}. Valid options: {list(folder_map.keys())}",
            "timestamp": datetime.now().isoformat()
        }

    folder_path = folder_map[folder_name.lower()]

    if not folder_path.exists():
        return {
            "status": "error",
            "message": f"Folder does not exist: {folder_path}",
            "timestamp": datetime.now().isoformat()
        }

    try:
        files = []
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": file_path.suffix
                })

        return {
            "status": "success",
            "folder_path": str(folder_path),
            "file_count": len(files),
            "files": files,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing files: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


# Example usage function
def run_example():
    """Example of how to use the file_manager skills"""
    # Example: Create a test file in the plans folder
    result = create_file("plans", "test_plan", "# Test Plan\n\nThis is a test plan created by the file manager skill.")
    print("Create file result:", json.dumps(result, indent=2))

    # Example: List files in the plans folder
    list_result = list_files("plans")
    print("List files result:", json.dumps(list_result, indent=2))

    # Example: Read the created file
    if list_result["status"] == "success" and list_result["file_count"] > 0:
        file_to_read = list_result["files"][0]["path"]
        read_result = read_file(file_to_read)
        print("Read file result:", json.dumps(read_result, indent=2))


if __name__ == "__main__":
    run_example()