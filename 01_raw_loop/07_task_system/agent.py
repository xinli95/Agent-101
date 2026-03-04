"""
Session 07 — Persistent Task System
======================================
Replace the in-memory todo list with a file-based task system that
survives process restarts, supports dependencies between tasks,
and can be shared across multiple agent processes.

This is how Claude Code's TaskCreate/TaskUpdate/TaskList system works.

Task schema:
  {
    "id": "1",
    "subject": "Write unit tests",
    "status": "pending",           # pending | in_progress | completed
    "blockedBy": ["2", "3"],       # task IDs that must complete first
    "blocks": ["4"]                # task IDs waiting on this one
  }

TODO: Implement
  - tasks.json as the persistent store
  - task_create(subject, description, blockedBy=[])
  - task_update(id, status)
  - task_list() → all tasks with their dependency status
  - task_get(id) → full task details
  - Validation: can't mark in_progress if blockedBy tasks aren't completed
"""

# Key functions to implement:
#
# def task_create(subject: str, description: str, blocked_by: list[str] = []) -> str:
#     tasks = _load_tasks()
#     new_id = str(max((int(t["id"]) for t in tasks), default=0) + 1)
#     task = {"id": new_id, "subject": subject, "description": description,
#             "status": "pending", "blockedBy": blocked_by, "blocks": []}
#     # Update the 'blocks' field of the tasks this one depends on
#     for dep_id in blocked_by:
#         for t in tasks:
#             if t["id"] == dep_id:
#                 t["blocks"].append(new_id)
#     tasks.append(task)
#     _save_tasks(tasks)
#     return f"Task {new_id} created: {subject}"
#
# def task_update(task_id: str, status: str) -> str:
#     tasks = _load_tasks()
#     task = next((t for t in tasks if t["id"] == task_id), None)
#     if not task:
#         return f"Task {task_id} not found"
#     if status == "in_progress":
#         blocking = [t for t in tasks if t["id"] in task["blockedBy"] and t["status"] != "completed"]
#         if blocking:
#             return f"Blocked by: {[t['subject'] for t in blocking]}"
#     task["status"] = status
#     _save_tasks(tasks)
#     return f"Task {task_id} → {status}"

print("Session 07 — Persistent Task System (see docstring for implementation guide)")
