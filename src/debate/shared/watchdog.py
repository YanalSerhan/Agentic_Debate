"""Watchdog — monitors agent processes and restarts them on failure.

Sends keep-alive pings at configurable intervals. If a process
fails to respond within the timeout, it is killed and restarted.
"""

from __future__ import annotations

import multiprocessing
import time
from collections.abc import Callable
from typing import Any

from debate.shared.logger import StructuredLogger


class WatchdogGaveUpError(Exception):
    """Raised when the watchdog exceeds max restart attempts for an agent."""


class AgentProcess:
    """Tracks a single monitored agent process.

    Args:
        name: Human-readable agent name.
        target: The callable to run in the process.
        args: Arguments for the target callable.
    """

    def __init__(self, name: str, target: Callable, args: tuple = ()) -> None:
        self.name = name
        self.target = target
        self.args = args
        self.process: multiprocessing.Process | None = None
        self.restart_count = 0
        self.last_ping: float = 0.0

    def start(self) -> None:
        """Start or restart the agent process."""
        self.process = multiprocessing.Process(
            target=self.target, args=self.args, name=self.name, daemon=True
        )
        self.process.start()
        self.last_ping = time.time()

    def is_alive(self) -> bool:
        """Check if the process is still running."""
        return self.process is not None and self.process.is_alive()

    def kill(self) -> None:
        """Terminate the process forcefully."""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)


class Watchdog:
    """Monitors agent sub-processes and restarts them on failure.

    Args:
        max_restarts: Max restart attempts per agent before giving up.
        ping_interval: Seconds between keep-alive checks.
        ping_timeout: Seconds before a non-responsive agent is killed.
        logger: StructuredLogger for logging restart events.
    """

    def __init__(
        self,
        max_restarts: int = 3,
        ping_interval: int = 10,
        ping_timeout: int = 30,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._max_restarts = max_restarts
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._logger = logger
        self._agents: dict[str, AgentProcess] = {}

    def register(self, name: str, target: Callable, args: tuple = ()) -> None:
        """Register an agent process to be monitored."""
        self._agents[name] = AgentProcess(name, target, args)

    def start_all(self) -> None:
        """Start all registered agent processes."""
        for agent in self._agents.values():
            agent.start()
            if self._logger:
                self._logger.info("watchdog", "agent_started", {"agent": agent.name})

    def check_all(self) -> None:
        """Check all agents and restart any that have died."""
        for agent in self._agents.values():
            if not agent.is_alive():
                self._handle_dead_agent(agent)

    def update_ping(self, name: str) -> None:
        """Record a keep-alive ping from an agent."""
        if name in self._agents:
            self._agents[name].last_ping = time.time()

    def check_timeouts(self) -> None:
        """Kill and restart agents that haven't pinged within timeout."""
        now = time.time()
        for agent in self._agents.values():
            if agent.is_alive() and (now - agent.last_ping) > self._ping_timeout:
                if self._logger:
                    self._logger.warning("watchdog", "agent_timeout", {
                        "agent": agent.name,
                        "last_ping_seconds_ago": round(now - agent.last_ping, 1),
                    })
                agent.kill()
                self._handle_dead_agent(agent)

    def _handle_dead_agent(self, agent: AgentProcess) -> None:
        """Restart a dead agent or raise if max restarts exceeded."""
        agent.restart_count += 1
        if agent.restart_count > self._max_restarts:
            if self._logger:
                self._logger.error("watchdog", "agent_gave_up", {
                    "agent": agent.name,
                    "restart_count": agent.restart_count,
                })
            msg = (
                f"Agent '{agent.name}' exceeded max restarts "
                f"({self._max_restarts})"
            )
            raise WatchdogGaveUpError(msg)

        if self._logger:
            self._logger.warning("watchdog", "agent_restarting", {
                "agent": agent.name,
                "restart_count": agent.restart_count,
            })
        agent.start()

    def stop_all(self) -> None:
        """Stop all monitored agent processes."""
        for agent in self._agents.values():
            agent.kill()
            if self._logger:
                self._logger.info("watchdog", "agent_stopped", {"agent": agent.name})

    def get_status(self) -> dict[str, Any]:
        """Return status of all monitored agents."""
        return {
            name: {
                "alive": agent.is_alive(),
                "restart_count": agent.restart_count,
                "pid": agent.process.pid if agent.process else None,
            }
            for name, agent in self._agents.items()
        }
