# Computer Use Agents

Control a desktop GUI with Claude — from a simple native API loop to a
production-style two-stage Planner+Grounder architecture inspired by the
[OSWorld benchmark](https://github.com/xlang-ai/OSWorld).

## The Core Insight

Computer use is still just the tool-use loop. What's new: one tool result
is an image (screenshot), and actions are mouse/keyboard events instead of
bash commands or file reads.

```
# The same loop from 06_claude_code/01_basic_loop — unchanged:
while stop_reason == "tool_use":
    result = run_tool(tool_call)       # ← now this might return a screenshot
    messages.append(result)
    response = client.messages.create(...)
```

## Sessions

| # | Script | Architecture | Key addition |
|---|--------|-------------|--------------|
| 01 | `01_basic_loop/agent.py` | Single-stage (native beta) | Claude plans AND grounds; minimal code |
| 02 | `02_two_stage/agent.py` | Two-stage (Planner + Grounder) | Semantic planning separate from coordinate prediction; memory |

## OSWorld Architecture (what session 02 demonstrates)

```
Task + Memory
     ↓
[PLANNER]  — LLM reasons about what to do, no coordinates
"left_click", target: "the Save button in the toolbar"
     ↓
[GROUNDER] — Vision LLM maps semantic → pixels
→ (x=900, y=40) in physical screenshot coordinates
     ↓
[EXECUTOR] — pyautogui performs the action
     ↓
[SCREENSHOT] → new observation, back to Planner
```

OSWorld uses Qwen3-VL + UI-TARS as the grounder. Session 02 uses Claude
for both stages — the architecture and interface contract are identical,
making it easy to swap in a specialized vision model later.

## macOS Permissions (Required)

Both scripts require explicit macOS permission grants before they will work:

1. **Screen Recording** — `System Settings → Privacy & Security → Screen Recording → add Terminal`
   Without this, screenshots will be entirely black.

2. **Accessibility** — `System Settings → Privacy & Security → Accessibility → add Terminal`
   Without this, mouse clicks and keyboard events are silently ignored.

Grant these, then restart your terminal session.

## Setup

```bash
pip install -e ".[computer-use]"

# Copy .env.example → .env and add your ANTHROPIC_API_KEY
python 07_computer_use/01_basic_loop/agent.py
python 07_computer_use/02_two_stage/agent.py
```

## Safety

Both scripts use pyautogui's built-in failsafe: **move the mouse to the
top-left corner of the screen to immediately abort**. A `PAUSE = 0.5`
delay between actions gives you time to intervene.

Start with read-only tasks ("describe what's on screen") before trying
interactive ones.

## Demo Tasks to Try

```python
# Session 01 — native beta, Claude handles everything
"Take a screenshot and describe what you see"
"What time is it? Look at the menu bar clock."
"Open Spotlight search with cmd+space"

# Session 02 — two-stage, watch the Planner/Grounder logs
"Describe all visible applications on screen"
"Open a new Finder window using the Dock"
"Open Spotlight, type 'TextEdit', press Enter, then close it"
```

## Architecture Comparison

| | Session 01 (Native beta) | Session 02 (Two-stage) |
|---|---|---|
| Planning | Claude (implicit) | Explicit Planner LLM call |
| Grounding | Claude (implicit) | Explicit Grounder LLM call |
| Memory | None | `Memory` dataclass (task-relevant notes) |
| API calls/step | 1 | 2 (Planner + Grounder) |
| Debuggability | Low | High (logged separately) |
| Token cost | Lower | Higher |
| Swappable grounder | No | Yes |

## Retina Display Handling

On macOS Retina displays, pyautogui works in logical pixels (e.g., 1470×956)
but screenshots are in physical pixels (e.g., 2940×1912). Both scripts detect
this at startup via `get_scale_factor()` and divide Claude's coordinate output
by the scale factor before passing to pyautogui.
