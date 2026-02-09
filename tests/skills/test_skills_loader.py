"""Tests for SkillsLoader."""

import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from light_agent.agent.skills import SkillsLoader


class TestSkillsLoader:
    """Tests for SkillsLoader class."""

    def test_get_metadata_yaml_parsing(self) -> None:
        """Test YAML metadata parsing."""
        content = """---
name: Test Skill
description: Testing
author: Author
---
Content"""
        match = content.startswith("---")
        assert match is True
        yaml_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert yaml_match is not None
        meta = yaml.safe_load(yaml_match.group(1))
        assert meta["name"] == "Test Skill"
        assert meta["description"] == "Testing"
        assert meta["author"] == "Author"
