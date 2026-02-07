---
name: skill-creator
description: Create, structure, and package AgentSkills with scripts, references, and assets. Includes templates and best practices.
---

# Skill Creator

Guide for creating effective skills that integrate well with the agent system.

## Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required) - Unique skill identifier
│   │   └── description: (required) - Brief explanation
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code
    ├── references/       - Documentation
    └── assets/           - Templates, config files
```

## Skill Structure

### SKILL.md Template

```markdown
---
name: my-skill
description: Brief description of what this skill does.
---

# My Skill Name

One-paragraph overview of when to use this skill.

## When to Use

- Scenario 1 where this skill applies
- Scenario 2 where this skill applies

## Usage

\`\`\`bash
# Basic example
command arg1 arg2

# With options
command --option value
\`\`\`

## Options

| Flag | Description |
|------|-------------|
| `-n` | Option description |

## Examples

### Example 1
Description of what this example demonstrates.
\`\`\`bash
# Command and output
command example
\`\`\`

### Example 2
Another use case.
\`\`\`bash
command example2
\`\`\`

## Tips

- Practical tip 1
- Practical tip 2
```

## Best Practices

### Naming
- Use kebab-case: `github-api`, `docker-containers`
- Keep names under 30 characters
- Be descriptive but concise

### Description
- One sentence maximum
- Include the domain/tools involved
- Example: "Manage Docker containers with docker CLI"

### Content
- Keep SKILL.md body focused and essential
- Use imperative/infinitive form ("Create a PR" not "Creating a PR")
- Include concrete examples with expected outputs
- Use tables for options/flags
- Add tips section for common patterns

### Frontmatter
```yaml
---
name: my-skill
description: Short description ending with period.
# Optional metadata
metadata:
  domain: [infrastructure|development|debugging|devops]
  requires: [list of required binaries]
```

## Skill Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Domain** | Tool-specific knowledge | `github`, `docker`, `kubernetes` |
| **Workflow** | Multi-step processes | `task-management`, `code-review` |
| **Utility** | Common operations | `summarize`, `check_logs` |
| **Integration** | External service APIs | `aws-cli`, `gcloud` |

## Complete Example

### Directory Structure
```
my-docker-skill/
├── SKILL.md
├── scripts/
│   ├── inspect-container.sh
│   └── logs-tail.sh
└── references/
    └── docker-cheatsheet.md
```

### SKILL.md Content
```markdown
---
name: docker-util
description: Common Docker container management operations.
---

# Docker Utility Skill

Quick reference for Docker container lifecycle management.

## Container Operations

### Start/Stop
```bash
docker start <container>
docker stop <container>
docker restart <container>
```

### Inspect
```bash
docker inspect <container>
docker logs -f <container>
docker exec -it <container> sh
```

### Resource Management
```bash
docker stats <container>
docker top <container>
docker pause <container>
docker unpause <container>
```

## Tips

- Use `docker ps -a` to see all containers including stopped
- Use `--format` for custom output: `docker ps --format "{{.Names}}\t{{.Status}}"`
- Use volumes for persistent data
```

## Validation Checklist

Before publishing a skill:

- [ ] Name is unique and descriptive
- [ ] Description is clear and under 30 words
- [ ] Examples work with real commands
- [ ] No placeholder text remains
- [ ] Frontmatter is valid YAML
- [ ] Markdown syntax is correct
- [ ] Scripts are executable (`chmod +x`)
