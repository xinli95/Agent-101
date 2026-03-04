"""
Session 06 — Context Management
==================================
As conversations grow, the context window fills up and API costs rise.
Solution: when messages exceed a token threshold, summarize the oldest
messages into a single compact summary, preserving the most recent turns verbatim.

Key insight: this is exactly what Claude Code does when it prints
"Auto-compacting context..." — it calls the LLM on old messages, replaces
them with a summary, and continues the session seamlessly.

Three-layer strategy:
  1. System prompt  — always in context, never compressed
  2. Summary block  — replaces old messages once threshold is hit
  3. Recent window  — last KEEP_RECENT messages kept verbatim

The loop doesn't change. Compression is transparent to the agent.

Run:
    python 06_claude_code/06_context_mgmt/agent.py
"""

import subprocess

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

COMPRESS_THRESHOLD = 20_000   # estimated tokens before compression triggers
KEEP_RECENT = 6               # number of recent messages to always keep verbatim


def estimate_tokens(messages: list) -> int:
    """Rough token estimate: total characters / 4."""
    total_chars = sum(len(str(m)) for m in messages)
    return total_chars // 4


def compress_messages(messages: list) -> tuple[list, bool]:
    """
    If messages exceed the threshold, summarize the oldest ones.
    Returns (new_messages, was_compressed).
    """
    if estimate_tokens(messages) < COMPRESS_THRESHOLD or len(messages) <= KEEP_RECENT:
        return messages, False

    to_compress = messages[:-KEEP_RECENT]
    to_keep = messages[-KEEP_RECENT:]

    print(f"\n  [context] Compressing {len(to_compress)} old messages "
          f"(~{estimate_tokens(to_compress):,} tokens)...")

    # Use a fast, cheap model for summarization
    summary_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=(
            "You are a conversation summarizer. Produce a dense, factual summary of the "
            "conversation history below. Preserve: key decisions, file paths, commands run, "
            "errors encountered, and any information the agent will need to continue. "
            "Omit: pleasantries, repeated content, verbose explanations."
        ),
        messages=[{"role": "user", "content": f"Summarize this conversation:\n\n{to_compress}"}],
    )
    summary = summary_response.content[0].text

    # Replace old messages with a single summary block
    compressed = [
        {
            "role": "user",
            "content": f"[Conversation summary — {len(to_compress)} prior messages compressed]\n\n{summary}",
        },
        {"role": "assistant", "content": "Understood. I have the context from the summary and will continue."},
    ]

    new_messages = compressed + to_keep
    print(f"  [context] Compressed to ~{estimate_tokens(new_messages):,} tokens.\n")
    return new_messages, True


# --- Tools ---

def run_bash(command: str) -> str:
    blocked = ["rm -rf /", "sudo rm"]
    if any(b in command for b in blocked):
        return f"Blocked: {command}"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip()[:10_000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"


TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    }
]


def agent_loop(user_message: str, messages: list | None = None) -> tuple[str, list]:
    """
    Returns (final_answer, updated_messages).
    Pass messages in to maintain history across calls (multi-turn session).
    """
    if messages is None:
        messages = []
    messages.append({"role": "user", "content": user_message})

    while True:
        # Compress before calling the LLM if context is getting large
        messages, compressed = compress_messages(messages)
        if compressed:
            print(f"  [context] Token estimate after compression: ~{estimate_tokens(messages):,}\n")

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system="You are a helpful coding agent. Use bash to accomplish tasks.",
            messages=messages,
            tools=TOOLS,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text, messages
            return "", messages

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [bash] {block.input['command']!r:.80s}")
                output = run_bash(block.input["command"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        messages.append({"role": "user", "content": tool_results})


def main():
    print("Agent ready (session 06 — context management). Type 'exit' to quit.")
    print(f"Compression threshold: ~{COMPRESS_THRESHOLD:,} tokens, keeping last {KEEP_RECENT} messages.\n")

    session_messages: list = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print(f"  [context] Current size: ~{estimate_tokens(session_messages):,} tokens")
        print()
        answer, session_messages = agent_loop(user_input, session_messages)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
