"""
Session 01 — Native Computer Use
==================================
The same tool-use loop you know — but the tool is your screen.

Anthropic's computer use beta exposes a built-in tool type "computer" that
lets Claude request screenshots and send mouse/keyboard actions. Your job:
take the screenshot it requests, execute the actions it sends.

Architecture:
    Screenshot → Claude (plans AND grounds) → pyautogui (executes) → repeat

Key insight: this is still just:
    while stop_reason == "tool_use":
        result = run_tool(tool_call)
        messages.append(result)
        response = client.messages.create(...)

The only new thing: one tool result is an image, not text.

macOS permissions required BEFORE running:
    System Settings → Privacy & Security → Screen Recording → add Terminal
    System Settings → Privacy & Security → Accessibility → add Terminal

Run:
    python 07_computer_use/01_basic_loop/agent.py
"""

import base64
import io
import time

import anthropic
import pyautogui
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

client = anthropic.Anthropic()

COMPUTER_USE_BETA = "computer-use-2025-01-24"
COMPUTER_TOOL_TYPE = "computer_20250124"

# Safety: pause between actions + move mouse to top-left corner to abort
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True


# ─── Utilities ───────────────────────────────────────────────────────────────


def get_scale_factor() -> float:
    """
    Detect Retina display scaling (physical pixels / logical pixels).
    On macOS Retina: returns 2.0. On standard displays: returns 1.0.

    pyautogui works in logical pixels; screenshots are in physical pixels.
    Coordinates from Claude (which sees the physical screenshot) must be
    divided by this factor before passing to pyautogui.
    """
    screenshot = pyautogui.screenshot()
    logical_w, _ = pyautogui.size()
    return screenshot.width / logical_w


def check_permissions() -> bool:
    """
    Verify Screen Recording permission is granted by checking if the
    screenshot contains non-black pixels. Returns False and prints help
    if the screen appears black (permission not granted).
    """
    screenshot = pyautogui.screenshot()
    pixels = list(screenshot.getdata())[:200]
    if all(max(p[:3]) < 10 for p in pixels):
        print("ERROR: Screen appears black — Screen Recording permission not granted.")
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


# ─── Action executor ─────────────────────────────────────────────────────────


def execute_action(action: str, scale: float, **kwargs) -> str:
    """
    Execute a mouse/keyboard action from Claude's computer tool call.
    Returns a human-readable summary of what was done.

    Claude sends coordinates in physical pixels (screenshot space).
    We divide by scale to get logical pixels for pyautogui.

    Claude's action types:
        left_click, right_click, double_click, middle_click — coordinate
        mouse_move — coordinate
        type — text
        key — key combo string ("Return", "cmd+s", etc.)
        scroll — coordinate + direction + amount
        screenshot — handled in the loop, not here
    """
    def logical(coord: list[int]) -> tuple[int, int]:
        return int(coord[0] / scale), int(coord[1] / scale)

    if action == "left_click":
        x, y = logical(kwargs["coordinate"])
        pyautogui.click(x, y)
        return f"Left-clicked ({x}, {y})"

    elif action == "right_click":
        x, y = logical(kwargs["coordinate"])
        pyautogui.rightClick(x, y)
        return f"Right-clicked ({x}, {y})"

    elif action == "double_click":
        x, y = logical(kwargs["coordinate"])
        pyautogui.doubleClick(x, y)
        return f"Double-clicked ({x}, {y})"

    elif action == "middle_click":
        x, y = logical(kwargs["coordinate"])
        pyautogui.middleClick(x, y)
        return f"Middle-clicked ({x}, {y})"

    elif action == "mouse_move":
        x, y = logical(kwargs["coordinate"])
        pyautogui.moveTo(x, y, duration=0.3)
        return f"Moved to ({x}, {y})"

    elif action == "type":
        text = kwargs["text"]
        # pyautogui.typewrite doesn't handle Unicode — use write() with interval
        pyautogui.write(text, interval=0.04)
        return f"Typed: {text!r}"

    elif action == "key":
        key = kwargs["text"]
        if "+" in key:
            pyautogui.hotkey(*key.split("+"))
        else:
            pyautogui.press(key)
        return f"Key: {key}"

    elif action == "scroll":
        x, y = logical(kwargs["coordinate"])
        direction = kwargs.get("direction", "down")
        amount = int(kwargs.get("amount", 3))
        clicks = -amount if direction == "down" else amount
        pyautogui.scroll(clicks, x=x, y=y)
        return f"Scrolled {direction} {amount}x at ({x}, {y})"

    else:
        return f"Unknown action: {action} (skipped)"


