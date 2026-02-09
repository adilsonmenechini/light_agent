"""Human approval tool for high-stakes operations."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from lightagent.agent.tools.base import Tool


class ApprovalUrgency(str, Enum):
    """Urgency level for approval requests."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalFormat(str, Enum):
    """Format for approval response."""

    FREE_TEXT = "free_text"
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"


class ApprovalOptions(BaseModel):
    """Configuration options for approval requests."""

    urgency: ApprovalUrgency = ApprovalUrgency.MEDIUM
    format: ApprovalFormat = ApprovalFormat.YES_NO
    choices: Optional[List[str]] = None
    timeout_seconds: int = 3600


class HumanApprovalTool(Tool):
    """Tool for requesting human approval before high-stakes operations."""

    @property
    def name(self) -> str:
        """Tool name."""
        return "request_human_approval"

    @property
    def description(self) -> str:
        """Description of the tool."""
        return "Request approval from a human before proceeding with a high-stakes operation."

    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question to ask for approval"},
                "context": {"type": "string", "description": "Background context for the decision"},
                "options": {
                    "type": "object",
                    "properties": {
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                        },
                        "format": {
                            "type": "string",
                            "enum": ["free_text", "yes_no", "multiple_choice"],
                        },
                        "choices": {"type": "array", "items": {"type": "string"}},
                        "timeout_seconds": {"type": "integer", "minimum": 60, "maximum": 86400},
                    },
                },
            },
            "required": ["question"],
        }

    def __init__(self, store: Optional["ApprovalStore"] = None):
        """Initialize with optional approval store."""
        self._store = store

    async def execute(self, **kwargs: Any) -> str:
        """Execute approval request.

        Args:
            **kwargs: Tool parameters (question, context, options)

        Returns:
            String with request status and ID
        """
        question = kwargs.get("question", "")
        context = kwargs.get("context", "")
        options = kwargs.get("options")

        request_id = str(uuid.uuid4())[:8]
        approval_opts = options or {}
        urgency = approval_opts.get("urgency", "medium")
        fmt = approval_opts.get("format", "yes_no")
        timeout = approval_opts.get("timeout_seconds", 3600)

        approval_request = {
            "request_id": request_id,
            "question": question,
            "context": context,
            "status": "pending",
            "urgency": urgency,
            "format": fmt,
            "timeout_seconds": timeout,
            "created_at": datetime.utcnow().isoformat(),
        }

        if self._store:
            await self._store.store_request(approval_request)

        return f"Approval request created:\nID: {request_id}\nQuestion: {question}\nUrgency: {urgency}\nStatus: pending"


class ApprovalStore:
    """Store and manage pending human approvals."""

    def __init__(self, storage_dir: str = "data/approvals"):
        """Initialize approval store.

        Args:
            storage_dir: Directory for storing approval requests
        """
        from pathlib import Path

        self.pending_dir = Path(storage_dir) / "pending"
        self.responses_dir = Path(storage_dir) / "responses"
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

    async def store_request(self, request: Dict[str, Any]) -> None:
        """Store a pending approval request."""
        import json

        filepath = self.pending_dir / f"{request['request_id']}.json"
        filepath.write_text(json.dumps(request, indent=2))

    async def record_response(
        self, request_id: str, response: str, approved: bool, user: Optional[str] = None
    ) -> bool:
        """Record a response to an approval request.

        Args:
            request_id: The approval request ID
            response: The user's response
            approved: Whether the request was approved
            user: Optional user identifier

        Returns:
            True if recorded, False if request not found
        """
        import json
        import os

        pending_file = self.pending_dir / f"{request_id}.json"
        if not pending_file.exists():
            return False

        # Read and update the request
        request = json.loads(pending_file.read_text())
        request["status"] = "responded"
        request["response"] = response
        request["approved"] = approved
        request["user"] = user
        request["responded_at"] = datetime.utcnow().isoformat()

        # Move to responses
        os.makedirs(self.responses_dir, exist_ok=True)
        response_file = self.responses_dir / f"{request_id}.json"
        response_file.write_text(json.dumps(request, indent=2))
        pending_file.unlink()

        return True

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a pending approval request."""
        import json

        filepath = self.pending_dir / f"{request_id}.json"
        if not filepath.exists():
            return None
        return json.loads(filepath.read_text())

    async def list_pending(self) -> List[Dict[str, Any]]:
        """List all pending approval requests."""
        import json

        pending = []
        for filepath in self.pending_dir.glob("*.json"):
            pending.append(json.loads(filepath.read_text()))
        return pending

    async def get_response(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a recorded response."""
        import json

        filepath = self.responses_dir / f"{request_id}.json"
        if not filepath.exists():
            return None
        return json.loads(filepath.read_text())
