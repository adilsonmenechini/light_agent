"""Control flow hooks for agent execution interception."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional


class HookPoint(str, Enum):
    """Points in the agent loop where hooks can intercept."""

    BEFORE_TOOL_CALL = "before_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"
    BEFORE_LLM_CALL = "before_llm_call"
    AFTER_LLM_CALL = "after_llm_call"
    BEFORE_MESSAGE = "before_message"
    AFTER_MESSAGE = "after_message"


@dataclass
class HookContext:
    """Context passed to hooks."""

    thread_id: str
    step_number: int
    tool_name: Optional[str] = None
    tool_args: Optional[Dict] = None
    llm_prompt: Optional[str] = None
    message: Optional[Dict] = None
    extra: Optional[Dict] = None


class HookResult:
    """Result from hook execution."""

    CONTINUE = None  # Continue normal flow
    STOP = "stop"  # Stop execution

    def __init__(self, action: Optional[str] = None, data: Optional[Dict] = None):
        self.action = action
        self.data = data or {}

    @classmethod
    def continue_(cls) -> "HookResult":
        return cls(action=None)

    @classmethod
    def stop(cls, reason: str = "") -> "HookResult":
        return cls(action=cls.STOP, data={"reason": reason})

    @classmethod
    def pause_for_approval(cls, tool_name: str, reason: str = "") -> "HookResult":
        return cls(action="pause_for_approval", data={"tool_name": tool_name, "reason": reason})

    @classmethod
    def skip(cls, reason: str = "") -> "HookResult":
        return cls(action="skip", data={"reason": reason})

    @classmethod
    def modify(cls, modifications: Dict) -> "HookResult":
        return cls(action="modify", data=modifications)


class Hook(ABC):
    """Base class for control flow hooks."""

    @abstractmethod
    async def run(self, context: HookContext) -> Optional[HookResult]:
        """Execute hook logic.

        Args:
            context: Hook context with execution details

        Returns:
            HookResult or None to continue
        """
        pass


class ApprovalHook(Hook):
    """Hook that requires human approval before high-stakes operations."""

    HIGH_STAKES_TOOLS = {"exec", "delete", "deploy", "write_file", "rm"}

    def __init__(self, approval_tool_name: str = "request_human_approval"):
        self.approval_tool_name = approval_tool_name

    async def run(self, context: HookContext) -> Optional[HookResult]:
        if context.tool_name in self.HIGH_STAKES_TOOLS:
            return HookResult.pause_for_approval(
                context.tool_name, f"High-stakes tool '{context.tool_name}' requires approval"
            )
        return None


class LoggingHook(Hook):
    """Hook for logging agent execution steps."""

    def __init__(self, logger=None):
        self.logger = logger

    async def run(self, context: HookContext) -> Optional[HookResult]:
        if self.logger:
            self.logger.info(f"Hook: {context.step_number} | {context.tool_name or 'llm'}")
        return None


class RateLimitHook(Hook):
    """Hook for rate limiting LLM calls."""

    def __init__(self, max_calls_per_minute: int = 60):
        self.max_calls = max_calls_per_minute
        self.calls: list = []

    async def run(self, context: HookContext) -> Optional[HookResult]:
        import time

        if context.tool_name != "llm":
            return None

        now = time.time()
        minute_ago = now - 60

        # Clean old calls
        self.calls = [t for t in self.calls if t > minute_ago]

        if len(self.calls) >= self.max_calls:
            wait_time = 60 - (now - self.calls[0])
            return HookResult.pause_for_approval(
                "rate_limit", f"Rate limit exceeded. Wait {int(wait_time)}s"
            )

        self.calls.append(now)
        return None


class ValidationHook(Hook):
    """Hook for validating tool arguments before execution."""

    def __init__(self):
        self.validators: Dict[str, Callable] = {}

    def register_validator(self, tool_name: str, validator: Callable):
        self.validators[tool_name] = validator

    async def run(self, context: HookContext) -> Optional[HookResult]:
        if not context.tool_name or not context.tool_args:
            return None

        validator = self.validators.get(context.tool_name)
        if validator:
            try:
                validator(context.tool_args)
            except ValueError as e:
                return HookResult.stop(str(e))

        return None


class HookManager:
    """Manage and execute hooks for agent control flow."""

    def __init__(self):
        self._hooks: Dict[HookPoint, list[Hook]] = {hp: [] for hp in HookPoint}

    def register(self, hook_point: HookPoint, hook: Hook) -> None:
        """Register a hook at a specific point."""
        self._hooks[hook_point].append(hook)

    async def execute(self, hook_point: HookPoint, context: HookContext) -> Optional[HookResult]:
        """Execute all hooks for a given point.

        Returns:
            First non-None result from hooks, or None to continue
        """
        for hook in self._hooks[hook_point]:
            result = await hook.run(context)
            if result is not None:
                return result
        return None

    def list_hooks(self) -> Dict[HookPoint, list[str]]:
        """List all registered hooks by name."""
        return {hp: [type(h).__name__ for h in hooks] for hp, hooks in self._hooks.items()}
