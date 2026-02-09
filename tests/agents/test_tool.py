"""Tests for Tool base class."""

from abc import ABC
from typing import Any
from unittest.mock import MagicMock

import pytest

from light_agent.agent.tools.base import Tool


class MockTool(Tool):
    """Concrete implementation of Tool for testing."""

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input string"},
                "count": {"type": "integer", "description": "Count", "minimum": 1, "maximum": 100},
                "enabled": {"type": "boolean", "description": "Enable option"},
            },
            "required": ["input"],
        }

    async def execute(self, **kwargs: Any) -> str:
        return f"Executed with {kwargs}"


class TestTool:
    """Tests for Tool base class."""

    def test_to_schema(self) -> None:
        """Test conversion to OpenAI function schema."""
        tool = MockTool()
        schema = tool.to_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "mock_tool"
        assert schema["function"]["description"] == "A mock tool for testing"
        assert schema["function"]["parameters"] == tool.parameters

    def test_validate_params_valid(self) -> None:
        """Test parameter validation with valid params."""
        tool = MockTool()
        errors = tool.validate_params({"input": "test", "count": 5, "enabled": True})
        assert errors == []

    def test_validate_params_missing_required(self) -> None:
        """Test parameter validation with missing required param."""
        tool = MockTool()
        errors = tool.validate_params({"count": 5})
        assert len(errors) == 1
        assert "missing required input" in errors[0]

    def test_validate_params_invalid_type_string(self) -> None:
        """Test parameter validation with wrong type for string field."""
        tool = MockTool()
        errors = tool.validate_params({"input": 123})
        assert len(errors) == 1
        assert "should be string" in errors[0]

    def test_validate_params_invalid_type_integer(self) -> None:
        """Test parameter validation with wrong type for integer field."""
        tool = MockTool()
        errors = tool.validate_params({"input": "test", "count": "not_a_number"})
        assert len(errors) >= 1
        assert any("should be integer" in e for e in errors)

    def test_validate_params_below_minimum(self) -> None:
        """Test parameter validation with value below minimum."""
        tool = MockTool()
        errors = tool.validate_params({"input": "test", "count": 0})
        assert len(errors) == 1
        assert "must be >= 1" in errors[0]

    def test_validate_params_above_maximum(self) -> None:
        """Test parameter validation with value above maximum."""
        tool = MockTool()
        errors = tool.validate_params({"input": "test", "count": 200})
        assert len(errors) == 1
        assert "must be <= 100" in errors[0]

    def test_validate_params_enum_violation(self) -> None:
        """Test parameter validation with enum values."""
        enum_tool = EnumTestTool()
        errors = enum_tool.validate_params({"mode": "invalid"})
        assert len(errors) == 1
        assert "must be one of" in errors[0]

    def test_validate_params_nested_object(self) -> None:
        """Test parameter validation with nested object."""
        nested_tool = NestedTestTool()
        errors = nested_tool.validate_params({"config": {"key": "value"}})
        assert errors == []

    def test_validate_params_nested_object_missing_required(self) -> None:
        """Test nested object validation with missing required field."""
        nested_tool = NestedTestTool()
        errors = nested_tool.validate_params({"config": {}})
        assert len(errors) == 1
        assert "missing required config.key" in errors[0]

    def test_validate_params_array(self) -> None:
        """Test parameter validation with array."""
        array_tool = ArrayTestTool()
        errors = array_tool.validate_params({"items": [1, 2, 3]})
        assert errors == []

    def test_validate_params_array_invalid_items(self) -> None:
        """Test array validation with invalid item type."""
        array_tool = ArrayTestTool()
        errors = array_tool.validate_params({"items": [1, "two", 3]})
        assert len(errors) >= 1

    def test_validate_params_string_min_length(self) -> None:
        """Test string validation with minLength."""
        minlen_tool = MinLenTestTool()
        errors = minlen_tool.validate_params({"text": "ab"})
        assert len(errors) == 1
        assert "at least 5 chars" in errors[0]

    def test_validate_params_string_max_length(self) -> None:
        """Test string validation with maxLength."""
        maxlen_tool = MaxLenTestTool()
        errors = maxlen_tool.validate_params({"text": "a" * 20})
        assert len(errors) == 1
        assert "at most 10 chars" in errors[0]

    def test_validate_params_object_type_required(self) -> None:
        """Test that validation works with object type schema."""
        tool = MockTool()
        errors = tool.validate_params({"input": "test"})
        assert errors == []

    def test_validate_params_returns_error_list(self) -> None:
        """Test that validate_params returns a list of errors."""
        enum_tool = EnumTestTool()
        errors = enum_tool.validate_params({"mode": "invalid"})
        assert isinstance(errors, list)
        assert len(errors) > 0


class EnumTestTool(Tool):
    """Tool with enum parameter for testing."""

    @property
    def name(self) -> str:
        return "enum_tool"

    @property
    def description(self) -> str:
        return "Tool with enum"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"mode": {"type": "string", "enum": ["read", "write", "delete"]}},
            "required": ["mode"],
        }

    async def execute(self, **kwargs: Any) -> str:
        return "executed"


class NestedTestTool(Tool):
    """Tool with nested object parameter for testing."""

    @property
    def name(self) -> str:
        return "nested_tool"

    @property
    def description(self) -> str:
        return "Tool with nested object"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {"key": {"type": "string"}},
                    "required": ["key"],
                }
            },
            "required": ["config"],
        }

    async def execute(self, **kwargs: Any) -> str:
        return "executed"


class ArrayTestTool(Tool):
    """Tool with array parameter for testing."""

    @property
    def name(self) -> str:
        return "array_tool"

    @property
    def description(self) -> str:
        return "Tool with array"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "integer"}}},
            "required": ["items"],
        }

    async def execute(self, **kwargs: Any) -> str:
        return "executed"


class MinLenTestTool(Tool):
    """Tool with minLength constraint."""

    @property
    def name(self) -> str:
        return "minlen_tool"

    @property
    def description(self) -> str:
        return "Tool with minLength"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"text": {"type": "string", "minLength": 5}},
            "required": ["text"],
        }

    async def execute(self, **kwargs: Any) -> str:
        return "executed"


class MaxLenTestTool(Tool):
    """Tool with maxLength constraint."""

    @property
    def name(self) -> str:
        return "maxlen_tool"

    @property
    def description(self) -> str:
        return "Tool with maxLength"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"text": {"type": "string", "maxLength": 10}},
            "required": ["text"],
        }

    async def execute(self, **kwargs: Any) -> str:
        return "executed"