# ─── Agent loop ──────────────────────────────────────────────────────────────


def agent_loop(task: str, scale: float) -> str:
    """
    Run the native computer use agent loop until the task is complete.

    Structural difference from 06_claude_code sessions:
    - Tool type is "computer_20250124" (a built-in beta type, no input_schema)
    - API call uses client.beta.messages.create with betas=[COMPUTER_USE_BETA]
    - Tool results include image content blocks (screenshots) not just text
    - Claude controls both planning AND grounding (decides its own coordinates)
    """
    width, height = pyautogui.size()
    # Tell Claude the display size so it generates valid coordinates
    physical_w, physical_h = int(width * scale), int(height * scale)

    tools = [{
        "type": COMPUTER_TOOL_TYPE,
        "name": "computer",
        "display_width_px": physical_w,
        "display_height_px": physical_h,
        "display_number": 1,
    }]

    system = (
        "You are a computer use agent controlling a macOS desktop. "
        "Complete the given task by taking screenshots to observe the screen "
        "and using mouse/keyboard actions to interact with UI elements. "
        "When the task is fully complete, respond with plain text describing "
        "what you accomplished — do not request another tool call."
    )

    # Start with an initial screenshot so Claude sees the current state
    initial_screenshot = take_screenshot()
    messages = [{
        "role": "user",
        "content": [
            image_block(initial_screenshot),
            {"type": "text", "text": task},
        ],
    }]

    step = 0
    while True:
        step += 1
        print(f"\n  [step {step}] Calling Claude...")

        response = client.beta.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tools,
            betas=[COMPUTER_USE_BETA],
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Claude is done — return the final text response
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "Task complete."

        # Execute all tool calls and collect results for the next round
        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "computer":
                action = block.input.get("action", "")
                print(f"  [computer] {action}", end="")
                if "coordinate" in block.input:
                    coord = block.input["coordinate"]
                    logical_x, logical_y = int(coord[0] / scale), int(coord[1] / scale)
                    print(f" → logical ({logical_x}, {logical_y})", end="")
                print()

                if action == "screenshot":
                    # Claude explicitly requested a screenshot
                    result_content = [image_block(take_screenshot())]
                else:
                    # Execute the action, then capture the resulting screen state
                    summary = execute_action(action, scale, **block.input)
                    time.sleep(0.3)  # let the UI settle before screenshotting
                    result_content = [
                        {"type": "text", "text": summary},
                        image_block(take_screenshot()),
                    ]

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                })

        messages.append({"role": "user", "content": tool_results})


# ─── Entry point ─────────────────────────────────────────────────────────────


def main():
    print("Computer Use Agent — Session 01 (native Anthropic beta)")
    print("Claude plans AND grounds: it sees the screen and decides its own coordinates.")
    print("WARNING: This agent controls your mouse and keyboard.")
    print("Safety: move mouse to top-left corner to abort at any time.\n")

    if not check_permissions():
        return

    scale = get_scale_factor()
    print(f"Display scale factor: {scale}x ({'Retina' if scale > 1 else 'standard'})\n")

    # Start with a safe read-only demo
    demo_task = "Take a screenshot and describe what you see on the screen in detail."
    print(f"Demo task: {demo_task}")
    result = agent_loop(demo_task, scale)
    print(f"\nAgent: {result}\n")

    print("─" * 60)
    print("Interactive mode. Type 'exit' to quit.\n")
    while True:
        user_input = input("Task: ").strip()
        if user_input.lower() in ("exit", "quit", "q") or not user_input:
            break
        print()
        result = agent_loop(user_input, scale)
        print(f"\nAgent: {result}\n")


if __name__ == "__main__":
    main()
