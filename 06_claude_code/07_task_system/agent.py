"""
Session 07 — Persistent Task System
======================================
Replace the in-memory todo list from session 03 with a file-based task system
that survives process restarts, supports dependency graphs between tasks,
and can be shared across multiple agent processes.

This is how Claude Code's TaskCreate/TaskUpdate/TaskList/TaskGet tools work.

Task schema:
  {
    "id": "1",
    "subject": "Write unit tests",
    "description": "Add pytest tests for the auth module",
    "status": "pending",       # pending | in_progress | completed
    "blockedBy": ["2"],        # task IDs that must complete first
    "blocks": ["3"]            # task IDs waiting on this one
  }

Run:
    python 06_claude_code/07_task_system/agent.py
"""

import json
import subprocess
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
TASKS_FILE = Path(__file__).parent / "tasks.json"


# --- Task store ---

def _load() -> list[dict]:
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []


def _save(tasks: list[dict]) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def _next_id(tasks: list[dict]) -> str:
    return str(max((int(t["id"]) for t in tasks), default=0) + 1)


# --- Tool implementations ---

def task_create(subject: str, description: str, blocked_by: list[str] | None = None) -> str:
    tasks = _load()
    blocked_by = blocked_by or []

    # Validate that all blocked_by IDs exist
    existing_ids = {t["id"] for t in tasks}
    missing = [bid for bid in blocked_by if bid not in existing_ids]
    if missing:
        return f"Error: unknown task IDs in blockedBy: {missing}"

    new_id = _next_id(tasks)
    task = {
        "id": new_id,
        "subject": subject,
        "description": description,
        "status": "pending",
        "blockedBy": blocked_by,
        "blocks": [],
    }

    # Register this task as a blocker in its dependencies
    for dep_id in blocked_by:
        for t in tasks:
            if t["id"] == dep_id:
                t["blocks"].append(new_id)

    tasks.append(task)
    _save(tasks)
    dep_str = f" (blocked by: {blocked_by})" if blocked_by else ""
    return f"Task {new_id} created: '{subject}'{dep_str}"


def task_update(task_id: str, status: str) -> str:
    valid_statuses = {"pending", "in_progress", "completed"}
    if status not in valid_statuses:
        return f"Invalid status '{status}'. Valid: {valid_statuses}"

    tasks = _load()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return f"Task {task_id} not found"

    # Enforce dependency order: can't start if blockers aren't done
    if status == "in_progress":
        blocking = [
            t for t in tasks
            if t["id"] in task["blockedBy"] and t["status"] != "completed"
        ]
        if blocking:
            subjects = [f"#{t['id']} {t['subject']}" for t in blocking]
            return f"Cannot start task {task_id} — blocked by: {subjects}"

    old_status = task["status"]
    task["status"] = status
    _save(tasks)
    return f"Task {task_id} '{task['subject']}': {old_status} → {status}"


def task_list() -> str:
    tasks = _load()
    if not tasks:
        return "No tasks."

    STATUS_ICON = {"pending": "○", "in_progress": "◑", "completed": "●"}
    lines = []
    for t in tasks:
        icon = STATUS_ICON.get(t["status"], "?")
        blockers = f" [blocked by: {t['blockedBy']}]" if t["blockedBy"] and t["status"] == "pending" else ""
        lines.append(f"  {icon} #{t['id']} {t['subject']}{blockers}")
    return "\n".join(lines)


def task_get(task_id: str) -> str:
    tasks = _load()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return f"Task {task_id} not found"
    return json.dumps(task, indent=2)


def run_bash(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip()[:10_000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"


TOOL_HANDLERS = {
    "bash":        lambda i: run_bash(i["command"]),
    "task_create": lambda i: task_create(i["subject"], i["description"], i.get("blocked_by")),
    "task_update": lambda i: task_update(i["task_id"], i["status"]),
    "task_list":   lambda i: task_list(),
    "task_get":    lambda i: task_get(i["task_id"]),
}

TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
    {
        "name": "task_create",
        "description": (
            "Create a new task. For multi-step work, create all tasks upfront "
            "with dependencies so progress is visible and order is enforced."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Short imperative title, e.g. 'Write unit tests'"},
                "description": {"type": "string", "description": "What needs to be done and why"},
                "blocked_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs that must complete before this one can start",
                },
            },
            "required": ["subject", "description"],
        },
    },
    {
        "name": "task_update",
        "description": "Update a task's status. Mark in_progress when starting, completed when done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "task_list",
        "description": "List all tasks with their status and dependency information.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "task_get",
        "description": "Get full details of a specific task including its description and dependencies.",
        "input_schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
]

SYSTEM = """You are a coding agent with a persistent task system.

For any work involving more than 2 steps:
1. Call task_create for each step upfront — set blocked_by to enforce ordering
2. Call task_update(id, "in_progress") when you start a task
3. Call task_update(id, "completed") when you finish it
4. Call task_list periodically to track progress

Tasks persist to disk — they survive process restarts."""


def agent_loop(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [{block.name}]")
                result = TOOL_HANDLERS[block.name](block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})


def main():
    print("Agent ready (session 07 — task system). Type 'exit' to quit.")
    print(f"Tasks stored at: {TASKS_FILE}\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        answer = agent_loop(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
