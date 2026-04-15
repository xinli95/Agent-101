"""
Session 02 — Two-Stage: Planner + Grounder
============================================
Production computer use agents decouple semantic planning from pixel-level
grounding. Here's why this matters:

  Single-stage (session 01):
    Claude sees screen → Claude decides action AND coordinates
    Hard to debug: did it misunderstand the task, or mislocate the button?

  Two-stage (this session):
    Planner: Claude + screenshot → "click the Save button"  (no coords)
    Grounder: Claude vision + screenshot + "Save button" → (x=450, y=320)
    Executor: pyautogui.click(225, 160)  (after Retina scale correction)

  Benefits:
    - Each stage has exactly one job → easy to debug and swap independently
    - Planner output is human-readable for logging/audit
    - Grounder can be replaced with a specialized vision model (e.g., Qwen3-VL
      as used in OSWorld) without changing the planner
    - Memory system tracks task-relevant facts without logging noise

Architecture (inspired by OSWorld/UiPath benchmark agent):
    Task + Memory
         ↓
    [PLANNER]  — LLM, semantic reasoning, no coordinates
    "left_click", target: "the blue Save button in the toolbar"
         ↓
    [GROUNDER] — Vision LLM, coordinate prediction
    → (x=900, y=40) in physical pixels
         ↓
    [EXECUTOR] — pyautogui, logical pixels (physical / scale_factor)
         ↓
    [SCREENSHOT] → new observation for next Planner call

OSWorld uses Qwen3-VL + UI-TARS as the grounder. We use Claude vision
for both stages — the architecture and interface contract are identical.

macOS permissions required BEFORE running:
    System Settings → Privacy & Security → Screen Recording → add Terminal
    System Settings → Privacy & Security → Accessibility → add Terminal

Run:

"""

import base64
import io
import json
import time
from dataclasses import dataclass, field
from typing import Literal

import anthropic
import pyautogui
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

MAX_STEPS = 20           # safety: stop after this many iterations
SCREENSHOT_HISTORY = 2   # only last N screenshots in planner context (token efficiency)

# Semantic action vocabulary — mirrors OSWorld's action set (simplified to 8)
ActionType = Literal[
    "left_click", "right_click", "double_click",
    "type", "key", "scroll", "mouse_move", "finish"
]
SPATIAL_ACTIONS = {"left_click", "right_click", "double_click", "mouse_move", "scroll"}


# ─── Data structures ─────────────────────────────────────────────────────────


@dataclass
class Memory:
    """
    Task-relevant facts the agent accumulates across steps.

    OSWorld's memory stores semantic information (e.g., "the Save button is
    in the top toolbar") not mechanical details (scrolled, hovered, focused).
    This keeps the planner context useful without growing unboundedly.
    """
    task_notes: list[str] = field(default_factory=list)

    def add(self, note: str) -> None:
        self.task_notes.append(note)

    def as_text(self) -> str:
        if not self.task_notes:
            return "No notes yet."
        return "\n".join(f"- {note}" for note in self.task_notes)


@dataclass
class PlannerOutput:
    """
    The Planner's structured decision for one step.

    action + args describe WHAT to do semantically — no pixel coordinates.
    For spatial actions, args["target"] is a natural-language description
    of the UI element (e.g., "the blue Save button in the top toolbar").
    The Grounder translates this description into (x, y) coordinates.
    """
    review: str               # What I observe on the current screen
    thought: str              # Why I'm taking this action
    action: ActionType
    args: dict                # Semantic args — no coordinates
    memory_update: str | None # New fact to remember, or None


# ─── Utilities ───────────────────────────────────────────────────────────────


def get_scale_factor() -> float:
    """
    Detect Retina display scaling (physical pixels / logical pixels).
    pyautogui uses logical pixels; screenshots and Claude coordinates are physical.
    """
    screenshot = pyautogui.screenshot()
    logical_w, _ = pyautogui.size()
    return screenshot.width / logical_w


def check_permissions() -> bool:
    """Verify Screen Recording permission by checking for non-black pixels."""
    screenshot = pyautogui.screenshot()
    pixels = list(screenshot.getdata())[:200]
    if all(max(p[:3]) < 10 for p in pixels):
        print("ERROR: Screen is black — Screen Recording permission not granted.")
        print("  System Settings → Privacy & Security → Screen Recording → add Terminal")
        return False
    return True


def take_screenshot() -> str:
    """Capture the full screen and return as base64-encoded PNG string."""
    screenshot = pyautogui.screenshot()
    buffer = io.BytesIO()
    screenshot.save(buffer, format="PNG")
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def image_block(b64_data: str) -> dict:
    """Build an Anthropic image content block from base64 PNG data."""
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": b64_data},
    }


def parse_json_response(text: str) -> dict:
    """
    Parse JSON from Claude's response, handling markdown code fences.
    Claude sometimes wraps JSON in ```json ... ``` blocks.
    """
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        # parts[1] is the content inside the fences
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


# ─── Stage 1: Planner ────────────────────────────────────────────────────────


