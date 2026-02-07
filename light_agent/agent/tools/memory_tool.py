import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from rank_bm25 import BM25Okapi

from light_agent.agent.tools.base import Tool


class LongMemoryTool(Tool):
    """
    A tool to store and retrieve past interactions using SQLite and BM25 relevance ranking.
    """

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        # Save in data/memory/ instead of workspace/
        self.data_dir = workspace_dir.parent / "data" / "memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "long_memory.db"
        self._init_db()
        self._migrate_json_files()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    conversation_id TEXT,
                    question TEXT,
                    answer TEXT,
                    summary TEXT,
                    raw_json TEXT,
                    type TEXT DEFAULT 'qa'
                )
            """)
            # Index for performance and safety
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cid_ts ON interactions(conversation_id, timestamp)"
            )
            # Add type column if it doesn't exist (migration)
            try:
                conn.execute("ALTER TABLE interactions ADD COLUMN type TEXT DEFAULT 'qa'")
            except sqlite3.OperationalError:
                pass  # Column already exists
            conn.commit()

    def get_recent_context(self, limit: int = 5) -> str:
        """Fetches the last N interactions for the system prompt context."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM interactions ORDER BY timestamp DESC LIMIT ?", (limit,)
                )
                rows = cursor.fetchall()

            if not rows:
                return "No recent interactions found."

            parts = ["## Recent Interactions (from Long-term Memory)"]
            # Reverse to show chronological order in prompt
            for row in reversed(rows):
                parts.append(
                    f"### [{row['timestamp']}] (ID: {row['conversation_id']})\n**Summary**: {row['summary']}\n**Q**: {row['question']}\n**A**: {row['answer']}"
                )

            return "\n\n".join(parts)
        except Exception as e:
            return f"Error retrieving context: {str(e)}"

    def _migrate_json_files(self):
        """Migrate existing JSON files from memory/ directory to SQLite."""
        memory_dir = self.workspace_dir / "memory"
        if not memory_dir.exists():
            return

        for json_file in memory_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        continue

                    with sqlite3.connect(self.db_path) as conn:
                        for entry in data:
                            # Skip legacy markers
                            if entry.get("type") == "legacy_md":
                                continue

                            conn.execute(
                                """
                                INSERT OR IGNORE INTO interactions (timestamp, conversation_id, question, answer, summary, raw_json)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    entry.get("timestamp"),
                                    entry.get("conversation_id"),
                                    entry.get("question"),
                                    entry.get("answer"),
                                    entry.get("summary"),
                                    json.dumps(entry, ensure_ascii=False),
                                ),
                            )
                        conn.commit()
            except Exception:
                # Silent skip during migration to avoid crashing tool load
                continue

    @property
    def name(self) -> str:
        return "long_memory"

    @property
    def description(self) -> str:
        return "Store and search historical interactions using relevance ranking (BM25) and time-based filters. Use this to recall past technical context or user preferences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "store"],
                    "description": "The action to perform: 'search' history or 'store' a new entry.",
                },
                "query": {
                    "type": "string",
                    "description": "The search term or question to find in history (required for search).",
                },
                "period": {
                    "type": "string",
                    "description": "Optional period filter for search, e.g., '30d' for 30 days, '12h' for 12 hours.",
                },
                "entry": {
                    "type": "object",
                    "description": "The entry dictionary to store (required for store).",
                },
            },
            "required": ["action"],
        }

    async def execute(self, **kwargs: Any) -> str:
        """Main execution point for the tool."""
        action = kwargs.get("action", "")
        if action == "store":
            entry = kwargs.get("entry")
            if not entry:
                return "Error: 'entry' is required for 'store' action."
            return await self.store(entry)
        elif action == "search":
            query = kwargs.get("query")
            if not query:
                return "Error: 'query' is required for 'search' action."
            return await self.search(query, kwargs.get("period"))
        else:
            return f"Error: Unknown action '{action}'."

    async def store(self, entry: Dict[str, Any]) -> str:
        """Stores a conversation entry in the database."""
        try:
            entry_type = entry.get("type", "qa")  # "qa" or "observation"

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO interactions (conversation_id, question, answer, summary, raw_json, type) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        entry.get("conversation_id"),
                        entry.get("question") or "",
                        entry.get("answer") or "",
                        entry.get("summary") or "",
                        json.dumps(entry, ensure_ascii=False),
                        entry_type,
                    ),
                )
                conn.commit()
            return f"Entry stored successfully in long-term memory (type: {entry_type})."
        except Exception as e:
            return f"Error storing entry: {str(e)}"

    async def store_observation(
        self,
        conversation_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: str,
        insight: str,
    ) -> str:
        """
        Stores a tool observation in the database.
        This captures discoveries made during tool execution.
        """
        entry = {
            "type": "observation",
            "conversation_id": conversation_id,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "insight": insight,
            "summary": insight,  # Use insight as summary for searchability
        }
        return await self.store(entry)

    async def search(self, query: str, period: Optional[str] = None) -> str:
        """
        Searches historical interactions using BM25 relevance ranking.
        Period can be like '30d', '24h', etc.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                sql = "SELECT * FROM interactions"
                params = []

                if period:
                    # Simple period parsing
                    days = 0
                    if period.endswith("d"):
                        days = int(period[:-1])
                    elif period.endswith("h"):
                        days = int(period[:-1]) / 24

                    if days > 0:
                        since = (datetime.now() - timedelta(days=days)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        sql += " WHERE timestamp >= ?"
                        params.append(since)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

            if not rows:
                return "No matching interactions found."

            # Prepare corpus for BM25
            # We rank based on summary, question, and answer combined
            corpus = []
            results_map = []

            for row in rows:
                text = f"{row['summary']} {row['question']} {row['answer']}"
                corpus.append(text.lower().split())
                results_map.append(row)

            bm25 = BM25Okapi(corpus)
            tokenized_query = query.lower().split()

            # Get top 5 results
            top_n = bm25.get_top_n(tokenized_query, results_map, n=5)

            if not top_n:
                return "No relevant results found."

            output = ["### Relevant Past Interactions:"]
            for res in top_n:
                output.append(
                    f"- [{res['timestamp']}] (ID: {res['conversation_id']})\n"
                    f"  **Summary**: {res['summary']}\n"
                    f"  **Q**: {res['question']}\n"
                    f"  **A**: {res['answer']}\n"
                )

            return "\n".join(output)

        except Exception as e:
            return f"Error searching memory: {str(e)}"
