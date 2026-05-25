"""Tests for debate.skills.base_skill — BaseSkill abstract class."""

import pytest

from debate.skills.base_skill import BaseSkill


class ConcreteSkill(BaseSkill):
    """Concrete implementation for testing."""

    def execute(self, context: dict) -> str:
        return "executed"

    def validate_input(self, context: dict) -> None:
        if "required" not in context:
            raise ValueError("missing 'required'")


class TestBaseSkill:
    """Tests for the abstract BaseSkill interface."""

    def test_concrete_must_implement_execute(self):
        class BadSkill(BaseSkill):
            def validate_input(self, context):
                pass

        with pytest.raises(TypeError):
            BadSkill()

    def test_concrete_must_implement_validate(self):
        class BadSkill(BaseSkill):
            def execute(self, context):
                return ""

        with pytest.raises(TypeError):
            BadSkill()

    def test_description_is_set(self):
        skill = ConcreteSkill()
        # Description may be empty for the test concrete class
        # (no SKILL.md in its directory), but the property exists
        assert isinstance(skill.description, str)

    def test_execute_is_callable(self):
        skill = ConcreteSkill()
        result = skill.execute({"required": True})
        assert result == "executed"

    def test_validate_input_raises_on_bad_context(self):
        skill = ConcreteSkill()
        with pytest.raises(ValueError):
            skill.validate_input({})
