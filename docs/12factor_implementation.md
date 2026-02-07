# 12-Factor Agents Implementation Guide

This document provides detailed implementation tasks for achieving 12-Factor Agents alignment.

## Implementation Phases

### Phase 1: Thread Serialization (High Priority)
**Factors:** 5, 6, 12  
**Status:** In Progress  
**Estimated Effort:** 3-4 days

#### Task 1.1: Define Thread State Schema
Create `light_agent/agent/thread.py`:

```python
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

class ThreadStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class ThreadState(BaseModel):
    """Unified state representation for agent thread."""
    thread_id: str
    version: int = 1
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
```

#### Task 1.2: Create Thread Store
Create `light_agent/agent/thread_store.py`:

```python
from pathlib import Path
from light_agent.agent.thread import ThreadState, ThreadStatus

class ThreadStore:
    """Persist and retrieve agent thread states."""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, thread: ThreadState) -> None:
        """Serialize thread to JSON file."""
        thread.updated_at = datetime.utcnow()
        filepath = self.storage_dir / f"{thread.thread_id}.json"
        filepath.write_text(thread.model_dump_json(indent=2))
    
    def load(self, thread_id: str) -> Optional[ThreadState]:
        """Deserialize thread from JSON file."""
        filepath = self.storage_dir / f"{thread_id}.json"
        if not filepath.exists():
            return None
        return ThreadState.model_validate_json(filepath.read_text())
```

#### Task 1.3: Integrate with AgentLoop
- Modify `AgentLoop` to accept optional `thread_id`
- Serialize messages after each iteration
- Load thread state on initialization if `thread_id` provided

**Acceptance Criteria:**
- [ ] `ThreadState` schema validated with Pydantic
- [ ] Thread can be saved/loaded from disk
- [ ] `AgentLoop` supports resume from `thread_id`
- [ ] Unit tests for serialization/deserialization

---

### Phase 2: API Server Mode (High Priority)
**Factors:** 6, 11  
**Status:** In Progress  
**Estimated Effort:** 4-5 days

#### Task 2.1: FastAPI Server Setup
Create `light_agent/server/main.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Light Agent API", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for triggering agent."""
    agent = await setup_agent()
    result = await agent.run(request.message)
    return ChatResponse(response=result, thread_id=agent.conversation_id)

@app.post("/api/threads/{thread_id}/pause")
async def pause_thread(thread_id: str):
    """Pause a running thread."""
    # Set thread status to PAUSED

@app.post("/api/threads/{thread_id}/resume")
async def resume_thread(thread_id: str):
    """Resume a paused thread."""
    # Load thread state and continue execution

@app.get("/api/threads")
async def list_threads():
    """List all threads."""
    return {"threads": thread_store.list_threads()}

@app.post("/api/webhooks/{thread_id}")
async def webhook_handler(thread_id: str, payload: dict):
    """Handle external webhooks to resume paused threads."""
    thread = thread_store.load(thread_id)
    thread.messages.append({"role": "user", "content": payload.get("response")})
    thread_store.save(thread)
    return {"status": "resumed", "thread_id": thread_id}
```

#### Task 2.2: CLI Integration
Add to `light_agent/cli/commands.py`:

```python
@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000):
    """Start the Light Agent API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)
```

**Acceptance Criteria:**
- [ ] FastAPI- [ ] POST server starts successfully
 `/api/chat` triggers agent and returns response
- [ ] POST `/api/threads/{id}/pause` pauses thread
- [ ] POST `/api/threads/{id}/resume` resumes thread
- [ ] Webhook endpoint triggers thread resume
- [ ] Integration tests for API endpoints

---

### Phase 3: Human Approval Tool (Medium Priority)
**Factors:** 7, 8  
**Status:** In Progress  
**Estimated Effort:** 2-3 days

#### Task 3.1: Define Approval Tool Schema
Create `light_agent/agent/tools/approval.py`:

