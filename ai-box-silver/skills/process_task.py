"""
Agent Skill: Process Task
This skill allows Claude Code to process tasks in the needs_action folder
"""
import json
from pathlib import Path
from datetime import datetime


def process_task(task_file_path: str, action: str = "review") -> dict:
    """
    Process a task file from the needs_action folder

    Args:
        task_file_path (str): Path to the task file to process
        action (str): What action to take on the task (review, complete, escalate)

    Returns:
        dict: Result of the task processing
    """
    task_path = Path(task_file_path)

    if not task_path.exists():
        return {
            "status": "error",
            "message": f"Task file does not exist: {task_file_path}",
            "timestamp": datetime.now().isoformat()
        }

    # Read the task file
    try:
        content = task_path.read_text(encoding='utf-8')

        # Parse frontmatter if it exists
        frontmatter = {}
        lines = content.split('\n')
        if lines and lines[0].strip() == '---':
            # Look for frontmatter
            end_fm_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end_fm_idx = i
                    break

            if end_fm_idx > 0:
                fm_content = '\n'.join(lines[1:end_fm_idx])
                for line in fm_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

        result = {
            "status": "success",
            "task_file": task_file_path,
            "action_taken": action,
            "original_content": content[:200] + "..." if len(content) > 200 else content,  # Truncate for display
            "metadata": frontmatter,
            "timestamp": datetime.now().isoformat()
        }

        # Move the file based on action
        project_root = task_path.parent.parent  # Go up from needs_action to project root

        if action == "complete":
            done_folder = project_root / "done"
            done_folder.mkdir(exist_ok=True)
            new_path = done_folder / task_path.name
            task_path.rename(new_path)
            result["new_location"] = str(new_path)
            result["message"] = f"Task completed and moved to done folder: {task_path.name}"

        elif action == "review":
            result["message"] = f"Task reviewed: {task_path.name}"

        elif action == "escalate":
            pending_approval = project_root / "pending_approval"
            pending_approval.mkdir(exist_ok=True)
            new_path = pending_approval / task_path.name
            task_path.rename(new_path)
            result["new_location"] = str(new_path)
            result["message"] = f"Task escalated and moved to pending approval: {task_path.name}"

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing task file: {str(e)}",
            "task_file": task_file_path,
            "timestamp": datetime.now().isoformat()
        }


def list_pending_tasks() -> dict:
    """
    List all pending tasks in the needs_action folder

    Returns:
        dict: List of pending task files
    """
    project_root = Path(__file__).parent.parent  # Go up to project root
    needs_action = project_root / "needs_action"

    if not needs_action.exists():
        return {
            "status": "error",
            "message": "needs_action folder does not exist",
            "tasks": [],
            "timestamp": datetime.now().isoformat()
        }

    task_files = list(needs_action.glob("*.md")) + list(needs_action.glob("*.txt"))

    tasks = []
    for task_file in task_files:
        tasks.append({
            "filename": task_file.name,
            "path": str(task_file),
            "size": task_file.stat().st_size,
            "modified": datetime.fromtimestamp(task_file.stat().st_mtime).isoformat()
        })

    return {
        "status": "success",
        "task_count": len(tasks),
        "tasks": tasks,
        "timestamp": datetime.now().isoformat()
    }


# Example usage function
def run_example():
    """Example of how to use the process_task skill"""
    project_root = Path(__file__).parent.parent
    needs_action = project_root / "needs_action"

    # List all pending tasks
    result = list_pending_tasks()
    print("Pending tasks:", json.dumps(result, indent=2))

    # Process the first task if one exists
    if result["status"] == "success" and result["task_count"] > 0:
        first_task = result["tasks"][0]["path"]
        process_result = process_task(first_task, "review")
        print("Process result:", json.dumps(process_result, indent=2))


if __name__ == "__main__":
    run_example()