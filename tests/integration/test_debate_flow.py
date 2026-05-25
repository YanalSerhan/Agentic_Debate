"""Integration tests — full debate flow with mocked Anthropic API.

Verifies end-to-end behaviour: debate runs, rounds complete,
verdict is produced, logs are written, gatekeeper is invoked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from debate.sdk.sdk import DebateSDK


def _build_mock_api_response(text: str, urls: list[str] | None = None):
    """Create a mock Anthropic Messages response."""
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text

    content = [text_block]
    if urls:
        search_block = MagicMock()
        search_block.type = "web_search_tool_result"
        results = []
        for url in urls:
            r = MagicMock()
            r.url = url
            results.append(r)
        search_block.search_results = results
        content.append(search_block)

    response = MagicMock()
    response.content = content
    response.usage = MagicMock()
    response.usage.input_tokens = 150
    response.usage.output_tokens = 80
    return response


def _build_verdict_response(winner="pro", pro_score=8, con_score=6):
    """Create a verdict API response."""
    verdict = {
        "winner": winner,
        "reasoning": f"{winner.upper()} demonstrated superior persuasive ability",
        "score": {"pro": pro_score, "con": con_score},
    }
    return _build_mock_api_response(json.dumps(verdict))


class TestFullDebateFlow:
    """End-to-end debate flow tests with mocked API."""

    @pytest.fixture
    def config_dir(self, tmp_path):
        """Create a temporary config directory."""
        config_path = tmp_path / "config"
        config_path.mkdir()

        setup = {
            "version": "1.00",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "debate_topic": "",
            "max_rounds": 10,
            "api_timeout_seconds": 60,
            "max_restart_attempts": 3,
            "keepalive_interval_seconds": 10,
            "keepalive_timeout_seconds": 30,
            "budget_cap_usd": 5.0,
        }
        (config_path / "setup.json").write_text(json.dumps(setup))

        rate_limits = {
            "version": "1.00",
            "services": {
                "default": {
                    "requests_per_minute": 1000,
                    "requests_per_hour": 10000,
                    "concurrent_max": 100,
                    "retry_after_seconds": 0.01,
                    "max_retries": 3,
                    "max_queue_depth": 50,
                }
            },
        }
        (config_path / "rate_limits.json").write_text(json.dumps(rate_limits))

        logging_config = {
            "version": "1.00",
            "max_files": 20,
            "max_lines_per_file": 500,
            "log_dir": str(tmp_path / "logs"),
            "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
        }
        (config_path / "logging_config.json").write_text(json.dumps(logging_config))

        return str(config_path)

    def _setup_sdk_with_mock(self, config_dir, max_rounds=10):
        """Create SDK and wire up mock gatekeeper responses."""
        sdk = DebateSDK(config_path=config_dir)

        if max_rounds is not None:
            sdk._judge_agent._max_rounds = max_rounds

        call_counter = {"n": 0}
        total_api_calls = max_rounds * 2 + 1  # pro + con per round, plus verdict

        def mock_execute(api_call, *args, **kwargs):
            call_counter["n"] += 1
            if call_counter["n"] == total_api_calls:
                return _build_verdict_response("pro", 8, 6)
            return _build_mock_api_response(
                f"Argument #{call_counter['n']}",
                urls=[f"https://source{call_counter['n']}.com"],
            )

        sdk._gatekeeper.execute = MagicMock(side_effect=mock_execute)
        return sdk, call_counter

    def test_full_debate_end_to_end(self, config_dir):
        """Test that a complete debate runs and produces a verdict."""
        rounds = 3
        sdk, counter = self._setup_sdk_with_mock(config_dir, max_rounds=rounds)

        verdict = sdk.run_debate(topic="Is AI good for humanity?")

        assert verdict["winner"] in ("pro", "con")
        assert "reasoning" in verdict
        assert "score" in verdict
        assert "pro" in verdict["score"]
        assert "con" in verdict["score"]
        sdk.close()

    def test_minimum_rounds_completed(self, config_dir):
        """Test that the configured number of rounds are completed."""
        rounds = 5
        sdk, counter = self._setup_sdk_with_mock(config_dir, max_rounds=rounds)

        sdk.run_debate(topic="Is AI good for humanity?")

        transcript = sdk.get_transcript()
        assert len(transcript) == rounds * 2  # pro + con each round
        sdk.close()

    def test_verdict_is_not_tie(self, config_dir):
        """Test that the judge always picks a winner (never tie)."""
        sdk, _ = self._setup_sdk_with_mock(config_dir, max_rounds=2)
        verdict = sdk.run_debate(topic="AI topic")

        assert verdict["winner"] in ("pro", "con")
        assert verdict["winner"] != "judge"
        sdk.close()

    def test_all_messages_are_valid_json(self, config_dir):
        """Test that every transcript entry is valid JSON with required keys."""
        sdk, _ = self._setup_sdk_with_mock(config_dir, max_rounds=2)
        sdk.run_debate(topic="AI topic")

        for turn in sdk.get_transcript():
            assert "round" in turn
            assert "speaker" in turn
            assert "argument" in turn
            assert "sources" in turn
            assert turn["speaker"] in ("pro", "con")
            assert isinstance(turn["sources"], list)
            assert len(turn["sources"]) >= 1
        sdk.close()

    def test_logs_are_written(self, config_dir, tmp_path):
        """Test that log files are created during the debate."""
        sdk, _ = self._setup_sdk_with_mock(config_dir, max_rounds=2)
        sdk.run_debate(topic="AI topic")

        log_path = sdk.get_log_path()
        assert log_path.endswith(".jsonl")
        assert Path(log_path).exists()

        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) > 0

        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "level" in entry
            assert "event" in entry
        sdk.close()

    def test_cost_report_is_generated(self, config_dir):
        """Test that a cost report is available after the debate."""
        sdk, _ = self._setup_sdk_with_mock(config_dir, max_rounds=2)
        sdk.run_debate(topic="AI topic")

        report = sdk.get_cost_report()
        assert "total_input_tokens" in report
        assert "total_output_tokens" in report
        assert "total_cost_usd" in report
        assert "budget_cap_usd" in report
        assert "budget_remaining_usd" in report
        sdk.close()

    def test_gatekeeper_invoked_for_every_api_call(self, config_dir):
        """Test that every API call goes through the gatekeeper."""
        rounds = 2
        sdk, _ = self._setup_sdk_with_mock(config_dir, max_rounds=rounds)
        sdk.run_debate(topic="AI topic")

        expected_calls = rounds * 2 + 1  # pro + con per round, plus verdict
        assert sdk._gatekeeper.execute.call_count == expected_calls
        sdk.close()

    def test_transcript_alternates_pro_con(self, config_dir):
        """Test that transcript correctly alternates pro and con turns."""
        sdk, _ = self._setup_sdk_with_mock(config_dir, max_rounds=3)
        sdk.run_debate(topic="AI topic")

        transcript = sdk.get_transcript()
        for i, turn in enumerate(transcript):
            expected_speaker = "pro" if i % 2 == 0 else "con"
            assert turn["speaker"] == expected_speaker
        sdk.close()

    def test_debate_with_custom_rounds(self, config_dir):
        """Test that custom round count is respected."""
        sdk, _ = self._setup_sdk_with_mock(config_dir, max_rounds=3)
        verdict = sdk.run_debate(topic="AI topic", rounds=3)

        transcript = sdk.get_transcript()
        assert len(transcript) == 6  # 3 rounds × 2 turns
        assert verdict["winner"] in ("pro", "con")
        sdk.close()