```python
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
import uuid
from datetime import datetime

class ApprovalUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ApprovalFormat(str, Enum):
    FREE_TEXT = "free_text"
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"

class ApprovalOptions(BaseModel):
    urgency: ApprovalUrgency = ApprovalUrgency.MEDIUM
    format: ApprovalFormat = ApprovalFormat.YES_NO
    choices: Optional[List[str]] = None
    timeout_seconds: int = 3600

class HumanApprovalTool:
    """Tool for requesting human approval before high-stakes operations."""
    
    name = "request_human_approval"
    
    description = """
    Request approval from a human before proceeding with a high-stakes operation.
    Use for: deploying to production, deleting resources, modifying infrastructure.
    
    Args:
        question: Clear question asking for approval
        context: Background context for the decision
        options: Approval configuration (urgency, format, choices)
    """
    
    parameters = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question to ask"},
            "context": {"type": "string", "description": "Context information"},
            "options": {"type": "object", "properties": {
                "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "format": {"type": "string", "enum": ["free_text", "yes_no", "multiple_choice"]},
                "choices": {"type": "array", "items": {"type": "string"}}
            }}
        },
        "required": ["question"]
    }
    
    async def execute(self, question: str, context: str = "", options = None) -> dict:
        """Execute approval request."""
        request_id = str(uuid.uuid4())[:8]
        approval_request = {
            "request_id": request_id,
            "question": question,
            "context": context,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        await self._store_pending(approval_request)
        return {"status": "waiting", "request_id": request_id}
```

#### Task 3.2: Approval Store
Create `light_agent/agent/approval_store.py`:

```python
from pathlib import Path
import json

class ApprovalStore:
    """Store and manage pending human approvals."""
    
    def __init__(self, storage_dir: Path):
        self.pending_dir = storage_dir / "pending"
        self.responses_dir = storage_dir / "responses"
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
    
    async def store_request(self, request: dict) -> None:
        filepath = self.pending_dir / f"{request['request_id']}.json"
        filepath.write_text(json.dumps(request))
    
    async def record_response(self, request_id: str, response: dict) -> None:
        response_file = self.responses_dir / f"{request_id}.json"
        response_file.write_text(json.dumps(response))
```

#### Task 3.3: API Endpoints for Approvals
Add to FastAPI app:

```python
@app.post("/api/approvals/{request_id}/respond")
async def respond_approval(request_id: str, body: dict):
    """Endpoint for humans to respond to approval requests."""
    await approval_store.record_response(request_id, {
        "response": body.get("response"),
        "approved": body.get("approved"),
        "user": body.get("user"),
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"status": "recorded", "request_id": request_id}
```

**Acceptance Criteria:**
- [ ] `request_human_approval` tool registered in `ToolRegistry`
- [ ] Approval request stored with unique ID
- [ ] API endpoint to submit approval responses
- [ ] Thread automatically resumes after approval
- [ ] Timeout handling for stale approvals

---

### Phase 4: Control Flow Hooks (Medium Priority)
**Factors:** 8  
**Status:** Pending  
**Estimated Effort:** 2-3 days

#### Task 4.1: Hook System Design
Create `light_agent/agent/hooks.py`:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum

class HookPoint(str, Enum):
    BEFORE_TOOL_CALL = "before_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"
    BEFORE_LLM_CALL = "before_llm_call"
    AFTER_LLM_CALL = "after_llm_call"

class HookContext:
    """Context passed to hooks."""
    thread_id: str
    step_number: int
    tool_name: Optional[str] = None
    tool_args: Optional[Dict] = None

class Hook(ABC):
    """Base class for control flow hooks."""
    
    @abstractmethod
    async def run(self, context: HookContext) -> Optional[dict]:
        pass

class ApprovalHook(Hook):
    """Hook that requires human approval before high-stakes tools."""
    
    HIGH_STAKES_TOOLS = {"exec", "delete", "deploy", "write_file"}
    
    async def run(self, context: HookContext) -> Optional[dict]:
        if context.tool_name in self.HIGH_STAKES_TOOLS:
            return {"action": "pause_for_approval", "tool": context.tool_name}
        return None

class HookManager:
    """Manage and execute hooks."""
    
    def __init__(self):
        self._hooks: Dict[HookPoint, list[Hook]] = {hp: [] for hp in HookPoint}
    
    def register(self, hook_point: HookPoint, hook: Hook) -> None:
        self._hooks[hook_point].append(hook)
    
    async def execute(self, hook_point: HookPoint, context: HookContext) -> Optional[dict]:
        for hook in self._hooks[hook_point]:
            result = await hook.run(context)
            if result:
                return result
        return None
