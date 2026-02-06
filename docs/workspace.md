# Workspace Structure (@workspace)

The `workspace/` directory is the central hub for all behavioral data, agents, and memories. Every file is in Markdown format for transparency and ease of editing.

## Directories

### `workspace/agents/`
Contains agent definitions. 
Example: `technician.md`
```markdown
---
name: Technician
description: Solves technical SRE problems
---
Your goal is to analyze logs and suggest fixes...
```

### `workspace/skills/`
Contains "Knowledge Items" or Skills. Each skill is a folder with a `SKILL.md`.
Generic skills adapted from `lightagent` include:
- `github/`: Interaction with `gh` CLI.
- `skill-creator/`: Guidelines for building new skills.
- `summarize/`: Text/URL summarization instructions.

Example: `workspace/skills/fetch_url/SKILL.md`
```markdown
---
name: fetch_url
description: Fetches content from a URL
requires:
  bins: [curl]
---
# Fetch URL Skill
Uses curl to download page content...
```

### `workspace/memory/`
- `memory/YYYY-MM-DD.json`: Daily logs of interactions in a structured format.
  - **Format**: JSON array `[...]` with one line per entry.
  - **Fields**: `timestamp`, `conversation_id`, `question`, `answer`, `summary`.
- `memory/MEMORY.md`: Long-term global context/facts distilled by the agent.

> [!NOTE]
> Detailed live conversation history is managed separately by the `SessionManager` in `~/.light_agent/sessions/` for LLM context purposes.

### `workspace/workflows/`
Markdown files describing complex multi-step processes or "Playbooks" that the agent can follow.
