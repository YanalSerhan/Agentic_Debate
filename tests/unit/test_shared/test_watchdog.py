"""Tests for debate.shared.watchdog — Watchdog process monitor."""

import time

import pytest

from debate.shared.watchdog import AgentProcess, Watchdog, WatchdogGaveUpError


def _dummy_target():
    """A dummy target that exits immediately."""
    pass


def _long_target():
    """A target that runs for a while."""
    time.sleep(60)


class TestAgentProcess:
    """Tests for AgentProcess wrapper."""

    def test_start_creates_process(self):
        agent = AgentProcess("test", _dummy_target)
        agent.start()
        assert agent.process is not None
        time.sleep(0.2)  # Let it finish

    def test_is_alive_for_running_process(self):
        agent = AgentProcess("test", _long_target)
        agent.start()
        assert agent.is_alive()
        agent.kill()

    def test_kill_stops_process(self):
        agent = AgentProcess("test", _long_target)
        agent.start()
        agent.kill()
        time.sleep(0.2)
        assert not agent.is_alive()


class TestWatchdog:
    """Tests for the Watchdog monitor."""

    def test_detects_dead_process(self):
        wd = Watchdog(max_restarts=3, ping_interval=1, ping_timeout=5)
        wd.register("test", _dummy_target)
        wd.start_all()
        time.sleep(0.5)  # Let the dummy finish
        # Should detect it's dead and restart
        wd.check_all()
        status = wd.get_status()
        assert status["test"]["restart_count"] >= 1
        wd.stop_all()

    def test_max_restart_raises(self):
        wd = Watchdog(max_restarts=1, ping_interval=1, ping_timeout=5)
        wd.register("test", _dummy_target)
        wd.start_all()
        time.sleep(1.0)  # Ensure process exits
        wd.check_all()  # restart 1
        time.sleep(1.0)  # Ensure restarted process also exits
        with pytest.raises(WatchdogGaveUpError):
            wd.check_all()  # restart 2 → exceeds max
        wd.stop_all()

    def test_keep_alive_ping(self):
        wd = Watchdog(max_restarts=3, ping_interval=1, ping_timeout=5)
        wd.register("test", _long_target)
        wd.start_all()
        wd.update_ping("test")
        status = wd.get_status()
        assert status["test"]["alive"]
        wd.stop_all()

    def test_get_status(self):
        wd = Watchdog(max_restarts=3)
        wd.register("agent_a", _long_target)
        wd.start_all()
        status = wd.get_status()
        assert "agent_a" in status
        assert "alive" in status["agent_a"]
        assert "restart_count" in status["agent_a"]
        wd.stop_all()
