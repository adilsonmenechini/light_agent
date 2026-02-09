"""Tests for thinking control system."""

import pytest
from lightagent.agent.thinking import (
    ThinkLevel,
    ThinkingConfig,
    ThinkingController,
    ThinkingEvent,
    ThinkingState,
    default_thinking_config,
    think_level_from_string,
    get_level_description,
    should_use_thinking,
    estimate_thinking_effort,
)


class TestThinkLevel:
    """Tests for ThinkLevel enum."""

    def test_all_levels_exist(self) -> None:
        """Should have all expected levels."""
        assert ThinkLevel.OFF.value == "off"
        assert ThinkLevel.LOW.value == "low"
        assert ThinkLevel.MEDIUM.value == "medium"
        assert ThinkLevel.HIGH.value == "high"


class TestThinkingConfig:
    """Tests for ThinkingConfig."""

    def test_defaults(self) -> None:
        """Should have correct default values."""
        config = ThinkingConfig()
        assert config.level == ThinkLevel.MEDIUM
        assert config.max_thought_length == 2000
        assert config.emit_thinking_events is True
        assert config.store_thinking_history is True
        assert config.max_history_entries == 50
        assert config.min_context_for_thinking == 5
        assert config.auto_escalate is False
        assert config.escalation_threshold == 3

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        config = ThinkingConfig(
            level=ThinkLevel.HIGH,
            max_thought_length=5000,
            emit_thinking_events=False,
            auto_escalate=True,
        )
        assert config.level == ThinkLevel.HIGH
        assert config.max_thought_length == 5000
        assert config.emit_thinking_events is False
        assert config.auto_escalate is True


class TestDefaultThinkingConfig:
    """Tests for default_thinking_config function."""

    def test_returns_config(self) -> None:
        """Should return a ThinkingConfig instance."""
        config = default_thinking_config()
        assert isinstance(config, ThinkingConfig)


class TestThinkLevelFromString:
    """Tests for think_level_from_string function."""

    def test_valid_levels(self) -> None:
        """Should convert valid strings."""
        assert think_level_from_string("off") == ThinkLevel.OFF
        assert think_level_from_string("low") == ThinkLevel.LOW
        assert think_level_from_string("medium") == ThinkLevel.MEDIUM
        assert think_level_from_string("high") == ThinkLevel.HIGH

    def test_case_insensitive(self) -> None:
        """Should be case insensitive."""
        assert think_level_from_string("OFF") == ThinkLevel.OFF
        assert think_level_from_string("Low") == ThinkLevel.LOW
        assert think_level_from_string("MEDIUM") == ThinkLevel.MEDIUM

    def test_invalid_returns_medium(self) -> None:
        """Invalid string should return MEDIUM."""
        assert think_level_from_string("invalid") == ThinkLevel.MEDIUM
        assert think_level_from_string("") == ThinkLevel.MEDIUM


class TestGetLevelDescription:
    """Tests for get_level_description function."""

    def test_all_levels_have_description(self) -> None:
        """All levels should have descriptions."""
        for level in ThinkLevel:
            desc = get_level_description(level)
            assert desc is not None
            assert len(desc) > 0


class TestShouldUseThinking:
    """Tests for should_use_thinking function."""

    def test_off_never_thinks(self) -> None:
        """OFF level should never think."""
        config = ThinkingConfig(level=ThinkLevel.OFF)
        assert should_use_thinking(config, 100, True) is False
        assert should_use_thinking(config, 0, False) is False

    def test_low_thinks_on_complex(self) -> None:
        """LOW level thinks only on complex tasks."""
        config = ThinkingConfig(level=ThinkLevel.LOW)
        assert should_use_thinking(config, 0, True) is True
        assert should_use_thinking(config, 0, False) is False

    def test_medium_thinks_with_context(self) -> None:
        """MEDIUM level thinks with enough context or complex."""
        config = ThinkingConfig(level=ThinkLevel.MEDIUM)
        assert should_use_thinking(config, 10, False) is True
        assert should_use_thinking(config, 3, True) is True
        assert should_use_thinking(config, 3, False) is False

    def test_high_always_thinks(self) -> None:
        """HIGH level always thinks."""
        config = ThinkingConfig(level=ThinkLevel.HIGH)
        assert should_use_thinking(config, 100, False) is True
        assert should_use_thinking(config, 0, False) is True


class TestEstimateThinkingEffort:
    """Tests for estimate_thinking_effort function."""

    def test_off_returns_none(self) -> None:
        """OFF should return none."""
        assert estimate_thinking_effort(ThinkLevel.OFF, 10, False) == "none"

    def test_low_returns_minimal_or_moderate(self) -> None:
        """LOW should return minimal or moderate."""
        result = estimate_thinking_effort(ThinkLevel.LOW, 0, False)
        assert result in ("minimal", "moderate")

    def test_medium_returns_thorough_with_context(self) -> None:
        """MEDIUM should return thorough with enough context."""
        result = estimate_thinking_effort(ThinkLevel.MEDIUM, 15, False)
        assert result in ("moderate", "thorough")


