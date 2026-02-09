"""Session compaction system for automatic context optimization.

Provides intelligent compression of conversation history when approaching
token limits, preserving important information while removing redundant content.
"""

from .config import (
    CompactionConfig,
    CompactionStrategy,
    default_compaction_config,
)
from .controller import SessionCompactor
from .strategies import (
    SummarizeStrategy,
    PruneStrategy,
    MergeStrategy,
    SemanticCompactionStrategy,
)

__all__ = [
    "CompactionConfig",
    "CompactionStrategy",
    "default_compaction_config",
    "SessionCompactor",
    "SummarizeStrategy",
    "PruneStrategy",
    "MergeStrategy",
    "SemanticCompactionStrategy",
]
