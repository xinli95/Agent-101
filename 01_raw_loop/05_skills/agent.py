"""
Session 05 — Skill Loading
============================
Skills are markdown files containing knowledge or instructions that are
loaded into the system prompt on demand.

Key insight: don't stuff everything into the system prompt upfront.
Load only what's needed for the current task. This is how Claude Code's
/memory and CLAUDE.md system works.

Architecture:
  skills/
    git.md       — how to use git in this project
    testing.md   — testing conventions
    deploy.md    — deployment runbook

  load_skill("git") → reads skills/git.md → injects into system prompt

TODO: Implement
  - skills/ directory with 2-3 example skill files
  - load_skill(name) tool: reads the file and returns its content
  - Dynamic system prompt: base prompt + loaded skills
  - The agent calls load_skill before tasks that need specific knowledge
"""

# Key data structures:
#
# LOADED_SKILLS: dict[str, str] = {}  # name → content
#
# def load_skill(name: str) -> str:
#     path = Path("skills") / f"{name}.md"
#     content = path.read_text()
#     LOADED_SKILLS[name] = content
#     return f"Loaded skill '{name}' ({len(content)} chars)"
#
# def get_system_prompt() -> str:
#     base = "You are a coding agent..."
#     if not LOADED_SKILLS:
#         return base
#     skills_text = "\n\n".join(f"## {k}\n{v}" for k, v in LOADED_SKILLS.items())
#     return f"{base}\n\n# Loaded Skills\n{skills_text}"
#
# The agent_loop() calls get_system_prompt() on each iteration
# so newly loaded skills are picked up immediately.

print("Session 05 — Skill Loading (see docstring for implementation guide)")
