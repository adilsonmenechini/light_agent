# Memory System

Light Agent uses a three-tier memory architecture for optimal context management.

## Long-term Memory (Persistent)

Stores information that should persist across sessions:
- **Fixed Facts (MEMORY.md)**: Immutable user facts, preferences, tech stack
- **Interaction History (SQLite)**: Q&A pairs and tool observations with BM25 search

## Short-term Memory (Session-scoped)

Provides fast, in-memory context for the current session:

### Components
| Component | Purpose | Limit |
|-----------|---------|-------|
| **Message Window** | Recent conversation history | 10 messages |
| **Task States** | Intermediate state for complex tasks | Unlimited |
| **Observations** | Temporary tool insights | 20 observations |

### Key Features
- **Zero-latency access**: In-memory data structure
- **Automatic sync**: Messages sync with AgentLoop
- **Manual clear**: `/new` command clears all STM
- **Exportable**: Can export session data for debugging

### Usage
```python
from lightagent.agent.short_memory import ShortTermMemory

# Create with custom limits
stm = ShortTermMemory(max_messages=15, max_observations=30)

# Add message
stm.add_message("user", "Help me debug this issue")

# Get recent messages
recent = stm.get_recent_messages(count=5)

# Task state management
stm.set_task_state("task_123", "debug", {"step": 2, "error": "timeout"})

# Get task state
task = stm.get_task_state("task_123")

# Clear all
stm.clear_all()
```

---

## User Information

(Important facts about the user)

## Preferences

(User preferences learned over time)

## Project Context

(Information about ongoing projects)

## Important Notes

(Things to remember)

---

*This file is automatically updated by lightagent when important information should be remembered.*
