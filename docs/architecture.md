# Architecture Overview - Light Agent

Light Agent is a lightweight, framework-agnostic agentic system designed for local execution, portability, and simplicity. It uses a file-based approach for configuration, skills, and memory.

## System Architecture

```mermaid
graph TD
    CLI[CLI Commands] --> AL[AgentLoop]
    AL --> Provider[LiteLLMProvider]
    AL --> ToolReg[ToolRegistry]
    AL --> Memory[MemoryStore]
    AL --> LongMemory[LongMemoryTool (SQLite)]
    
    ToolReg --> Skills[SkillsLoader]
    ToolReg --> MCP[MCP Clients]
    
    AL --> Session[SessionManager]
    
    Memory --> Markdown[workspace/memory/MEMORY.md]
    LongMemory --> DB[data/memory/long_memory.db]
    Session --> JSONL[~/.light_agent/sessions/*.jsonl]
    
    Provider --> LLM[External LLM Providers]
```

## Multi-Agent Logic
The system supports multiple agents defined as Markdown personas. A supervisor or a coordinator can orchestrate tasks between these agents using a simple event-driven loop.

## Core Flow
1. **Input**: User command via CLI.
2. **Context Assembly**: The system loads fixed facts (`MEMORY.md`), recent interaction history (SQLite), and available skills.
3. **Execution Loop**:
    - The LLM receives the context and decides which skill/tool to call.
    - The `SkillLoader` or native tools execute the task.
    - Results are appended to the context.
4. **Memory Update**: 
    - At the end of the run, the agent generates a concise summary of the interaction.
    - The question, answer, and summary are stored in the SQLite database (`long_memory.db`).

## Technology Stack
- **Manager**: `uv`.
- **LLM Interface**: `litellm`.
- **Tooling Protocols**: Model Context Protocol (MCP) for external integrations.
- **Configuration**: `pydantic-settings` to manage ENV-based tools and MCP servers.
- **Logic**: Async-first Python 3.12+.
