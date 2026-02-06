import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class MemoryStore:
    def __init__(self, workspace_dir: Path):
        self.memory_dir = workspace_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "MEMORY.md"

    def read_long_term(self) -> str:
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""

    def get_context(self) -> str:
        """Only returns long-term fixed facts (MEMORY.md)."""
        long_term = self.read_long_term()
        if long_term:
            return f"## Long-term Memory\n{long_term}"
        return ""
