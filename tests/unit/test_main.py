"""Tests for src/main.py — CLI entry point."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestMainCLI:
    """Tests for the main CLI entry point."""

    def test_parse_args_topic(self):
        """Test that --topic is parsed correctly."""
        from main import parse_args

        with patch("sys.argv", ["main.py", "--topic", "Is AI good?"]):
            args = parse_args()
        assert args.topic == "Is AI good?"
        assert args.rounds is None
        assert args.config == "config"

    def test_parse_args_all_options(self):
        """Test that --rounds and --config are parsed correctly."""
        from main import parse_args

        with patch("sys.argv", [
            "main.py", "--topic", "AI", "--rounds", "5", "--config", "/tmp/cfg"
        ]):
            args = parse_args()
        assert args.topic == "AI"
        assert args.rounds == 5
        assert args.config == "/tmp/cfg"

    def test_main_success(self, capsys):
        """Test main() returns 0 on success."""
        from main import main

        mock_verdict = {
            "winner": "pro",
            "reasoning": "Pro was more persuasive",
            "score": {"pro": 8, "con": 6},
        }
        mock_cost = {
            "total_input_tokens": 1000,
            "total_output_tokens": 500,
            "total_cost_usd": 0.0105,
            "budget_cap_usd": 5.0,
            "budget_remaining_usd": 4.9895,
        }

        mock_sdk = MagicMock()
        mock_sdk.run_debate.return_value = mock_verdict
        mock_sdk.get_cost_report.return_value = mock_cost
        mock_sdk.get_log_path.return_value = "results/logs/test.jsonl"

        with patch("sys.argv", [
            "main.py", "--topic", "AI is good", "--config", "config"
        ]), patch("debate.sdk.sdk.DebateSDK", return_value=mock_sdk):
            result = main()

        assert result == 0
        output = capsys.readouterr().out
        assert "PRO" in output
        assert "VERDICT" in output

    def test_main_error_returns_1(self, capsys):
        """Test main() returns 1 on error."""
        from main import main

        with patch("sys.argv", [
            "main.py", "--topic", "AI", "--config", "config"
        ]), patch(
            "debate.sdk.sdk.DebateSDK",
            side_effect=Exception("Test error"),
        ):
            result = main()

        assert result == 1

    def test_main_keyboard_interrupt(self, capsys):
        """Test main() handles KeyboardInterrupt gracefully."""
        from main import main

        with patch("sys.argv", [
            "main.py", "--topic", "AI", "--config", "config"
        ]), patch(
            "debate.sdk.sdk.DebateSDK",
            side_effect=KeyboardInterrupt(),
        ):
            result = main()

        assert result == 1
        output = capsys.readouterr().out
        assert "interrupted" in output.lower()
