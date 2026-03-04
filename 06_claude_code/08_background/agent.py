"""
Session 08 — Background Operations
=====================================
Long-running tools (test suite, build, deploy) block the agent loop.
Solution: run them in daemon threads, return a job ID immediately,
and let the agent check status or wait for completion later.

Key insight: this is how Claude Code runs `pytest` or `npm build` in the
background while staying responsive to follow-up questions.

New tools in this session:
  run_background(command)  → job_id   (non-blocking, returns immediately)
  check_job(job_id)        → status + output so far
  wait_for_job(job_id)     → blocks until done, returns full output
  list_jobs()              → all jobs and their statuses

Run:
    python 06_claude_code/08_background/agent.py
"""

import subprocess
import threading
import uuid
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# Job registry: id → {command, status, output, thread}
JOBS: dict[str, dict] = {}
_jobs_lock = threading.Lock()


# --- Job management ---

def run_background(command: str) -> str:
    """Start a shell command in a daemon thread. Returns immediately with a job ID."""
    job_id = str(uuid.uuid4())[:8]
    job = {"id": job_id, "command": command, "status": "running", "output": ""}

    with _jobs_lock:
        JOBS[job_id] = job

    def _worker():
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=300
            )
            output = (result.stdout + result.stderr).strip()
            with _jobs_lock:
                job["output"] = output[:50_000]
                job["status"] = "done" if result.returncode == 0 else "error"
                job["returncode"] = result.returncode
        except subprocess.TimeoutExpired:
            with _jobs_lock:
                job["status"] = "error"
                job["output"] = "Error: command timed out after 300s"
        except Exception as e:
            with _jobs_lock:
                job["status"] = "error"
                job["output"] = f"Error: {e}"

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    with _jobs_lock:
        job["thread"] = thread

    return f"Job {job_id} started in background: {command!r}\nUse check_job('{job_id}') to poll or wait_for_job('{job_id}') to block."


def check_job(job_id: str) -> str:
    """Return the current status and latest output of a background job."""
    with _jobs_lock:
        job = JOBS.get(job_id)
    if not job:
        return f"Job {job_id} not found. Use list_jobs() to see all jobs."
    output_tail = job["output"][-2000:] if job["output"] else "(no output yet)"
    return f"[{job['status'].upper()}] Job {job_id}: {job['command']!r}\n\n{output_tail}"


def wait_for_job(job_id: str) -> str:
    """Block until a background job finishes. Returns the full output."""
    with _jobs_lock:
        job = JOBS.get(job_id)
    if not job:
        return f"Job {job_id} not found."
    if job["status"] != "running":
        return check_job(job_id)

    print(f"  [background] Waiting for job {job_id}...")
    job["thread"].join()

    with _jobs_lock:
        status = job["status"]
        output = job["output"] or "(no output)"
    return f"[{status.upper()}] Job {job_id} finished.\n\n{output}"


def list_jobs() -> str:
    """List all background jobs and their current status."""
    with _jobs_lock:
        jobs = list(JOBS.values())
    if not jobs:
        return "No background jobs."
    STATUS_ICON = {"running": "⟳", "done": "✓", "error": "✗"}
    lines = [
        f"  {STATUS_ICON.get(j['status'], '?')} {j['id']}  [{j['status']}]  {j['command']!r:.60s}"
        for j in jobs
    ]
    return "\n".join(lines)


def run_bash(command: str) -> str:
    """Synchronous bash — for quick commands."""
    blocked = ["rm -rf /", "sudo rm"]
    if any(b in command for b in blocked):
        return f"Blocked: {command}"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip()[:10_000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"


TOOL_HANDLERS = {
    "bash":            lambda i: run_bash(i["command"]),
    "run_background":  lambda i: run_background(i["command"]),
    "check_job":       lambda i: check_job(i["job_id"]),
    "wait_for_job":    lambda i: wait_for_job(i["job_id"]),
    "list_jobs":       lambda i: list_jobs(),
}

TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command synchronously (blocks until done). Use for quick commands (<5s).",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
    {
        "name": "run_background",
        "description": (
            "Start a long-running shell command in the background. Returns immediately with a job ID. "
            "Use for: test suites, builds, installs, or any command that takes >5 seconds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Shell command to run in background"}},
            "required": ["command"],
        },
    },
    {
        "name": "check_job",
        "description": "Check the current status and latest output of a background job (non-blocking).",
        "input_schema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
    {
        "name": "wait_for_job",
        "description": "Wait for a background job to complete and return its full output (blocking).",
        "input_schema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
    {
        "name": "list_jobs",
        "description": "List all background jobs and their statuses.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

SYSTEM = """You are a coding agent that can run tasks in the background.

Guidelines:
- Use bash for quick commands (<5s)
- Use run_background for slow commands (tests, builds, installs)
- After starting a background job, you can continue reasoning or ask clarifying questions
- Use wait_for_job when you need the result before proceeding
- Use check_job to poll without blocking"""


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
                cmd_preview = list(block.input.values())[0] if block.input else ""
                print(f"  [{block.name}] {str(cmd_preview)!r:.60s}")
                result = TOOL_HANDLERS[block.name](block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})


def main():
    print("Agent ready (session 08 — background operations). Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        answer = agent_loop(user_input)
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
