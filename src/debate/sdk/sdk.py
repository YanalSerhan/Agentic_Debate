"""DebateSDK — single public entry point for the debate system.

All consumers (CLI, tests, future GUI) must use this class
to interact with the debate system. No internal modules should
be imported directly by consumers.
"""

from __future__ import annotations

from typing import Any

from debate.agents.con_agent import ConAgent
from debate.agents.judge_agent import JudgeAgent
from debate.agents.pro_agent import ProAgent
from debate.shared.config import ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.logger import StructuredLogger


class SecurityError(Exception):
    """Raised when malicious input is detected."""

class DebateSDK:
    """Single entry point for running AI debates.

    Args:
        config_path: Path to the directory containing JSON config files.
    """

    def __init__(self, config_path: str = "config") -> None:
        self._config = ConfigManager(config_path)
        self._logger = StructuredLogger(
            log_dir=self._config.get_log_dir(),
            max_lines=self._config.get_log_max_lines(),
            max_files=self._config.get_log_max_files(),
        )
        self._gatekeeper = ApiGatekeeper(
            rate_limits=self._config.get_rate_limits(),
            budget_cap=self._config.get_budget_cap(),
            logger=self._logger,
        )
        self._pro_agent = ProAgent(
            gatekeeper=self._gatekeeper,
            logger=self._logger,
            model=self._config.get_model(),
            max_tokens=self._config.get_max_tokens(),
            api_timeout=self._config.get_api_timeout(),
        )
        self._con_agent = ConAgent(
            gatekeeper=self._gatekeeper,
            logger=self._logger,
            model=self._config.get_model(),
            max_tokens=self._config.get_max_tokens(),
            api_timeout=self._config.get_api_timeout(),
        )
        self._judge_agent = JudgeAgent(
            pro_agent=self._pro_agent,
            con_agent=self._con_agent,
            gatekeeper=self._gatekeeper,
            logger=self._logger,
            max_rounds=self._config.get_max_rounds(),
            model=self._config.get_model(),
            max_tokens=self._config.get_max_tokens(),
            api_timeout=self._config.get_api_timeout(),
        )
        self._last_verdict: str | None = None

    def _sanitize_topic(self, topic: str) -> None:
        """Scan topic for malicious prompt injection or shell commands."""
        malicious_keywords = [
            "rm -rf", "sudo", "ignore previous instructions", "system prompt",
            "chmod", "rm ", "delete file", "delete directory", "os.system"
        ]
        topic_lower = topic.lower()
        for keyword in malicious_keywords:
            if keyword in topic_lower:
                self._logger.warning("sdk", "security_alert", {"topic": topic})
                msg = f"Security Error: Malicious input detected ('{keyword}')"
                raise SecurityError(msg)

    def run_debate(self, topic: str, rounds: int | None = None) -> dict[str, Any]:
        """Run a full debate on the given topic.

        Args:
            topic: The debate topic string.
            rounds: Override max_rounds from config (optional).

        Returns:
            Parsed VerdictMessage as a dict.
        """
        self._sanitize_topic(topic)

        if rounds is not None:
            self._judge_agent._max_rounds = rounds

        import json
        self._logger.info("sdk", "debate_initiated", {"topic": topic})
        verdict_json = self._judge_agent.run({"topic": topic})
        self._last_verdict = verdict_json
        return json.loads(verdict_json)

    def get_transcript(self) -> list[dict]:
        """Return the full debate transcript."""
        return self._judge_agent.transcript

    def get_cost_report(self) -> dict[str, Any]:
        """Return API usage and cost breakdown."""
        return self._gatekeeper.get_cost_report()

    def get_log_path(self) -> str:
        """Return the path to the current log file."""
        log_file = self._logger.get_current_file()
        return str(log_file) if log_file else ""

    def close(self) -> None:
        """Clean up resources."""
        self._logger.close()