class TestThinkingController:
    """Tests for ThinkingController class."""

    def test_initial_state(self) -> None:
        """Should start in IDLE state."""
        controller = ThinkingController()
        assert controller.state == ThinkingState.IDLE
        assert controller.is_thinking is False
        assert controller.level == ThinkLevel.MEDIUM

    def test_set_level(self) -> None:
        """Should change thinking level."""
        controller = ThinkingController()
        controller.set_level(ThinkLevel.HIGH)
        assert controller.level == ThinkLevel.HIGH

    def test_start_thinking_off(self) -> None:
        """Should not start thinking when OFF."""
        controller = ThinkingController(ThinkingConfig(level=ThinkLevel.OFF))
        result = controller.start_thinking(context_length=10)
        assert result is False
        assert controller.is_thinking is False

    def test_start_thinking_on(self) -> None:
        """Should start thinking when enabled."""
        controller = ThinkingController()
        result = controller.start_thinking(context_length=10)
        assert result is True
        assert controller.is_thinking is True

    def test_complete_thinking(self) -> None:
        """Should complete thinking process."""
        controller = ThinkingController()
        controller.start_thinking(context_length=10)
        event = controller.complete_thinking("Final thought")
        assert event is not None
        assert event.event_type == "completed"
        assert event.thought == "Final thought"
        assert controller.is_thinking is False

    def test_pause_and_resume(self) -> None:
        """Should pause and resume thinking."""
        controller = ThinkingController()
        controller.start_thinking(context_length=10)
        controller.pause_thinking()
        assert controller.state == ThinkingState.PAUSED
        controller.resume_thinking()
        assert controller.state == ThinkingState.THINKING

    def test_add_thought(self) -> None:
        """Should add intermediate thoughts."""
        controller = ThinkingController()
        controller.start_thinking(context_length=10)
        controller.add_thought("First thought")
        controller.add_thought("Second thought")
        assert len(controller.thought_history) == 2

    def test_reset(self) -> None:
        """Should reset state."""
        controller = ThinkingController()
        controller.start_thinking(context_length=10)
        controller.add_thought("Thought")
        controller.reset()
        assert controller.state == ThinkingState.IDLE
        assert controller.is_thinking is False

    def test_history_limit(self) -> None:
        """Should limit history size."""
        config = ThinkingConfig(store_thinking_history=True, max_history_entries=3)
        controller = ThinkingController(config=config, emit_events=False)
        controller.start_thinking(context_length=10)
        for i in range(5):
            controller.complete_thinking(f"Thought {i}")
            if i < 4:
                controller.start_thinking(context_length=10)

        assert len(controller.thought_history) == 3

    def test_get_effort_description(self) -> None:
        """Should return effort description."""
        controller = ThinkingController(ThinkingConfig(level=ThinkLevel.HIGH))
        effort = controller.get_effort_description(20)
        assert effort is not None
        assert len(effort) > 0

    def test_should_emit_detailed_thinking(self) -> None:
        """Should emit detailed for MEDIUM and HIGH."""
        controller_low = ThinkingController(ThinkingConfig(level=ThinkLevel.LOW))
        controller_medium = ThinkingController(ThinkingConfig(level=ThinkLevel.MEDIUM))
        controller_high = ThinkingController(ThinkingConfig(level=ThinkLevel.HIGH))

        assert controller_low.should_emit_detailed_thinking() is False
        assert controller_medium.should_emit_detailed_thinking() is True
        assert controller_high.should_emit_detailed_thinking() is True

    def test_should_emit_summary_only(self) -> None:
        """Should emit summary only for LOW."""
        controller_low = ThinkingController(ThinkingConfig(level=ThinkLevel.LOW))
        controller_medium = ThinkingController(ThinkingConfig(level=ThinkLevel.MEDIUM))

        assert controller_low.should_emit_summary_only() is True
        assert controller_medium.should_emit_summary_only() is False

    def test_get_state_summary(self) -> None:
        """Should return state summary."""
        controller = ThinkingController()
        controller.start_thinking(context_length=10)
        summary = controller.get_state_summary()
        assert summary["state"] == "thinking"
        assert summary["level"] == "medium"
        assert summary["is_thinking"] is True
        assert summary["history_count"] == 0

    def test_to_json(self) -> None:
        """Should serialize to JSON."""
        controller = ThinkingController()
        json_str = controller.to_json()
        assert isinstance(json_str, str)
        assert "medium" in json_str
        assert "idle" in json_str

    def test_complexity_score(self) -> None:
        """Should calculate complexity correctly."""
        controller = ThinkingController()
        controller.start_thinking(context_length=25, is_complex=True, task_type="debug")
        assert controller._complexity_score > 0

        controller.reset()
        controller.start_thinking(context_length=2, is_complex=False, task_type="list")
        assert controller._complexity_score < 0.5
