# Memory Types

Agents need memory to be useful across more than one turn. There are four distinct types.

## 1. In-Context Memory (Short-Term)

The conversation history passed directly in the LLM prompt. Fast, zero setup, but limited by the context window and lost when the session ends.

```
messages = [
    {"role": "user",      "content": "My name is Alice."},
    {"role": "assistant", "content": "Hi Alice!"},
    {"role": "user",      "content": "What's my name?"},  # LLM can answer from context
]
```

**When to use:** Single-session conversations, task execution within one run.

## 2. External Memory (Long-Term)

Information stored outside the LLM and retrieved when needed. Enables memory that persists across sessions and scales beyond context limits.

Two flavors:
- **Key-value store** — Exact lookup by key (Redis, DynamoDB). Good for user preferences, session data.
- **Vector store** — Semantic similarity search (Chroma, Pinecone, pgvector). Good for unstructured knowledge.

```
# Store
memory_store.save("user:alice:preferences", {"language": "Python", "level": "expert"})

# Retrieve (semantic search)
relevant_docs = vector_store.search("what does alice know about Python?", k=3)
```

**When to use:** Persistent user profiles, knowledge bases, long-running agents.

## 3. Episodic Memory

A record of past agent runs — what the agent did, what worked, what failed. Enables agents to learn from experience and avoid repeating mistakes.

```
episodes = [
    {"task": "book flight", "actions": [...], "outcome": "success", "notes": "user prefers aisle seats"},
    {"task": "book flight", "actions": [...], "outcome": "failure", "notes": "price limit too low"},
]
```

**When to use:** Agents that run repeatedly on similar tasks, self-improving systems.

## 4. Procedural Memory (Learned Skills)

Knowledge encoded in the model weights or system prompt about *how* to do things. Updated via fine-tuning or prompt engineering, not at runtime.

**When to use:** When a behavior needs to be baked in permanently (e.g., always format responses as JSON).

## Summary

| Type        | Persistence | Capacity  | Speed  | Use Case                    |
|-------------|-------------|-----------|--------|-----------------------------|
| In-context  | Session     | ~200K tok | Fast   | Active conversation         |
| External KV | Permanent   | Unlimited | Medium | User profiles, session data |
| Vector store| Permanent   | Unlimited | Medium | Knowledge retrieval (RAG)   |
| Episodic    | Permanent   | Unlimited | Slow   | Learning from past runs     |
| Procedural  | Permanent   | Fixed     | Instant| Baked-in behaviors          |
