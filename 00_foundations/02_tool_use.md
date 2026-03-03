# Tool Use

Tools (also called "function calling") are how agents interact with the world beyond generating text.

## How It Works

Modern LLMs support **structured output** for tool calls. Instead of returning free text, the model returns a JSON object specifying which tool to call and with what arguments.

```
User:    "What's the weather in Paris?"

LLM:     { "tool": "get_weather", "arguments": { "city": "Paris" } }

App:     calls get_weather("Paris") → "65°F, overcast"

LLM:     "The weather in Paris is 65°F and overcast."
```

## Anatomy of a Tool

Tools have three components:

1. **Name** — What to call it (`get_weather`)
2. **Description** — When and why to use it (the LLM reads this to decide)
3. **Schema** — What arguments it accepts and their types

The **description** is the most important part. A bad description leads to a tool being called incorrectly or never at all.

## Tool Design Principles

- **Single responsibility** — Each tool does one thing well
- **Descriptive names** — `search_web`, not `tool_1`
- **Clear docstrings** — Tell the LLM exactly when to use it and what it returns
- **Return strings or structured dicts** — Easier for the LLM to parse than complex objects

## Tool Categories

| Category             | Examples                                    |
|----------------------|---------------------------------------------|
| Information retrieval | web search, document lookup, database query |
| Computation          | calculator, code execution, data analysis   |
| External actions     | send email, create GitHub issue, call API   |
| Memory               | save note, recall from memory               |
| Agent coordination   | call sub-agent, hand off to specialist      |

## Parallel Tool Calls

Modern LLMs can call multiple tools in a single turn when the calls are independent:

```
User:  "What's the weather in Paris and Tokyo?"
LLM:   [get_weather("Paris"), get_weather("Tokyo")]  ← parallel calls
```

This is more efficient than sequential calls and all four frameworks support it.
