# What is an Agent?

## The Core Idea

A **language model** takes text in and produces text out — it's stateless and reactive.

An **agent** is a language model that can take *actions*, observe results, and repeat until it achieves a goal. The key difference: **a loop**.

```
while not done:
    thought = llm.think(goal + history)
    action  = llm.decide(thought)
    result  = environment.run(action)
    history.append(result)
```

## The Agent Loop

```
┌──────────────────────────────────┐
│                                  │
│   Perceive → Think → Act         │
│       ↑               │          │
│       └───────────────┘          │
│                                  │
└──────────────────────────────────┘
```

1. **Perceive** — Read the current state (goal, history, tool results)
2. **Think** — The LLM reasons about what to do next
3. **Act** — Call a tool, respond to the user, or stop

## Agent vs. Chatbot

|                | Chatbot         | Agent                        |
|----------------|-----------------|------------------------------|
| Loop           | Single turn     | Multi-turn until goal is met |
| Actions        | Text only       | Tools, APIs, code execution  |
| State          | Stateless       | Maintains state              |
| Goal           | Answer question | Achieve objective            |

## Minimal Requirements for an Agent

1. **Tools** — The LLM can call external functions
2. **Decision-making** — The LLM decides *when* and *which* tool to call
3. **Loop** — The process repeats until the goal is reached

Everything else (memory, planning, multi-agent coordination) builds on this foundation.
