"""
Session 03 — Planning with TodoWrite
=======================================
Add a TodoWrite tool so the agent can break tasks into steps,
track progress, and avoid drifting on long tasks.

Key insight: structured planning is just another tool.
The loop still doesn't change.

Run:
    python 06_claude_code/03_planning/agent.py
"""

import json
import subprocess
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
WORK_DIR = Path.cwd()
TODO_FILE = WORK_DIR / ".agent_todos.json"


# --- Todo store ---

def _load_todos() -> list[dict]:
    if TODO_FILE.exists():
        return json.loads(TODO_FILE.read_text())
    return []


def _save_todos(todos: list[dict]) -> None:
    TODO_FILE.write_text(json.dumps(todos, indent=2))


def run_todo_write(todos: list[dict]) -> str:
    """Replace the task list with a new set of todos."""
    _save_todos(todos)
    lines = [f"  [{t['status']}] {t['id']}: {t['content']}" for t in todos]
    return "Task list updated:\n" + "\n".join(lines)


def run_todo_update(todo_id: str, status: str) -> str:
    """Update the status of a specific todo."""
    todos = _load_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["status"] = status
            _save_todos(todos)
            return f"Task {todo_id} → {status}"
    return f"Task {todo_id} not found"


def run_todo_read() -> str:
    todos = _load_todos()
    if not todos:
        return "No tasks."
    lines = [f"  [{t['status']}] {t['id']}: {t['content']}" for t in todos]
    return "\n".join(lines)


# --- Other tools (carried over from session 02) ---

def run_bash(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip()[:10_000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"


TOOL_HANDLERS = {
    "bash":         lambda i: run_bash(i["command"]),
    "todo_write":   lambda i: run_todo_write(i["todos"]),
    "todo_update":  lambda i: run_todo_update(i["todo_id"], i["status"]),
    "todo_read":    lambda i: run_todo_read(),
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
        "name": "todo_write",
        "description": "Create or replace the task list. Call this at the start of any multi-step task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "content": {"type": "string"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                        },
                        "required": ["id", "content", "status"],
                    },
                }
            },
            "required": ["todos"],
        },
    },
    {
        "name": "todo_update",
        "description": "Update the status of a task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
            },
            "required": ["todo_id", "status"],
        },
    },
    {
        "name": "todo_read",
        "description": "Read the current task list.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

SYSTEM = """You are a coding agent. For any task with more than 2 steps:
1. Call todo_write to create a plan first
2. Mark tasks in_progress when you start them
3. Mark tasks completed when done
Use bash to execute tasks."""


def agent_loop(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
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
    print("Agent ready (session 03 — planning). Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        answer = agent_loop(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
