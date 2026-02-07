# Development Guide

Guide for contributing new features to Light Agent without frameworks.

## Feature Development Workflow

### 1. Create Feature Branch

```bash
# Always create a new branch for any feature
git checkout -b feature/my-new-feature

# Or for bugfixes
git checkout -b bugfix/issue-description

# Or for documentation
git checkout -b docs/update-section
```

### 2. Follow Python Best Practices

#### Code Style
- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Linting**: Ruff with rules E, F, I, N, W
- **Type checking**: Pyright

```bash
# Run linter
uv run ruff check light_agent/

# Run type checker
uv run pyright light_agent/
```

#### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | `snake_case` | `thread_store.py` |
| Classes | `PascalCase` | `ThreadStore` |
| Functions | `snake_case` | `load_thread()` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES` |
| Variables | `snake_case` | `thread_id` |

#### Imports Order

```python
# Standard library
import json
from datetime import datetime
from typing import Any, Dict, Optional

# Third party
from pydantic import BaseModel

# Local
from light_agent.agent.base import Tool
```

### 3. File Structure for New Features

```
light_agent/agent/
├── my_feature/
│   ├── __init__.py
│   ├── models.py          # Pydantic models, dataclasses
│   ├── core.py            # Main logic
│   └── utils.py           # Helper functions
├── tools/
│   └── my_tool.py         # If feature adds a tool
└── tests/
    └── test_my_feature.py # Unit tests
```

### 4. Creating a New Tool

Extend the `Tool` base class:

```python
from light_agent.agent.tools.base import Tool
from typing import Any

class MyTool(Tool):
    """Brief description of what the tool does."""

    @property
    def name(self) -> str:
        return "my_tool_name"

    @property
    def description(self) -> str:
        return "What this tool does and when to use it."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."}
            },
            "required": ["param1"]
        }

    async def execute(self, **kwargs: Any) -> str:
        # Tool implementation
        return "Result string"
```

### 5. Testing

```python
import pytest

class TestMyFeature:
    def test_basic_functionality(self):
        result = my_function("input")
        assert result == "expected"

    async def test_async_functionality(self):
        result = await async_function()
        assert result is not None
```

### 6. Pre-Commit Checklist

Before committing:

- [ ] Code passes `ruff check`
- [ ] Code passes `pyright`
- [ ] Tests pass (`pytest`)
- [ ] No `as any`, `@ts-ignore`, or type suppression
- [ ] Docstrings on public APIs
- [ ] Imports sorted

### 7. Commit Message Format

```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code restructuring
- test: Test additions
- chore: Maintenance

Examples:
feat(agent): add new thread serialization
fix(tools): resolve memory leak in approval tool
docs(readme): update usage instructions
```

### 8. Pull Request Process

1. Push branch to remote
2. Create PR via GitHub or `gh pr create`
3. Ensure CI checks pass
4. Request review
5. Address feedback
6. Merge and delete branch

```bash
# Push branch
git push -u origin feature/my-feature

# Create PR
gh pr create --title "feat: Add my feature" --body "Description..."
```

### 9. Directory Structure Reference

```
light_agent/
├── agent/              # Core agent logic
│   ├── tools/          # Tool implementations
│   ├── loop.py         # Main agent loop
│   └── ...
├── base/               # Bundled resources
│   ├── skills/         # Markdown skills
│   ├── memory/         # Memory files
│   └── agents/         # Agent definitions
├── cli/                # Command-line interface
├── config/             # Configuration
├── providers/          # LLM providers
└── utils/              # Utilities
```

### 10. Common Patterns

#### Using Pydantic Models

```python
from pydantic import BaseModel
from datetime import datetime

class MyModel(BaseModel):
    name: str
    value: int
    created_at: datetime = datetime.utcnow()
```

#### Async Operations

```python
import asyncio
from typing import Optional

async def fetch_data(self, query: str) -> Optional[dict]:
    # Async implementation
    await asyncio.sleep(0.1)
    return {"result": query}
```

#### Error Handling

```python
class MyError(Exception):
    """Custom error for this feature."""

async def risky_operation(self) -> str:
    try:
        result = await potentially_failing_call()
        return result
    except SpecificError as e:
        # Handle specific error
        raise MyError("Helpful message") from e
```

## Quick Reference

```bash
# Create branch
git checkout -b feature/new-feature

# Lint
uv run ruff check light_agent/

# Type check
uv run pyright light_agent/

# Test
pytest light_agent/

# Commit
git add .
git commit -m "feat(scope): description"

# Push
git push -u origin feature/new-feature
```
