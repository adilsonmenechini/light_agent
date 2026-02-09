# Status

Light Agent is **actively developed** with regular updates.

## Coming Soon

| Feature | Status | Description |
|---------|--------|-------------|
| MCP Server Templates | In Progress | Pre-configured MCP integrations |
| Telegram Integration | Planned | Chat-based interface via Telegram bot |
| Docker Support | ✅ Done | Containerized deployment |
| Sandbox Isolation | ✅ Done | Containerized execution for risky tools |

## Roadmap

| Feature | Category | Status | Description |
| :--- | :--- | :--- | :--- |
| **Short-term Memory** | Memory | ✅ Done | In-memory session context with message window, task states, and temporary observations. |
| **Long-term Memory** | Memory | ✅ Done | Persistent storage using SQLite + BM25 with time-based filtering (e.g., last 30d). |
| **Tool Observations** | Memory | ✅ Done | Auto-capture insights from tool executions as searchable observations. |
| **Vector Memory Search** | Memory | ✅ Done | Semantic similarity search using embeddings (complements BM25). |
| **Thinking Control** | Reasoning | ✅ Done | Configurable reasoning levels (OFF/LOW/MEDIUM/HIGH) for verbosity control. |
| **Session Compaction** | Context | ✅ Done | Automatic context optimization with Summarize, Prune, Merge, and Semantic strategies. |
| **Sandbox Isolation** | Security | ✅ Done | Containerized execution with configurable isolation levels (Process/Docker). |
| **Parallel Subagents** | Agents | ✅ Done | Enable multiple subagents to work concurrently on complex tasks. |
| **Multi-Model Orchestration** | LLM | ✅ Done | Use different models for reasoning (main loop) vs. speed (summaries). |
| **Interactive Chat Mode** | CLI | ✅ Done | Persistent chat session launched via `uv run lightagent chat`. |
| **Slash Commands** | CLI | ✅ Done | Support for commands like `/new`, `/reset`, and `/status` within the chat. |
| **Security Hardening** | Security | ✅ Done | Shell command allowlist, injection protection, workspace restriction. |
| **Human Approval Tool** | 12-Factor | ✅ Done | Pause execution for human approval before high-stakes operations. |
| **Control Flow Hooks** | 12-Factor | ✅ Done | Intercept agent execution at strategic points (before/after tool, LLM calls). |
| **Reducer Pattern** | 12-Factor | ✅ Done | Immutable state transitions for predictable, testable agent behavior. |
