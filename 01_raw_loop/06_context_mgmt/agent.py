"""
Session 06 — Context Management
==================================
As conversations grow, the context window fills up and costs increase.
Solution: when messages exceed a threshold, summarize the oldest ones
into a single compact summary message.

Key insight: this is exactly what Claude Code does when it shows
"Auto-compacting context..." — it calls the LLM to summarize old turns.

Three-layer strategy:
  1. Keep:    the system prompt (always in context)
  2. Compress: old messages → one summary message
  3. Preserve: the last N messages verbatim (recent context)

TODO: Implement
  - count_tokens(messages) → estimate token usage
  - compress_old_messages(messages, keep_recent=10) → compressed messages:
      * Ask Claude to summarize the oldest messages
      * Replace them with: {"role": "user", "content": "[Summary]: ..."}
  - In agent_loop(): call compress when token count > threshold (e.g., 80k)
"""

# Key data structure:
#
# COMPRESS_THRESHOLD = 80_000  # tokens
# KEEP_RECENT = 10             # messages to keep verbatim
#
# def compress_old_messages(messages: list, keep_recent: int = KEEP_RECENT) -> list:
#     if len(messages) <= keep_recent:
#         return messages
#
#     to_compress = messages[:-keep_recent]
#     to_keep = messages[-keep_recent:]
#
#     summary_response = client.messages.create(
#         model="claude-haiku-4-5-20251001",  # cheap model for summarization
#         max_tokens=1024,
#         system="Summarize this conversation history concisely. Preserve key facts and decisions.",
#         messages=[{"role": "user", "content": str(to_compress)}],
#     )
#     summary = summary_response.content[0].text
#
#     return [{"role": "user", "content": f"[Conversation summary]: {summary}"}] + to_keep

print("Session 06 — Context Management (see docstring for implementation guide)")
