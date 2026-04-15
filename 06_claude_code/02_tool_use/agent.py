"""
Session 02 — Multiple Tools
==============================
Add bash, read, write, and edit tools. The loop doesn't change —
only the dispatch map grows.

Key insight: "adding a tool means adding one handler and one entry in TOOL_HANDLERS."

Run:
    python 06_claude_code/02_tool_use/agent.py
"""

import os
import subprocess
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
WORK_DIR = Path.cwd()


def safe_path(p: str) -> Path:
    """Resolve a path and ensure it stays inside WORK_DIR."""
    resolved = (WORK_DIR / p).resolve()
    if not str(resolved).startswith(str(WORK_DIR)):
        raise ValueError(f"Path escape blocked: {p}")
    return resolved


# --- Tool handlers ---

def run_bash(command: str) -> str:
    blocked = ["rm -rf /", "sudo rm", "> /dev/sd"]
    if any(b in command for b in blocked):
        return f"Blocked: '{command}'"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = (result.stdout + result.stderr).strip()
        return output[:10_000] or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: timed out"
    except Exception as e:
        return f"Error: {e}"


def run_read(file_path: str, limit: int = 200) -> str:
    try:
        path = safe_path(file_path)
        lines = path.read_text().splitlines()
        excerpt = "\n".join(f"{i+1}: {l}" for i, l in enumerate(lines[:limit]))
        if len(lines) > limit:
            excerpt += f"\n... ({len(lines) - limit} more lines)"
        return excerpt
    except Exception as e:
        return f"Error reading {file_path}: {e}"


def run_write(file_path: str, content: str) -> str:
    try:
        path = safe_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Written {len(content)} chars to {file_path}"
    except Exception as e:
        return f"Error writing {file_path}: {e}"


def run_edit(file_path: str, old_string: str, new_string: str) -> str:
    try:
        path = safe_path(file_path)
        original = path.read_text()
        if old_string not in original:
            return f"Error: string not found in {file_path}"
        path.write_text(original.replace(old_string, new_string, 1))
        return f"Edit applied to {file_path}"
    except Exception as e:
        return f"Error editing {file_path}: {e}"


TOOL_HANDLERS = {
    "bash":  lambda i: run_bash(i["command"]),
    "read":  lambda i: run_read(i["file_path"], i.get("limit", 200)),
    "write": lambda i: run_write(i["file_path"], i["content"]),
    "edit":  lambda i: run_edit(i["file_path"], i["old_string"], i["new_string"]),
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
        "name": "read",
        "description": "Read a file and return its contents with line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "limit": {"type": "integer", "description": "Max lines to return (default 200)"},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "write",
        "description": "Write content to a file, creating it if it doesn't exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "edit",
        "description": "Replace the first occurrence of old_string with new_string in a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
            },
            "required": ["file_path", "old_string", "new_string"],
        },
    },
]


def agent_loop(user_message: str) -> str:
    """The loop is identical to session 01 — only the tools changed."""
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system="You are a coding agent. Use tools to read, write, and edit files.",
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
                print(f"  [{block.name}] {list(block.input.values())[0]!r:.80s}")
                result = TOOL_HANDLERS[block.name](block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})


def main():
    print("Agent ready (session 02 — tool use). Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        answer = agent_loop(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
