"""
Session 04 — Subagents
========================
The orchestrator spawns subagents for self-contained subtasks.
Each subagent gets a clean, minimal context — no accumulated history.

Key insight: a subagent is just agent_loop() called recursively
with a focused prompt. The outer agent hands off, collects the result,
and continues.

Run:
    python 06_claude_code/04_subagents/agent.py
"""

import subprocess

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

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
        "name": "spawn_subagent",
        "description": (
            "Delegate a self-contained subtask to a focused subagent. "
            "The subagent has no knowledge of the parent conversation — "
            "provide all necessary context in the task description. "
            "Returns the subagent's final answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Complete, self-contained task description for the subagent.",
                },
                "context": {
                    "type": "string",
                    "description": "Any additional context the subagent needs (optional).",
                },
            },
            "required": ["task"],
        },
    },
]


def run_bash(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip()[:10_000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"


def run_subagent(task: str, context: str = "") -> str:
    """A minimal single-tool agent with clean context."""
    system = "You are a focused subagent. Complete the given task concisely using bash."
    if context:
        system += f"\n\nContext:\n{context}"

    subagent_tools = [TOOLS[0]]  # only bash
    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=subagent_tools,
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
                print(f"    [subagent:bash] {block.input['command']!r:.60s}")
                output = run_bash(block.input["command"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": tool_results})


TOOL_HANDLERS = {
    "bash":           lambda i: run_bash(i["command"]),
    "spawn_subagent": lambda i: run_subagent(i["task"], i.get("context", "")),
}

SYSTEM = """You are an orchestrating agent. For complex tasks:
- Break them into independent subtasks
- Delegate each subtask to a subagent via spawn_subagent
- Each subagent gets clean context — include everything it needs in the task description
- Combine the subagent results into a final answer"""


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
    print("Agent ready (session 04 — subagents). Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        answer = agent_loop(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
