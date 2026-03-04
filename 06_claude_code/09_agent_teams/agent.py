"""
Session 09 — Agent Teams
==========================
Multiple specialized agents running concurrently, communicating via
file-based JSONL mailboxes. Each agent has an inbox it polls; replies
go back to the sender's inbox.

This is the foundation of how Claude Code's multi-agent worktree mode works:
isolated agent processes coordinate through shared state on disk.

Architecture:
  mailboxes/
    orchestrator.jsonl    ← orchestrator reads replies here
    researcher.jsonl      ← researcher reads tasks here
    writer.jsonl          ← writer reads tasks here

  Message: {"id": str, "from": str, "task": str, "context": str}
  Reply:   {"id": str, "from": str, "result": str}

The orchestrator uses a `delegate(worker, task)` tool that:
  1. Writes the task to the worker's mailbox
  2. Waits on a threading.Event for the reply
  3. Returns the result when the worker is done

Workers run in daemon threads, each with their own agent_loop.

Run:
    python 06_claude_code/09_agent_teams/agent.py
"""

import json
import threading
import uuid
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MAILBOX_DIR = Path(__file__).parent / "mailboxes"
MAILBOX_DIR.mkdir(exist_ok=True)

# Shared result store and per-message events for synchronization
_RESULTS: dict[str, str] = {}
_EVENTS: dict[str, threading.Event] = {}
_lock = threading.Lock()


# --- Mailbox primitives ---

def _inbox_path(agent_name: str) -> Path:
    return MAILBOX_DIR / f"{agent_name}.jsonl"


def send_message(to: str, msg: dict) -> None:
    path = _inbox_path(to)
    with _lock:
        with open(path, "a") as f:
            f.write(json.dumps(msg) + "\n")


def read_inbox(agent_name: str) -> list[dict]:
    path = _inbox_path(agent_name)
    if not path.exists():
        return []
    with _lock:
        lines = path.read_text().splitlines()
        path.write_text("")  # clear after reading
    return [json.loads(line) for line in lines if line.strip()]


# --- Mini agent loop for workers (bash-only, focused) ---

def worker_agent_loop(task: str, system: str) -> str:
    """Minimal agent loop used by worker threads."""
    messages = [{"role": "user", "content": task}]
    tools = [
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

    import subprocess

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=tools,
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
                try:
                    result = subprocess.run(
                        block.input["command"], shell=True,
                        capture_output=True, text=True, timeout=30,
                    )
                    output = (result.stdout + result.stderr).strip()[:5_000] or "(no output)"
                except Exception as e:
                    output = f"Error: {e}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": tool_results})


# --- Worker thread: poll inbox, process tasks, send replies ---

def run_worker(name: str, system_prompt: str, stop_event: threading.Event) -> None:
    print(f"  [team] Worker '{name}' started.")
    while not stop_event.is_set():
        messages = read_inbox(name)
        for msg in messages:
            print(f"  [team] '{name}' received task: {msg['task']!r:.60s}")
            result = worker_agent_loop(msg["task"], system_prompt)
            reply = {"id": msg["id"], "from": name, "result": result}
            send_message(msg["from"], reply)
            print(f"  [team] '{name}' sent reply for msg {msg['id']}")
        stop_event.wait(timeout=0.3)  # poll interval


# --- Orchestrator's delegate tool ---

def delegate(worker_name: str, task: str, context: str = "") -> str:
    """Send a task to a worker and block until the reply arrives."""
    msg_id = str(uuid.uuid4())[:8]
    event = threading.Event()

    with _lock:
        _EVENTS[msg_id] = event

    full_task = f"{task}\n\nContext:\n{context}" if context else task
    send_message(worker_name, {"id": msg_id, "from": "orchestrator", "task": full_task})

    # Poll orchestrator's own inbox for the reply
    def _wait_for_reply():
        while True:
            replies = read_inbox("orchestrator")
            for reply in replies:
                if reply.get("id") == msg_id:
                    with _lock:
                        _RESULTS[msg_id] = reply["result"]
                    event.set()
                    return
                else:
                    # Not our reply — put it back
                    send_message("orchestrator", reply)
            event.wait(timeout=0.3)
            if event.is_set():
                return

    reply_thread = threading.Thread(target=_wait_for_reply, daemon=True)
    reply_thread.start()
    event.wait(timeout=60)

    with _lock:
        result = _RESULTS.pop(msg_id, "Error: reply timed out after 60s")
        _EVENTS.pop(msg_id, None)

    return result


# --- Orchestrator agent ---

TOOL_HANDLERS = {
    "delegate": lambda i: delegate(i["worker"], i["task"], i.get("context", "")),
}

TOOLS = [
    {
        "name": "delegate",
        "description": (
            "Delegate a self-contained task to a specialist worker agent. "
            "Blocks until the worker replies. Available workers:\n"
            "  - 'researcher': finds facts, summarizes information\n"
            "  - 'writer': drafts content, rewrites prose"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "worker": {"type": "string", "enum": ["researcher", "writer"]},
                "task": {"type": "string", "description": "Complete, self-contained task description"},
                "context": {"type": "string", "description": "Additional context the worker needs"},
            },
            "required": ["worker", "task"],
        },
    }
]

ORCHESTRATOR_SYSTEM = """You are an orchestrator. You coordinate a team of specialist agents.

For content creation tasks:
1. Delegate research to the 'researcher' worker
2. Pass the research results as context when delegating writing to the 'writer' worker
3. Combine the results into a final answer

Always delegate to specialists — don't answer from your own knowledge."""


def agent_loop(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=ORCHESTRATOR_SYSTEM,
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
                worker = block.input.get("worker", "?")
                task_preview = block.input.get("task", "")[:60]
                print(f"  [delegate → {worker}] {task_preview!r}")
                result = TOOL_HANDLERS[block.name](block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})


def main():
    # Start worker threads
    stop_event = threading.Event()
    workers = {
        "researcher": "You are a research specialist. Summarize key facts concisely in 2-3 sentences.",
        "writer":     "You are a writing specialist. Transform notes into one clear, engaging paragraph.",
    }
    worker_threads = []
    for name, system in workers.items():
        t = threading.Thread(target=run_worker, args=(name, system, stop_event), daemon=True)
        t.start()
        worker_threads.append(t)

    print("Agent team ready (session 09 — agent teams).")
    print(f"Workers: {list(workers.keys())}. Mailboxes: {MAILBOX_DIR}\n")

    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit", "q") or not user_input:
                break
            print()
            answer = agent_loop(user_input)
            print(f"\nAgent: {answer}\n")
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
