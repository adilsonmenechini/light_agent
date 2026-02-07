# Workspace Structure

Light Agent uses a **dual-directory** approach for organizing behavioral data, agents, and memories.

## Directory Priority

| Priority | Location | Purpose |
|----------|----------|---------|
| **1 (Default)** | `light_agent/base/` | Base configuration, skills, and shared resources |
| **2 (Optional)** | `workspace/` | User-specific overrides and daily use examples |

The agent first looks in `light_agent/base/`. If a file/directory doesn't exist there, it falls back to `workspace/`.

---

## `light_agent/base/` (Base Configuration)

Contains the default configuration and skills bundled with the agent.

### `light_agent/base/agents/`
Agent definitions for Claude Desktop or compatible CLI.
- `AGENTS.md`: Default agent instructions
- `HEARTBEAT.md`: Periodic task management

Example agent definition:
```markdown
---
name: Task Assistant
description: Helps with everyday tasks and questions
---
Your goal is to assist users with their daily tasks...
```

### `light_agent/base/skills/`
Knowledge Items (Skills). Each skill is a folder with a `SKILL.md`.

Bundled skills:
- `github/`: GitHub CLI (`gh`) interactions
- `skill-creator/`: Guidelines for creating new skills
- `summarize/`: Text/URL summarization
- `task-management/`: Complex task workflows
- `tmux/`: TMUX session management
- `code-search/`: Production code patterns from open source repos

### `light_agent/base/memory/`
- `MEMORY.md`: **Fixed Facts**. Long-term global context distilled by the agent. Always injected into context.

### `light_agent/base/workflows/`
Markdown files describing complex multi-step processes or "Playbooks".

---

## `workspace/` (User Overrides - Optional)

The `workspace/` directory is **optional** and serves as an override layer. Use it for:

- Daily experiments and testing
- User-specific skills/agents that differ from defaults
- Temporary configurations

### Creating a Workspace

If you want to override base configurations, create the directory structure:

```bash
mkdir -p workspace/skills
mkdir -p workspace/memory
mkdir -p workspace/agents
mkdir -p workspace/workflows
```

### Example Structure

```
workspace/                    # Optional override layer
├── agents/
│   └── custom_agent.md       # Overrides light_agent/base/agents/
├── skills/
│   └── my_custom_skill/      # Adds to (not overrides) base skills
├── memory/
│   └── MEMORY.md            # Merged with base memory
└── workflows/
    └── my_playbook.md       # Adds to base workflows
```

### Important Notes

- Files in `workspace/` **add to** or **override** base files
- Skills from both directories are loaded and available
- Memory files are merged
- Use `workspace/` for things you want to keep separate from the base agent

---

## File Locations

| Feature | Default Path | Override Path |
|---------|--------------|---------------|
| Skills | `light_agent/base/skills/` | `workspace/skills/` |
| Memory | `light_agent/base/memory/` | `workspace/memory/` |
| Agents | `light_agent/base/agents/` | `workspace/agents/` |
| Workflows | `light_agent/base/workflows/` | `workspace/workflows/` |
| MCP Config | `light_agent/base/servers_config.json` | `workspace/servers_config.json` |

---

## Best Practices

1. **Keep base clean**: Modify `light_agent/base/` for permanent changes
2. **Use workspace for testing**: Experiment in `workspace/` first
3. **Document your skills**: Every skill should have a `SKILL.md` with metadata
4. **Back up base**: Before modifying `light_agent/base/`, ensure you have backups
