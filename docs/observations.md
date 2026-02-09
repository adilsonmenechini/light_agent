# Tool Observations 2.0

Advanced system for capturing, organizing, and utilizing insights from tool executions.

## Overview

Tool Observations 2.0 provides intelligent observation management with automatic categorization, importance scoring, deduplication, and AI-powered summarization.

## Features

### Auto-Categorization

Observations are automatically categorized into 13 types:

| Category | Description |
|----------|-------------|
| `bug` | Bug reports and fixes |
| `config` | Configuration discoveries |
| `docs` | Documentation findings |
| `error` | Error encounters |
| `file_pattern` | File structure patterns |
| `finding` | General discoveries |
| `hint` | Suggestions and tips |
| `metric` | Performance metrics |
| `pattern` | Code patterns |
| `security` | Security findings |
| `test` | Test-related observations |
| `todo` | Pending tasks |
| `unknown` | Uncategorized |

### Importance Scoring

Each observation receives a priority score:

| Score | Priority | Use Case |
|-------|----------|----------|
| 1.0 | CRITICAL | Security findings, bugs, blockers |
| 0.8 | HIGH | Important discoveries, key insights |
| 0.6 | MEDIUM | Useful patterns, helpful findings |
| 0.4 | LOW | Minor details, low-impact notes |
| 0.2 | INFO | Basic information, confirmations |

### Deduplication

Prevents redundant observations using:
- **Content similarity** (Jaccard index ≥ 0.7)
- **Exact match detection**
- **Semantic deduplication** with configurable thresholds

### Context Awareness

Observations track:
- **Temporal context**: When the observation was made
- **Causal relationships**: Dependencies between observations
- **Session continuity**: Cross-session relevance

### AI Summaries

Automatic summarization provides:
- Brief descriptions of observation clusters
- Key takeaways for quick review
- Related observations grouped together

## Usage

### Basic Capture

```python
from lightagent.agent.observations import ToolObservation, MemoryConsolidator

# Observations are automatically captured by tools
observation = ToolObservation(
    tool_name="read_file",
    insight="Found configuration in config.yaml",
    importance=0.6,
    category="config"
)
```

### Query by Category

```python
from lightagent.agent.observations import MemoryConsolidator

consolidator = MemoryConsolidator()

# Get all security observations
security_obs = consolidator.query(
    categories=["security"],
    min_importance=0.8
)
```

### Query by Importance

```python
# Get all high-priority observations
high_priority = consolidator.query(
    min_importance=0.8
)
```

## Configuration

Default settings are in `lightagent/agent/observations/`:

```python
# Example: Custom importance thresholds
importance_thresholds = {
    "CRITICAL": 1.0,
    "HIGH": 0.8,
    "MEDIUM": 0.6,
    "LOW": 0.4,
    "INFO": 0.2
}

# Deduplication settings
deduplication = {
    "jaccard_threshold": 0.7,
    "enable_exact_dedup": True
}
```

## Architecture

```
lightagent/agent/observations/
├── __init__.py           # Main exports
├── categorizer.py        # 13-category classification
├── scorer.py             # Priority scoring (0-1)
├── deduplication.py      # Similarity detection
├── context.py            # Temporal/causal tracking
├── summarizer.py         # AI summaries
└── consolidation.py      # MemoryEntry, MemoryConsolidator
```

## Best Practices

1. **Review regularly**: Check high-priority observations after each session
2. **Use categories**: Filter by category for targeted reviews
3. **Trust scores**: Higher importance scores indicate more critical insights
4. **Leverage summaries**: Use AI summaries for quick context refresh

## Integration

Observations integrate with:
- **Short-term Memory**: Temporary session insights
- **Long-term Memory**: Persistent observation storage
- **Vector Search**: Semantic similarity for related findings
- **Session Compaction**: Preserved during context optimization
