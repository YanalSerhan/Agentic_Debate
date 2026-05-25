"""Tests for debate.agents.judge_agent — JudgeAgent."""

import json
from unittest.mock import MagicMock

from debate.agents.judge_agent import JudgeAgent
from debate.constants import AgentRole


def _make_mock_debater(speaker: str, argument: str = "test argument"):
    """Create a mock debater agent."""
    agent = MagicMock()
    agent.role = AgentRole(speaker)

    def mock_run(context):
        return json.dumps({
            "round": context.get("round", 1),
            "speaker": speaker,
            "argument": argument,
            "sources": ["https://example.com"],
        })

    agent.run = MagicMock(side_effect=mock_run)
    return agent


def _make_verdict_gatekeeper(mock_gatekeeper, winner="pro", pro_score=8, con_score=6):
    """Configure mock gatekeeper to return a verdict response."""
    verdict_response = MagicMock()
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = json.dumps({
        "winner": winner,
        "reasoning": f"{winner.title()} was more persuasive",
        "score": {"pro": pro_score, "con": con_score},
    })
    verdict_response.content = [text_block]
    verdict_response.usage.input_tokens = 200
    verdict_response.usage.output_tokens = 100
    mock_gatekeeper.execute = MagicMock(return_value=verdict_response)
    return mock_gatekeeper


class TestJudgeAgent:
    """Tests for JudgeAgent orchestration."""

    def test_all_messages_routed_through_judge(self, mock_gatekeeper, mock_logger):
        pro = _make_mock_debater("pro", "Pro argument")
        con = _make_mock_debater("con", "Con argument")
        gk = _make_verdict_gatekeeper(mock_gatekeeper)

        judge = JudgeAgent(
            pro_agent=pro, con_agent=con,
            gatekeeper=gk, logger=mock_logger,
            max_rounds=2,
        )
        json.loads(judge.run({"topic": "AI is good"}))

        # Pro and con should have been called through judge
        assert pro.run.call_count == 2
        assert con.run.call_count == 2

    def test_judge_relays_pro_to_con(self, mock_gatekeeper, mock_logger):
        pro = _make_mock_debater("pro", "Pro argument")
        con = _make_mock_debater("con", "Con argument")
        gk = _make_verdict_gatekeeper(mock_gatekeeper, "con", 5, 7)

        judge = JudgeAgent(
            pro_agent=pro, con_agent=con,
            gatekeeper=gk, logger=mock_logger,
            max_rounds=1,
        )
        judge.run({"topic": "AI is good"})

        # Con should receive pro's argument in context
        con_call_args = con.run.call_args[0][0]
        assert "opponent_argument" in con_call_args

    def test_verdict_is_never_tie(self, mock_gatekeeper, mock_logger):
        pro = _make_mock_debater("pro")
        con = _make_mock_debater("con")
        gk = _make_verdict_gatekeeper(mock_gatekeeper, "pro", 9, 4)

        judge = JudgeAgent(
            pro_agent=pro, con_agent=con,
            gatekeeper=gk, logger=mock_logger,
            max_rounds=1,
        )
        result = json.loads(judge.run({"topic": "AI"}))

        assert result["winner"] in ("pro", "con")

    def test_delivers_verdict_after_max_rounds(self, mock_gatekeeper, mock_logger):
        pro = _make_mock_debater("pro")
        con = _make_mock_debater("con")
        gk = _make_verdict_gatekeeper(mock_gatekeeper, "con", 6, 7)

        max_rounds = 3
        judge = JudgeAgent(
            pro_agent=pro, con_agent=con,
            gatekeeper=gk, logger=mock_logger,
            max_rounds=max_rounds,
        )
        result = json.loads(judge.run({"topic": "AI"}))

        assert pro.run.call_count == max_rounds
        assert con.run.call_count == max_rounds
        assert result["winner"] in ("pro", "con")

    def test_transcript_is_built(self, mock_gatekeeper, mock_logger):
        pro = _make_mock_debater("pro")
        con = _make_mock_debater("con")
        gk = _make_verdict_gatekeeper(mock_gatekeeper)

        judge = JudgeAgent(
            pro_agent=pro, con_agent=con,
            gatekeeper=gk, logger=mock_logger,
            max_rounds=2,
        )
        judge.run({"topic": "AI"})

        transcript = judge.transcript
        assert len(transcript) == 4  # 2 rounds × 2 turns
