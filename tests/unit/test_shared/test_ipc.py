"""Tests for debate.shared.ipc — message schemas and validation."""

import json

import pytest
from pydantic import ValidationError

from debate.constants import AgentRole
from debate.shared.ipc import (
    DebateTurnMessage,
    JudgeRelayMessage,
    VerdictMessage,
    validate_message,
)


class TestDebateTurnMessage:
    """Tests for DebateTurnMessage schema."""

    def test_valid_creation(self):
        msg = DebateTurnMessage(
            round=1, speaker=AgentRole.PRO,
            argument="AI is beneficial", sources=["https://example.com"]
        )
        assert msg.round == 1
        assert msg.speaker == AgentRole.PRO
        assert msg.argument == "AI is beneficial"
        assert len(msg.sources) == 1

    def test_speaker_must_be_debater(self):
        with pytest.raises(ValidationError):
            DebateTurnMessage(
                round=1, speaker=AgentRole.JUDGE,
                argument="test", sources=["https://example.com"]
            )

    def test_empty_argument_rejected(self):
        with pytest.raises(ValidationError):
            DebateTurnMessage(
                round=1, speaker=AgentRole.PRO,
                argument="", sources=["https://example.com"]
            )

    def test_empty_sources_rejected(self):
        with pytest.raises(ValidationError):
            DebateTurnMessage(
                round=1, speaker=AgentRole.PRO,
                argument="test argument", sources=[]
            )

    def test_round_must_be_positive(self):
        with pytest.raises(ValidationError):
            DebateTurnMessage(
                round=0, speaker=AgentRole.PRO,
                argument="test", sources=["https://example.com"]
            )


class TestJudgeRelayMessage:
    """Tests for JudgeRelayMessage schema."""

    def test_valid_relay(self):
        turn = DebateTurnMessage(
            round=1, speaker=AgentRole.PRO,
            argument="test", sources=["https://example.com"]
        )
        relay = JudgeRelayMessage(
            from_agent=AgentRole.PRO, to_agent=AgentRole.CON, payload=turn
        )
        assert relay.from_agent == AgentRole.PRO
        assert relay.to_agent == AgentRole.CON
        assert relay.payload.argument == "test"


class TestVerdictMessage:
    """Tests for VerdictMessage schema."""

    def test_valid_verdict(self):
        verdict = VerdictMessage(
            winner=AgentRole.PRO,
            reasoning="Pro was more persuasive",
            score={"pro": 8, "con": 6},
        )
        assert verdict.winner == AgentRole.PRO
        assert verdict.reasoning == "Pro was more persuasive"

    def test_winner_cannot_be_judge(self):
        with pytest.raises(ValidationError):
            VerdictMessage(
                winner=AgentRole.JUDGE,
                reasoning="test", score={"pro": 5, "con": 5},
            )

    def test_score_must_have_both_keys(self):
        with pytest.raises(ValidationError):
            VerdictMessage(
                winner=AgentRole.PRO,
                reasoning="test", score={"pro": 8},
            )

    def test_empty_reasoning_rejected(self):
        with pytest.raises(ValidationError):
            VerdictMessage(
                winner=AgentRole.PRO,
                reasoning="", score={"pro": 8, "con": 6},
            )

    def test_verdict_is_never_tie(self):
        """Verdict winner must be explicitly pro or con."""
        verdict = VerdictMessage(
            winner=AgentRole.PRO,
            reasoning="test", score={"pro": 7, "con": 7},
        )
        assert verdict.winner in (AgentRole.PRO, AgentRole.CON)


class TestValidateMessage:
    """Tests for the validate_message() function."""

    def test_validates_debate_turn(self):
        raw = json.dumps({
            "round": 1, "speaker": "pro",
            "argument": "AI is good", "sources": ["https://example.com"],
        })
        msg = validate_message(raw)
        assert isinstance(msg, DebateTurnMessage)

    def test_validates_verdict(self):
        raw = json.dumps({
            "winner": "pro", "reasoning": "Better arguments",
            "score": {"pro": 8, "con": 6},
        })
        msg = validate_message(raw)
        assert isinstance(msg, VerdictMessage)

    def test_validates_judge_relay(self):
        raw = json.dumps({
            "from_agent": "pro", "to_agent": "con",
            "payload": {
                "round": 1, "speaker": "pro",
                "argument": "test", "sources": ["https://example.com"],
            },
        })
        msg = validate_message(raw)
        assert isinstance(msg, JudgeRelayMessage)

    def test_rejects_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            validate_message("not json")

    def test_rejects_non_object(self):
        with pytest.raises(ValueError, match="must be a JSON object"):
            validate_message('"just a string"')

    def test_rejects_unknown_schema(self):
        with pytest.raises(ValueError):
            validate_message(json.dumps({"unknown": "data"}))
