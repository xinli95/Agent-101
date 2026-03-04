"""
Session 08 — Background Operations
=====================================
Long-running tools (build, test suite, deploy) block the agent loop.
Solution: run them in daemon threads, return immediately with a job ID,
and let the agent poll or receive a callback when done.

Key insight: this is how Claude Code runs tests and builds in the background
while continuing to answer questions.

Architecture:
  run_background(command) → job_id (returns immediately)
  check_job(job_id)       → status + output so far
  wait_for_job(job_id)    → blocks until done, returns full output

TODO: Implement
  - JOBS: dict[str, dict] — in-memory job registry
  - run_background(): starts subprocess in a thread, registers job
  - check_job(): returns current status and captured output
  - Notification: when a job completes, append a notification to a queue
    that the agent checks on its next loop iteration
"""

# Key data structures:
#
# import threading, uuid
#
# JOBS: dict[str, dict] = {}
# # job schema: {"id": str, "command": str, "status": "running"|"done"|"error",
# #              "output": str, "thread": Thread}
#
# def run_background(command: str) -> str:
#     job_id = str(uuid.uuid4())[:8]
#     job = {"id": job_id, "command": command, "status": "running", "output": ""}
#     JOBS[job_id] = job
#
#     def _run():
#         result = subprocess.run(command, shell=True, capture_output=True, text=True)
#         job["output"] = (result.stdout + result.stderr)[:50_000]
#         job["status"] = "done" if result.returncode == 0 else "error"
#
#     thread = threading.Thread(target=_run, daemon=True)
#     thread.start()
#     job["thread"] = thread
#     return f"Job {job_id} started: {command!r}"
#
# def check_job(job_id: str) -> str:
#     job = JOBS.get(job_id)
#     if not job:
#         return f"Job {job_id} not found"
#     return f"[{job['status']}] {job['output'][-2000:] or '(running...)'}"

print("Session 08 — Background Operations (see docstring for implementation guide)")
