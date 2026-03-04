"""
Session 09 — Agent Teams
==========================
Multiple agents running concurrently, communicating via file-based mailboxes.
Each agent has an inbox it polls and an outbox it writes to.

This is the foundation of how Claude Code handles multi-agent worktrees:
agents are isolated processes that coordinate through shared state.

Architecture:
  mailboxes/
    orchestrator.jsonl   ← orchestrator's inbox
    researcher.jsonl     ← researcher's inbox
    writer.jsonl         ← writer's inbox

  Message schema:
    {"from": "orchestrator", "to": "researcher", "task": "...", "id": "msg-1"}

  Each agent runs its own agent_loop(), polling its inbox for new messages
  and writing results back to the sender's mailbox.

TODO: Implement
  - send_message(to, task, context) → writes to mailboxes/{to}.jsonl
  - read_inbox(agent_name) → reads and clears own mailbox
  - Orchestrator loop: sends tasks, waits for replies, aggregates results
  - Worker loop: reads inbox, processes task, sends reply
  - Run agents in separate threads or processes

Key challenge: the orchestrator must know when all workers are done.
Solution: use a shared results dict with a threading.Event per message ID.
"""

# Core mailbox functions:
#
# import json, threading
# from pathlib import Path
#
# MAILBOX_DIR = Path("mailboxes")
# MAILBOX_DIR.mkdir(exist_ok=True)
# _locks: dict[str, threading.Lock] = {}
#
# def send_message(to: str, task: str, from_agent: str, msg_id: str) -> None:
#     msg = {"id": msg_id, "from": from_agent, "task": task}
#     lock = _locks.setdefault(to, threading.Lock())
#     with lock:
#         with open(MAILBOX_DIR / f"{to}.jsonl", "a") as f:
#             f.write(json.dumps(msg) + "\n")
#
# def read_inbox(agent_name: str) -> list[dict]:
#     path = MAILBOX_DIR / f"{agent_name}.jsonl"
#     if not path.exists():
#         return []
#     lock = _locks.setdefault(agent_name, threading.Lock())
#     with lock:
#         messages = [json.loads(line) for line in path.read_text().splitlines() if line]
#         path.write_text("")  # clear inbox
#     return messages

print("Session 09 — Agent Teams (see docstring for implementation guide)")
