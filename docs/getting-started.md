# Getting Started with Light Agent

A quick guide to get you up and running with Light Agent in minutes.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- An LLM API key (Ollama, OpenAI, Anthropic, Gemini, etc.)

## Installation

```bash
# Clone the repository
git clone https://github.com/adilsonmenechini/light-agent.git
cd light-agent

# Install dependencies
uv sync
```

## Quick Start

### Interactive Chat

Start an interactive chat session:

```bash
uv run lightagent chat
```

### Single Prompt

Run a single command:

```bash
uv run lightagent chat "List all Python files in this project"
```

### Verbose Mode

Get detailed logs for debugging:

```bash
uv run lightagent chat "Analyze the memory system" --verbose
```

## Your First Conversation

```
$ uv run lightagent chat
🤖 Light Agent v0.1.0 - Type /help for commands

You: /status
Agent: Connected tools: exec, read_file, write_file, web_search, web_fetch, spawn...
Available skills: github, summarize, task-management, code-search...

You: read_file the README and tell me what this project does
Agent: [Reads README.md]
This is Light Agent - a lightweight AI agent for local execution...

You: Search the web for latest AI agent trends
Agent: [Performs web search and summarizes findings]

You: /quit
```

## Configuration

Create a `.env` file based on `.env-examples`:

```env
# LLM Provider (choose one)
LITELLM_PROVIDER=ollama          # Local models
LITELLM_PROVIDER=openai          # OpenAI
LITELLM_PROVIDER=anthropic       # Anthropic
LITELLM_PROVIDER=google          # Google Gemini

# Model Configuration
REASONING_MODEL=gpt-4o           # Complex planning
FAST_MODEL=gpt-4o-mini           # Quick tasks

# Ollama (local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Security
RESTRICT_TO_WORKSPACE=true       # Keep agent in project directory
```

## Common Use Cases

### 1. Code Analysis

```bash
uv run lightagent chat "Find all async functions and explain their purpose"
```

### 2. Documentation Writing

```bash
uv run lightagent chat "Generate a README for the docs/ directory"
```

### 3. Git Operations

```bash
uv run lightagent chat "What changed since the last release?"
uv run lightagent chat "Create a PR description for the current branch"
```

### 4. Web Research

```bash
uv run lightagent chat "Find best practices for Python async programming"
```

### 5. Complex Tasks with Subagents

```bash
uv run lightagent chat "Analyze all Python files, check tests, and summarize code coverage"
```

## Slash Commands Reference

| Command | Description |
|---------|-------------|
| `/new` | Clear conversation and start fresh |
| `/status` | Show connected MCP servers and loaded skills |
| `/reset` | Restart tools and reconnect MCP servers |
| `/quit` or `/exit` | Close the session |

## Next Steps

- [Architecture Overview](architecture.md) - Understand the system design
- [Tools & MCP](tools_mcp.md) - Available tools reference
- [Workspace Structure](workspace.md) - How to customize behavior
- [Development Guide](development_guide.md) - Contributing guidelines

## Need Help?

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/adilsonmenechini/light-agent/issues)
- 💬 [Discussions](https://github.com/adilsonmenechini/light-agent/discussions)
