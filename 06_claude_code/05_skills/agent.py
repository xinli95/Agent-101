"""
Session 05 — Skill Loading
============================
Skills are markdown files containing knowledge or instructions loaded
into the system prompt on demand.

Key insight: don't stuff everything into the system prompt upfront.
Load only what's needed for the current task. This is how Claude Code's
CLAUDE.md and /memory system works — knowledge is injected per-task,
not pre-loaded for every turn.

The loop doesn't change. Only the system prompt grows dynamically.

Run:
    python 06_claude_code/05_skills/agent.py
"""

import subprocess
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
SKILLS_DIR = Path(__file__).parent / "skills"

# Runtime cache of loaded skills: name → content
LOADED_SKILLS: dict[str, str] = {}

BASE_SYSTEM = "You are a coding agent. Use bash to accomplish tasks. Load skills before tasks that need specific domain knowledge."


def get_system_prompt() -> str:
    """Rebuild system prompt with currently loaded skills injected."""
    if not LOADED_SKILLS:
        return BASE_SYSTEM
    skills_text = "\n\n".join(f"## Skill: {name}\n{content}" for name, content in LOADED_SKILLS.items())
    return f"{BASE_SYSTEM}\n\n# Loaded Knowledge\n\n{skills_text}"


# --- Tool handlers ---

def run_bash(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip()[:10_000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"


def tool_list_skills(_: dict) -> str:
    """List all available skill files."""
    files = sorted(SKILLS_DIR.glob("*.md"))
    if not files:
        return f"No skills found in {SKILLS_DIR}"
    loaded = set(LOADED_SKILLS.keys())
    lines = []
    for f in files:
        name = f.stem
        status = " [loaded]" if name in loaded else ""
        lines.append(f"  {name}{status}")
    return "Available skills:\n" + "\n".join(lines)


def tool_load_skill(name: str) -> str:
    """Load a skill file into the system prompt."""
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        available = [f.stem for f in SKILLS_DIR.glob("*.md")]
        return f"Skill '{name}' not found. Available: {available}"
    content = path.read_text().strip()
    LOADED_SKILLS[name] = content
    return f"Loaded skill '{name}' ({len(content)} chars). It is now active in your system prompt."


def tool_unload_skill(name: str) -> str:
    """Remove a skill from the active system prompt."""
    if name not in LOADED_SKILLS:
        return f"Skill '{name}' is not loaded."
    del LOADED_SKILLS[name]
    return f"Unloaded skill '{name}'."


TOOL_HANDLERS = {
    "bash":         lambda i: run_bash(i["command"]),
    "list_skills":  lambda i: tool_list_skills(i),
    "load_skill":   lambda i: tool_load_skill(i["name"]),
    "unload_skill": lambda i: tool_unload_skill(i["name"]),
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
        "name": "list_skills",
        "description": "List all available skill files and which ones are currently loaded.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "load_skill",
        "description": (
            "Load a skill file into your system prompt. "
            "Call this before tasks that require specific domain knowledge "
            "(e.g., load 'git' before git operations, 'testing' before writing tests)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Skill name without .md extension"}},
            "required": ["name"],
        },
    },
    {
        "name": "unload_skill",
        "description": "Remove a skill from the active system prompt to free context space.",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
]


def agent_loop(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        # Re-read system prompt each turn — picks up newly loaded skills immediately
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=get_system_prompt(),
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
                print(f"  [{block.name}] {list(block.input.values())[:1]}")
                result = TOOL_HANDLERS[block.name](block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})


def main():
    print("Agent ready (session 05 — skill loading). Type 'exit' to quit.")
    print(f"Skills directory: {SKILLS_DIR}\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        answer = agent_loop(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