```

#### Task 4.2: Integrate with AgentLoop
Add hook execution at strategic points in the agent loop:
- Before LLM call
- After LLM call
- Before tool execution
- After tool execution

**Acceptance Criteria:**
- [ ] `HookPoint` enum with all control flow points
- [ ] `Hook` base class and concrete implementations
- [ ] `HookManager` for registration and execution
- [ ] `ApprovalHook` intercepts high-stakes tools
- [ ] Integration with `AgentLoop` at all hook points

---

### Phase 5: Error Compaction (Low Priority)
**Factors:** 9  
**Status:** Pending  
**Estimated Effort:** 2 days

#### Task 5.1: Error Handler
Create `light_agent/agent/error_handler.py`:

```python
from typing import Any, Dict, Optional

class ErrorCompactor:
    """Compact errors into context-friendly format."""
    
    MAX_ERROR_LENGTH = 500
    
    def compact(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert error to compact, LLM-friendly format."""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error)[:self.MAX_ERROR_LENGTH],
            "suggested_fix": self._suggest_fix(error),
            "retry_recommended": self._should_retry(error),
            "context_summary": self._summarize_context(context)
        }
    
    def _suggest_fix(self, error: Exception) -> str:
        """Generate suggested fix based on error type."""
        error_messages = {
            "FileNotFoundError": "Check file path and ensure file exists",
            "PermissionError": "Verify file permissions or run with appropriate access"
        }
        return error_messages.get(type(error).__name__, "Review error message and adjust parameters")
    
    def _should_retry(self, error: Exception) -> bool:
        """Determine if error is retryable."""
        retryable = {"TimeoutError", "ConnectionError", "RateLimitError"}
        return type(error).__name__ in retryable
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Generate brief context summary."""
        return f"Step {context.get('step_number')}: {context.get('tool_name')}"
```

**Acceptance Criteria:**
- [ ] Error types classified and compacted
- [ ] Suggested fixes generated for common errors
- [ ] Retry recommendations based on error type
- [ ] Context summaries for error messages

---

### Phase 6: Stateless Reducer Pattern (Low Priority)
**Factors:** 12  
**Status:** Pending  
**Estimated Effort:** 3-4 days

#### Task 6.1: Reducer Function
Create `light_agent/agent/reducer.py`:

```python
from typing import Any, Dict, List, Tuple
from light_agent.agent.thread import ThreadState

class AgentReducer:
    """Stateless reducer for agent state transitions."""
    
    def reduce(self, state: ThreadState, event: Dict[str, Any]) -> Tuple[ThreadState, Dict[str, Any]]:
        """
        Pure function that reduces state with an event.
        
        Args:
            state: Current thread state
            event: New event to apply
            
        Returns:
            Tuple of (new_state, agent_response)
        """
        new_messages = state.messages + [event]
        new_state = ThreadState(
            thread_id=state.thread_id,
            created_at=state.created_at,
            updated_at=datetime.utcnow(),
            messages=new_messages,
            metadata=state.metadata
        )
        
        response = self._generate_response(new_state)
        return new_state, response
    
    def _generate_response(self, state: ThreadState) -> Dict[str, Any]:
        """Generate agent response based on current state."""
        # LLM call to determine next action
        pass
```

**Acceptance Criteria:**
- [ ] Reducer function is pure (no side effects)
- [ ] State transitions are predictable and testable
- [ ] Agent can be serialized/deserialized at any point
- [ ] Easy to fork/branch agent state

---

## Dependencies

Add to `pyproject.toml`:

```toml
[project.dependencies]
fastapi = ">=0.100.0"
uvicorn = {extras = ["standard"], version = ">=0.23.0"}
```

---

## File Structure

```
light_agent/
  agent/
    thread.py           # Task 1.1
    thread_store.py     # Task 1.2
    hooks.py            # Task 4.1
    error_handler.py    # Task 5.1
    reducer.py          # Task 6.1
    tools/
      approval.py       # Task 3.1
  server/
    main.py             # Task 2.1
  cli/
    commands.py         # Task 2.2
```

---

## Testing Strategy

### Unit Tests
- Thread serialization/deserialization
- Hook execution logic
- Error compaction

### Integration Tests
- API endpoints with real agent
- Pause/resume workflow
- Human approval flow

### E2E Tests
- Complete workflow with thread persistence
- Multi-step agent with human approval
