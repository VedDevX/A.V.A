import json          # To read/write tasks as JSON in a file
import os            # To check if the task file exists
from datetime import datetime  # To store timestamps for tasks

# ===============================
# Constants
# ===============================
TODO_FILE = "tasks.json"  # File to store all tasks

# ===============================
# Load tasks from file (if it exists)
# ===============================
if os.path.exists(TODO_FILE):
    with open(TODO_FILE, "r") as f:
        # Read tasks from JSON file and convert to Python list of dictionaries
        tasks = json.load(f)
else:
    # If file doesn't exist, start with an empty task list
    tasks = []

# ===============================
# Helper function: Save tasks to file
# ===============================
def _save_tasks():
    """
    Write the current tasks list to the JSON file.
    indent=2 makes the file human-readable.
    """
    with open(TODO_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

# ===============================
# Add a task
# ===============================
def add_task(title: str):
    """
    Add a task with metadata like ID, status, and timestamp.

    Args:
        title (str): The title/description of the task.

    Returns:
        str: Success or error message.
    """
    title = title.strip()  # Remove leading/trailing spaces
    if not title:
        return "Task cannot be empty"

    # Check for duplicates (case-insensitive)
    for t in tasks:
        if t["title"].lower() == title.lower():
            return "Task already exists"

    # Create the task dictionary
    task = {
        "id": len(tasks) + 1,           # Simple incremental ID
        "title": title,
        "status": "pending",            # Default status
        "created_at": datetime.now().isoformat()  # Store creation time
    }

    # Add to list and save to file
    tasks.append(task)
    _save_tasks()
    return f"Task added: {title}"

# ===============================
# Get tasks
# ===============================
def get_tasks(status: str = None):
    """
    Return all tasks, or filter by status (pending/done).

    Args:
        status (str, optional): Filter by "pending" or "done". Defaults to None.

    Returns:
        list: List of task dictionaries.
    """
    if status not in ("pending", "done", None):
        return []
    # Filter tasks if status is provided
    return [t for t in tasks if status is None or t["status"] == status]

# ===============================
# Remove a task
# ===============================
def remove_task(task_id: int):
    """
    Remove a task by its ID.

    Args:
        task_id (int): The ID of the task to remove.

    Returns:
        str: Success or error message.
    """
    global tasks
    for t in tasks:
        if t["id"] == task_id:
            tasks.remove(t)  # Remove from list
            _save_tasks()    # Save updated list to file
            return f"Removed task: {t['title']}"
    return "Task not found"

# ===============================
# Mark a task as done
# ===============================
def mark_done(task_id: int):
    """
    Mark a task's status as "done" by its ID.

    Args:
        task_id (int): The ID of the task to mark done.

    Returns:
        str: Success or error message.
    """
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            _save_tasks()  # Save the change
            return f"Marked done: {t['title']}"
    return "Task not found"
