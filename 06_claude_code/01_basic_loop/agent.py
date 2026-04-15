"""
Session 01 — The Basic Agent Loop
===================================
The minimal agentic loop. Nothing else.

The entire agent is: call LLM → if tool_use → run tool → append result → repeat.
Every agent framework you'll use in later sections wraps this exact pattern.

Run:
    python 06_claude_code/01_basic_loop/agent.py
"""

import subprocess

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command and return its output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."}
            },
            "required": ["command"],
        },
    }
]

BLOCKED = ["rm -rf /", "sudo rm", "> /dev/sd", "mkfs"]


def run_bash(command: str) -> str:
    if any(b in command for b in BLOCKED):
        return f"Blocked: '{command}' is not allowed."
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = (result.stdout + result.stderr).strip()
        return output[:10_000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30s"
    except Exception as e:
        return f"Error: {e}"


def agent_loop(user_message: str) -> str:
    """Run the agent loop until the model stops requesting tool calls."""
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system="You are a coding agent. Use bash to accomplish tasks. Be concise.",
            messages=messages,
            tools=TOOLS,
        )

        # Always append the assistant's response to maintain conversation history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Model is done — extract and return the final text
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Execute every tool call and collect results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [bash] {block.input['command']}")
                output = run_bash(block.input["command"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        # Feed results back so the model can continue reasoning
        messages.append({"role": "user", "content": tool_results})


def main():
    print("Agent ready (session 01 — basic loop). Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        answer = agent_loop(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