PLANNER_SYSTEM = """You are a computer use planning agent on macOS.

Decide the NEXT SINGLE ACTION to take toward completing the task.
You do NOT predict pixel coordinates — describe what to interact with in plain language.
The Grounder will translate your description into screen coordinates.

Respond ONLY with valid JSON in this exact format:
{
  "review": "What I observe on the current screen (1-2 sentences)",
  "thought": "Why I'm taking this action (1 sentence)",
  "action": "one of: left_click | right_click | double_click | type | key | scroll | mouse_move | finish",
  "args": {
    "For left_click/right_click/double_click/mouse_move": {"target": "plain English description of the UI element"},
    "For scroll": {"target": "plain English description of the area to scroll", "direction": "up or down", "amount": 3},
    "For type": {"text": "exact text to type"},
    "For key": {"key": "Return or cmd+s or ctrl+c etc."},
    "For finish": {"result": "what was accomplished"}
  },
  "memory_update": "A useful fact to remember for this task, or null"
}

Use "finish" only when the task is fully and verifiably complete."""


def plan_next_action(
    task: str,
    memory: Memory,
    screenshot_history: list[str],
) -> PlannerOutput:
    """
    Call the Planner: Claude + screenshots + task + memory → semantic action.

    Only the last SCREENSHOT_HISTORY screenshots are included to limit token
    usage — this mirrors OSWorld's design choice of a 2-screenshot window.
    """
    recent = screenshot_history[-SCREENSHOT_HISTORY:]

    # Build content: screenshots first (visual context), then task and memory
    content: list[dict] = []
    for i, screenshot_b64 in enumerate(recent):
        label = "Previous screen:" if i < len(recent) - 1 else "Current screen:"
        content.append({"type": "text", "text": label})
        content.append(image_block(screenshot_b64))

    content.append({
        "type": "text",
        "text": (
            f"Task: {task}\n\n"
            f"Task memory (accumulated notes):\n{memory.as_text()}\n\n"
            "What is the next single action to take? Respond with JSON."
        ),
    })

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=PLANNER_SYSTEM,
        messages=[{"role": "user", "content": content}],
    )

    data = parse_json_response(response.content[0].text)
    return PlannerOutput(
        review=data["review"],
        thought=data["thought"],
        action=data["action"],
        args=data["args"],
        memory_update=data.get("memory_update"),
    )


# ─── Stage 2: Grounder ───────────────────────────────────────────────────────


GROUNDER_SYSTEM = """You are a visual grounding agent for macOS screenshots.

Given a screenshot and a plain-English description of a UI element, return
the PIXEL COORDINATES of that element's center point.

Respond ONLY with valid JSON:
{
  "x": 450,
  "y": 320,
  "confidence": "high" | "medium" | "low",
  "reasoning": "brief explanation of why you chose these coordinates"
}

Be precise — the coordinates will be used directly for mouse clicks.
If you cannot locate the element with reasonable confidence, set confidence to "low"."""


def ground_target(
    screenshot_b64: str,
    target_description: str,
) -> tuple[int, int] | None:
    """
    Call the Grounder: Claude vision + screenshot + description → (x, y).

    Returns physical pixel coordinates (screenshot space), or None if the
    grounder has low confidence or fails to parse. The caller applies the
    Retina scale factor before passing coordinates to pyautogui.

    In OSWorld, this stage uses Qwen3-VL + UI-TARS. Using Claude here keeps
    this example self-contained while demonstrating the same interface contract.
    """
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=GROUNDER_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                image_block(screenshot_b64),
                {
                    "type": "text",
                    "text": (
                        f"Find this UI element and return its center coordinates:\n"
                        f"{target_description}"
                    ),
                },
            ],
        }],
    )

    try:
        data = parse_json_response(response.content[0].text)
        if data.get("confidence") == "low":
            print(f"    [grounder] Low confidence for: {target_description!r}")
            print(f"    [grounder] Reasoning: {data.get('reasoning', '')}")
            return None
        x, y = int(data["x"]), int(data["y"])
        print(f"    [grounder] → ({x}, {y}) [{data.get('confidence', '?')} confidence]")
        return x, y
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"    [grounder] Parse error: {e}")
        return None


# ─── Stage 3: Executor ───────────────────────────────────────────────────────


