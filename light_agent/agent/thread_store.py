"""Thread persistence layer."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from light_agent.agent.thread import ThreadState, ThreadStatus


class ThreadStore:
    """Persist and retrieve agent thread states."""

    def __init__(self, storage_dir: Path):
        """Initialize thread store with a storage directory.

        Args:
            storage_dir: Directory where thread JSON files will be stored.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, thread: ThreadState) -> None:
        """Serialize thread to JSON file.

        Args:
            thread: The thread state to persist.
        """
        thread.updated_at = datetime.utcnow()
        filepath = self.storage_dir / f"{thread.thread_id}.json"
        filepath.write_text(thread.model_dump_json(indent=2))

    def load(self, thread_id: str) -> Optional[ThreadState]:
        """Deserialize thread from JSON file.

        Args:
            thread_id: The ID of the thread to load.

        Returns:
            ThreadState if found, None otherwise.
        """
        filepath = self.storage_dir / f"{thread_id}.json"
        if not filepath.exists():
            return None
        return ThreadState.model_validate_json(filepath.read_text())

    def delete(self, thread_id: str) -> bool:
        """Delete a thread from storage.

        Args:
            thread_id: The ID of the thread to delete.

        Returns:
            True if deleted, False if not found.
        """
        filepath = self.storage_dir / f"{thread_id}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def list_threads(self) -> list[str]:
        """List all thread IDs in storage.

        Returns:
            List of thread IDs.
        """
        return [f.stem for f in self.storage_dir.glob("*.json")]

    def update_status(self, thread_id: str, status: ThreadStatus) -> bool:
        """Update the status of a thread.

        Args:
            thread_id: The ID of the thread to update.
            status: The new status.

        Returns:
            True if updated, False if not found.
        """
        thread = self.load(thread_id)
        if thread is None:
            return False
        thread.metadata["status"] = status.value
        self.save(thread)
        return True
