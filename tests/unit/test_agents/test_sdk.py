"""Tests for debate.sdk.sdk — DebateSDK."""

import json
from unittest.mock import MagicMock

from debate.sdk.sdk import DebateSDK


class TestDebateSDK:
    """Tests for the DebateSDK entry point."""

    def test_sdk_initializes(self, config_dir):
        sdk = DebateSDK(config_path=config_dir)
        assert sdk is not None
        sdk.close()

    def test_run_debate_returns_verdict(self, config_dir):
        sdk = DebateSDK(config_path=config_dir)

        # Mock the judge agent's run method
        mock_verdict = {
            "winner": "pro",
            "reasoning": "Pro was more persuasive",
            "score": {"pro": 8, "con": 6},
        }
        sdk._judge_agent.run = MagicMock(return_value=json.dumps(mock_verdict))

        result = sdk.run_debate(topic="AI is good")
        assert result["winner"] == "pro"
        assert "reasoning" in result
        assert "score" in result
        sdk.close()

    def test_get_transcript(self, config_dir):
        sdk = DebateSDK(config_path=config_dir)
        # Before running, transcript should be empty
        assert sdk.get_transcript() == []
        sdk.close()

    def test_get_cost_report(self, config_dir):
        sdk = DebateSDK(config_path=config_dir)
        report = sdk.get_cost_report()
        assert "total_input_tokens" in report
        assert "total_cost_usd" in report
        sdk.close()

    def test_get_log_path(self, config_dir):
        sdk = DebateSDK(config_path=config_dir)
        log_path = sdk.get_log_path()
        assert log_path.endswith(".jsonl")
        sdk.close()

    def test_run_debate_with_custom_rounds(self, config_dir):
        sdk = DebateSDK(config_path=config_dir)

        mock_verdict = {
            "winner": "con",
            "reasoning": "Con won",
            "score": {"pro": 4, "con": 8},
        }
        sdk._judge_agent.run = MagicMock(return_value=json.dumps(mock_verdict))

        result = sdk.run_debate(topic="AI", rounds=5)
        assert result["winner"] == "con"
        sdk.close()