def execute_action(plan: PlannerOutput, coords: tuple[int, int] | None, scale: float) -> str:
    """
    Execute the planned action via pyautogui.

    coords are in physical pixels (from the Grounder / screenshot space).
    We divide by scale to get logical pixels for pyautogui on Retina displays.
    Non-spatial actions (type, key, finish) ignore coords.
    """
    action = plan.action
    args = plan.args

    def logical(xy: tuple[int, int]) -> tuple[int, int]:
        return int(xy[0] / scale), int(xy[1] / scale)

    if action in ("left_click", "right_click", "double_click", "mouse_move"):
        if coords is None:
            return f"Error: no coordinates for {action}"
        x, y = logical(coords)
        if action == "left_click":
            pyautogui.click(x, y)
            return f"Left-clicked ({x}, {y})"
        elif action == "right_click":
            pyautogui.rightClick(x, y)
            return f"Right-clicked ({x}, {y})"
        elif action == "double_click":
            pyautogui.doubleClick(x, y)
            return f"Double-clicked ({x}, {y})"
        elif action == "mouse_move":
            pyautogui.moveTo(x, y, duration=0.3)
            return f"Moved to ({x}, {y})"

    elif action == "scroll":
        if coords is None:
            return "Error: no coordinates for scroll"
        x, y = logical(coords)
        direction = args.get("direction", "down")
        amount = int(args.get("amount", 3))
        clicks = -amount if direction == "down" else amount
        pyautogui.scroll(clicks, x=x, y=y)
        return f"Scrolled {direction} {amount}x at ({x}, {y})"

    elif action == "type":
        text = args["text"]
        pyautogui.write(text, interval=0.04)
        return f"Typed: {text!r}"

    elif action == "key":
        key = args["key"]
        if "+" in key:
            pyautogui.hotkey(*key.split("+"))
        else:
            pyautogui.press(key)
        return f"Key: {key}"

    elif action == "finish":
        return f"DONE: {args.get('result', 'Task complete')}"

    return f"Unknown action: {action} (skipped)"


# ─── Main loop ───────────────────────────────────────────────────────────────


def run_task(task: str, scale: float) -> str:
    """
    Full two-stage computer use loop for a single task.

    Each iteration:
      1. Take screenshot, append to history
      2. Planner: screenshots + task + memory → semantic action (no coords)
      3. Grounder (spatial actions only): screenshot + target → (x, y)
      4. Executor: pyautogui performs the action (with Retina correction)
      5. Update memory if the planner noted something
      6. Repeat until "finish" or MAX_STEPS
    """
    memory = Memory()
    screenshot_history: list[str] = []

    print(f"\nTask: {task}")
    print(f"Memory: {memory.as_text()}\n")

    for step in range(1, MAX_STEPS + 1):
        # 1. Screenshot
        screenshot_b64 = take_screenshot()
        screenshot_history.append(screenshot_b64)
        # Trim history to avoid unbounded growth between the windowed context
        if len(screenshot_history) > SCREENSHOT_HISTORY + 2:
            screenshot_history = screenshot_history[-(SCREENSHOT_HISTORY + 2):]

        # 2. Planner
        print(f"[step {step}] Planning...")
        plan = plan_next_action(task, memory, screenshot_history)
        print(f"  review:  {plan.review}")
        print(f"  thought: {plan.thought}")
        print(f"  action:  {plan.action} {plan.args}")

        # Update memory before acting (so grounder failures can be noted)
        if plan.memory_update:
            memory.add(plan.memory_update)
            print(f"  memory:  + {plan.memory_update!r}")

        # 3. Finish check
        if plan.action == "finish":
            result = plan.args.get("result", "Task complete")
            print(f"\n[done] {result}")
            return result

        # 4. Grounder — only for spatial actions that need coordinates
        coords: tuple[int, int] | None = None
        if plan.action in SPATIAL_ACTIONS:
            target = plan.args.get("target", "")
            print(f"  [grounder] Locating: {target!r}")
            coords = ground_target(screenshot_b64, target)
            if coords is None:
                # Grounding failed — remember this and retry with different description
                memory.add(
                    f"Grounding failed for target: {target!r}. "
                    "Try a more specific description next time."
                )
                print(f"  [grounder] Failed — skipping step, added note to memory")
                continue

        # 5. Executor
        summary = execute_action(plan, coords, scale)
        print(f"  [executor] {summary}")
        time.sleep(0.5)  # let the UI settle before the next screenshot

    return f"Stopped after {MAX_STEPS} steps without completing the task."


# ─── Entry point ─────────────────────────────────────────────────────────────


def main():
    print("Two-Stage Computer Use Agent — Session 02 (Planner + Grounder)")
    print("Architecture: Planner (semantic) → Grounder (pixel) → Executor (pyautogui)")
    print("Inspired by: OSWorld/UiPath benchmark (https://github.com/xlang-ai/OSWorld)")
    print("WARNING: This agent controls your mouse and keyboard.")
    print("Safety: move mouse to top-left corner to abort at any time.\n")

    if not check_permissions():
        return

    scale = get_scale_factor()
    print(f"Display scale factor: {scale}x ({'Retina' if scale > 1 else 'standard'})\n")

    # Start with a safe read-only demo to verify the two-stage pipeline
    demo_task = "Describe what applications and windows are currently visible on the screen."
    print(f"Demo task: {demo_task}")
    result = run_task(demo_task, scale)
    print(f"\nResult: {result}\n")

    print("─" * 60)
    print("Interactive mode. Type 'exit' to quit.\n")
    while True:
        user_input = input("Task: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        result = run_task(user_input, scale)
        print(f"\nResult: {result}\n")


if __name__ == "__main__":
    main()
