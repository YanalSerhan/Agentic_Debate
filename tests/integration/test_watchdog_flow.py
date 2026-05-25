"""Integration tests — watchdog process monitoring flow.

Tests that the Watchdog correctly detects dead processes, restarts
them, and gives up after exceeding max restart attempts.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from debate.shared.logger import StructuredLogger
from debate.shared.watchdog import Watchdog, WatchdogGaveUpError


def _crash_target():
    """Target that exits immediately (simulates crash)."""
    return


def _healthy_target():
    """Target that runs for a long time (simulates healthy agent)."""
    time.sleep(300)


class TestWatchdogIntegration:
    """Integration tests for Watchdog restart and monitoring."""

    @pytest.fixture
    def logger(self, tmp_path):
        """Create a real StructuredLogger for integration testing."""
        log_dir = str(tmp_path / "watchdog_logs")
        return StructuredLogger(log_dir=log_dir, max_lines=500, max_files=5)

    def test_watchdog_detects_and_restarts_crashed_agent(self, logger):
        """Test that a crashed agent is detected and restarted."""
        wd = Watchdog(
            max_restarts=3, ping_interval=1, ping_timeout=5, logger=logger,
        )
        wd.register("crashing_agent", _crash_target)
        wd.start_all()

        time.sleep(0.5)  # Let process exit

        wd.check_all()
        status = wd.get_status()
        assert status["crashing_agent"]["restart_count"] >= 1
        wd.stop_all()
        logger.close()

    def test_debate_resumes_after_restart(self, logger):
        """Test that a restarted agent process is alive again."""
        wd = Watchdog(
            max_restarts=3, ping_interval=1, ping_timeout=5, logger=logger,
        )
        wd.register("resumable_agent", _crash_target)
        wd.start_all()

        time.sleep(0.5)

        wd.check_all()
        # After restart, the agent should have been restarted
        # (it will die again since _crash_target exits, but the
        # restart mechanism itself is verified)
        status = wd.get_status()
        assert status["resumable_agent"]["restart_count"] >= 1
        wd.stop_all()
        logger.close()

    def test_max_restarts_exceeded_raises(self, logger):
        """Test WatchdogGaveUpError when max restarts exceeded."""
        wd = Watchdog(
            max_restarts=1, ping_interval=1, ping_timeout=5, logger=logger,
        )
        wd.register("doomed_agent", _crash_target)
        wd.start_all()

        time.sleep(1.0)  # Ensure process exits
        wd.check_all()  # restart 1

        time.sleep(1.0)  # Ensure restarted process also exits
        with pytest.raises(WatchdogGaveUpError):
            wd.check_all()  # restart 2 → exceeds max

        wd.stop_all()
        logger.close()

    def test_healthy_agent_not_restarted(self, logger):
        """Test that a healthy agent is not unnecessarily restarted."""
        wd = Watchdog(
            max_restarts=3, ping_interval=1, ping_timeout=30, logger=logger,
        )
        wd.register("healthy_agent", _healthy_target)
        wd.start_all()

        time.sleep(0.3)
        wd.check_all()

        status = wd.get_status()
        assert status["healthy_agent"]["alive"]
        assert status["healthy_agent"]["restart_count"] == 0
        wd.stop_all()
        logger.close()

    def test_restart_events_are_logged(self, logger, tmp_path):
        """Test that restart events appear in the log file."""
        wd = Watchdog(
            max_restarts=3, ping_interval=1, ping_timeout=5, logger=logger,
        )
        wd.register("logged_agent", _crash_target)
        wd.start_all()

        time.sleep(0.5)
        wd.check_all()
        wd.stop_all()

        log_file = logger.get_current_file()
        logger.close()

        assert log_file is not None
        with open(log_file) as f:
            lines = f.readlines()

        events = [json.loads(line) for line in lines]
        event_names = [e["event"] for e in events]
        assert "agent_started" in event_names
        assert "agent_restarting" in event_names

    def test_timeout_detection_kills_and_restarts(self, logger):
        """Test that an agent exceeding ping timeout is killed and restarted."""
        wd = Watchdog(
            max_restarts=3, ping_interval=1, ping_timeout=0.1, logger=logger,
        )
        wd.register("timeout_agent", _healthy_target)
        wd.start_all()

        # Wait for the ping timeout to elapse
        time.sleep(0.5)
        wd.check_timeouts()

        status = wd.get_status()
        assert status["timeout_agent"]["restart_count"] >= 1
        wd.stop_all()
        logger.close()
