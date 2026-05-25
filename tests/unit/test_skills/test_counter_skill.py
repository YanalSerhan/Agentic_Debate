"""Tests for debate.skills.counter_skill — CounterSkill."""

import json

import pytest

from debate.skills.counter_skill.counter_skill import CounterSkill


class TestCounterSkill:
    """Tests for CounterSkill."""

    def test_execute_returns_counter_argument(self):
        skill = CounterSkill()
        result = skill.execute({
            "topic": "AI is good",
            "round": 2,
            "opponent_argument": "AI increases productivity",
        })
        assert result
        data = json.loads(result)
        assert data["side"] == "con"

    def test_description_is_loaded(self):
        skill = CounterSkill()
        assert "AGAINST" in skill.description

    def test_raises_on_missing_topic(self):
        skill = CounterSkill()
        with pytest.raises(ValueError, match="topic"):
            skill.execute({"round": 1})

    def test_raises_on_missing_opponent_after_round_1(self):
        skill = CounterSkill()
        with pytest.raises(ValueError, match="opponent_argument"):
            skill.execute({"topic": "AI is good", "round": 2})

    def test_round_1_works_without_opponent(self):
        skill = CounterSkill()
        result = skill.execute({"topic": "AI is good", "round": 1})
        data = json.loads(result)
        assert data["side"] == "con"

    def test_references_opponent_in_prompt(self):
        skill = CounterSkill()
        result = skill.execute({
            "topic": "AI is good",
            "round": 3,
            "opponent_argument": "AI saves lives",
        })
        data = json.loads(result)
        assert "opponent" in data["user"].lower() or "argued" in data["user"].lower()
