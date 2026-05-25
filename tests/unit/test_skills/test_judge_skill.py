"""Tests for debate.skills.judge_skill — JudgeSkill."""

import json

import pytest

from debate.skills.judge_skill.judge_skill import JudgeSkill


class TestJudgeSkill:
    """Tests for JudgeSkill."""

    def _sample_transcript(self):
        return [
            {"round": 1, "speaker": "pro", "argument": "AI helps", "sources": ["https://a.com"]},
            {"round": 1, "speaker": "con", "argument": "AI harms", "sources": ["https://b.com"]},
        ]

    def test_execute_returns_prompt(self):
        skill = JudgeSkill()
        result = skill.execute({
            "topic": "AI is good",
            "transcript": self._sample_transcript(),
        })
        data = json.loads(result)
        assert "system" in data
        assert "user" in data

    def test_description_is_loaded(self):
        skill = JudgeSkill()
        assert "verdict" in skill.description.lower()

    def test_raises_on_missing_topic(self):
        skill = JudgeSkill()
        with pytest.raises(ValueError, match="topic"):
            skill.execute({"transcript": self._sample_transcript()})

    def test_raises_on_missing_transcript(self):
        skill = JudgeSkill()
        with pytest.raises(ValueError, match="transcript"):
            skill.execute({"topic": "AI is good"})

    def test_raises_on_empty_transcript(self):
        skill = JudgeSkill()
        with pytest.raises(ValueError, match="transcript"):
            skill.execute({"topic": "AI is good", "transcript": []})

    def test_system_prompt_forbids_tie(self):
        skill = JudgeSkill()
        result = skill.execute({
            "topic": "AI is good",
            "transcript": self._sample_transcript(),
        })
        data = json.loads(result)
        assert "tie" in data["system"].lower() or "forbidden" in data["system"].lower()

    def test_system_prompt_scores_persuasion(self):
        skill = JudgeSkill()
        result = skill.execute({
            "topic": "AI is good",
            "transcript": self._sample_transcript(),
        })
        data = json.loads(result)
        assert "persuasive" in data["system"].lower()

    def test_transcript_is_included_in_user_prompt(self):
        skill = JudgeSkill()
        result = skill.execute({
            "topic": "AI is good",
            "transcript": self._sample_transcript(),
        })
        data = json.loads(result)
        assert "AI helps" in data["user"]
        assert "AI harms" in data["user"]
