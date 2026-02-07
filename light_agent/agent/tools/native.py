"""Native tool wrapper for Python functions."""

from typing import Any, Callable

from light_agent.agent.tools.base import Tool


class NativeTool(Tool):
    """
    Wrapper for native Python functions to be used as tools.

    Allows registering arbitrary Python functions as agent tools.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: dict[str, Any] | None = None,
    ):
        """
        Initialize a native tool.

        Args:
            name: Tool name.
            func: Python function to execute.
            description: Tool description.
            parameters: JSON Schema for parameters (defaults to empty object).
        """
        self._name = name
        self._func = func
        self._description = description
        self._parameters = parameters or {"type": "object", "properties": {}}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    async def execute(self, **kwargs: Any) -> str:
        """Execute the wrapped function."""
        import inspect

        # Handle both sync and async functions
        if inspect.iscoroutinefunction(self._func):
            result = await self._func(**kwargs)
        else:
            result = self._func(**kwargs)

        return str(result)
