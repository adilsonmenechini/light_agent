import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class MemoryStore:
    def __init__(self, workspace_dir: Path):
        self.memory_dir = workspace_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "MEMORY.md"

    def get_today_file(self, extension: str = "json") -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.memory_dir / f"{date_str}.{extension}"

    def read_today(self) -> List[Dict[str, Any]]:
        today_file = self.get_today_file("json")
        if today_file.exists():
            try:
                with open(today_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return []
        
        # Fallback to old MD if JSON doesn't exist (for transition)
        md_file = self.get_today_file("md")
        if md_file.exists():
            return [{"content": md_file.read_text(encoding="utf-8"), "type": "legacy_md"}]
            
        return []

    def append_entry(self, entry: Dict[str, Any]) -> None:
        """Append a structured entry to today's JSON memory (one line per entry)."""
        today_file = self.get_today_file("json")
        entries = self.read_today()
        
        # If it returned a list with one legacy entry, keep it or handle it
        if entries and entries[0].get("type") == "legacy_md":
            # Just start a fresh list for JSON if we are transitioning
            entries = []

        entries.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            **entry
        })

        # Format as a list with one line per minified object
        json_lines = [json.dumps(e, ensure_ascii=False) for e in entries]
        with open(today_file, "w", encoding="utf-8") as f:
            f.write("[\n" + ",\n".join(json_lines) + "\n]")

    def append_today(self, content: str) -> None:
        """Legacy support for plain string appends."""
        self.append_entry({"content": content})

    def read_long_term(self) -> str:
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""

    def get_context(self) -> str:
        parts = []
        long_term = self.read_long_term()
        if long_term:
            parts.append(f"## Long-term Memory\n{long_term}")

        entries = self.read_today()
        if entries:
            today_parts = ["## Today's Log"]
            for entry in entries:
                if entry.get("type") == "legacy_md":
                    today_parts.append(entry["content"])
                else:
                    ts = entry.get("timestamp", "")
                    cid = entry.get("conversation_id", "N/A")
                    summary = entry.get("summary", "")
                    question = entry.get("question", "")
                    answer = entry.get("answer", "")
                    content = entry.get("content", "")
                    
                    header = f"### [{ts}] (ID: {cid})"
                    if summary:
                        detail = content or f"User asked: {question}\nAgent replied: {answer}"
                        today_parts.append(f"{header}\n**Summary**: {summary}\n**Detail**: {detail}")
                    else:
                        today_parts.append(f"{header}\n{content or answer}")
            
            parts.append("\n".join(today_parts))

        return "\n\n".join(parts)
