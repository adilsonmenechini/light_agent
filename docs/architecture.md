# Architecture Overview - Light Agent

Light Agent is a lightweight, framework-agnostic agentic system designed for local execution, portability, and everyday tasks. It uses a file-based approach for configuration, skills, and memory.

## System Architecture

```mermaid
graph TD
    CLI[CLI Commands] --> AL[AgentLoop]
    AL --> Provider[LiteLLMProvider]
    AL --> ToolReg[ToolRegistry]
    AL --> Memory[MemoryStore]
    AL --> LongMemory[LongMemoryTool (SQLite)]
    AL --> Subagent[SubagentManager]
    
    ToolReg --> Skills[SkillsLoader]
    ToolReg --> MCP[MCP Clients]
    
    AL --> Session[SessionManager]
    AL -.-> |auto-capture insights| LongMemory
    
    Memory --> Markdown[workspace/memory/MEMORY.md]
    LongMemory --> DB[data/memory/long_memory.db]
    LongMemory --> |qa + observations| DB
    Session --> JSONL[~/.light_agent/sessions/*.jsonl]
    
    Provider --> LLM[External LLM Providers]
```

## Multi-Agent & Multi-Model Orchestration
The system supports spawning background subagents. These are isolated agent instances that share the same provider but have a focused system prompt and localized tools. 

Concurrent execution is supported via `SubagentManager`, allowing the main agent to delegate multiple tasks in parallel and coordinate their results.

The system also orchestrates multiple models for efficiency:
- **Reasoning Loop**: Uses the `REASONING_MODEL` for complex planning and tool use.
- **Utility Tasks**: Uses the `FAST_MODEL` for lighter tasks such as interaction summarization, ensuring low latency and reduced cost/resource usage.

## Core Flow
1. **Input**: User command via CLI.
2. **Context Assembly**: The system loads fixed facts (`MEMORY.md`), recent interaction history (SQLite), and available skills.
3. **Execution Loop**:
    - The LLM receives the context and decides which skill/tool to call.
    - The `SkillLoader` or native tools execute the task.
    - Results are appended to the context.
4. **Memory Update**:
    - **Q&A Summary**: The agent generates a concise summary of the interaction.
    - **Tool Observations**: Insights from tool executions are automatically extracted and stored (read_file discoveries, command outputs, grep results, etc.).
    - All data is stored in the SQLite database (`long_memory.db`) with type标记 (`qa` or `observation`).

## Memory System

### Long-term Memory (SQLite)
- Stores all interactions and tool observations in `data/memory/long_memory.db`
- Uses BM25 for semantic search with time-based filtering (e.g., last 30 days)
- Entry types: `qa` (question/answer) and `observation` (tool discoveries)

### Tool Observations
Inspired by Claude-Mem's progressive disclosure pattern, the agent automatically captures insights from tool executions:

| Tool | Observation Captured |
|------|---------------------|
| `read_file` | "Lido arquivo: descobriu que..." |
| `write_file` | "Criou/editou arquivo..." |
| `exec` | "Executou comando que retornou..." |
| `grep` | "Busca encontrou X resultados" |
| `glob` | "Encontrou X arquivos..." |
| `web_search` | "Pesquisa web retornou X resultados" |
| `web_fetch` | "Conteúdo web extraído..." |

Observations are only stored if:
- Result is not empty or an error
- Result has at least 20 characters
- Results are truncated to 2000 characters

This enables the agent to remember discoveries from past sessions (e.g., "onde foi que encontramos a config do banco?").

Light Agent includes multiple security layers to prevent malicious use:

### Shell Command Safety
- **Command Allowlist**: Only 60+ pre-approved commands can be executed (git, ls, cat, grep, docker, etc.)
- **Shell Metacharacter Detection**: Blocks dangerous characters (`;|&$<>`{}[]\\*?\n\r)
- **Dangerous Pattern Blocking**: Prevents destructive commands like `rm -rf`, fork bombs, disk writes
- **Subprocess Isolation**: Uses `create_subprocess_exec()` instead of `shell=True`

### SSRF Protection (Web Tools)
- **Private IP Blocking**: Blocks RFC 1918 addresses (10.x, 172.16.x, 192.168.x)
- **Loopback/Link-local Blocking**: Blocks 127.x, 169.254.x, ::1
- **Cloud Metadata Protection**: Blocks AWS/GCP/Azure metadata endpoints

### Workspace Restriction
- **RESTRICT_TO_WORKSPACE**: When enabled (default), all file operations are confined to the workspace directory
- **Path Traversal Prevention**: Detects and blocks `../` attacks

## Configuration

Security settings can be configured via `.env`:

```env
# Security
RESTRICT_TO_WORKSPACE=true  # Default: true
```

## Technology Stack
- **Manager**: `uv`.
- **LLM Interface**: `litellm`.
- **Tooling Protocols**: Model Context Protocol (MCP) for external integrations.
- **Configuration**: `pydantic-settings` to manage ENV-based tools and MCP servers.
- **Logic**: Async-first Python 3.12+.
