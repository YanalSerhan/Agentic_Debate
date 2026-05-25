"""Tests for debate.skills.argument_skill — ArgumentSkill."""

import json

import pytest

from debate.skills.argument_skill.argument_skill import ArgumentSkill


class TestArgumentSkill:
    """Tests for ArgumentSkill."""

    def test_execute_returns_non_empty(self):
        skill = ArgumentSkill()
        result = skill.execute({"topic": "AI is good", "round": 1})
        assert result
        data = json.loads(result)
        assert data["side"] == "pro"
        assert "system" in data
        assert "user" in data

    def test_description_is_loaded(self):
        skill = ArgumentSkill()
        assert "FOR" in skill.description
        assert len(skill.description) > 0

    def test_raises_on_missing_topic(self):
        skill = ArgumentSkill()
        with pytest.raises(ValueError, match="topic"):
            skill.execute({})

    def test_raises_on_empty_topic(self):
        skill = ArgumentSkill()
        with pytest.raises(ValueError, match="topic"):
            skill.execute({"topic": ""})

    def test_includes_opponent_argument_in_prompt(self):
        skill = ArgumentSkill()
        result = skill.execute({
            "topic": "AI is good",
            "round": 2,
            "opponent_argument": "AI causes unemployment",
        })
        data = json.loads(result)
        assert "opponent" in data["user"].lower() or "argued" in data["user"].lower()

    def test_round_number_in_output(self):
        skill = ArgumentSkill()
        result = skill.execute({"topic": "AI is good", "round": 3})
        data = json.loads(result)
        assert data["round"] == 3
