"""Immutable project constants and enumerations.

All enum values used across the debate system are defined here.
Runtime-configurable values (max_rounds, timeouts, etc.) are loaded
via ConfigManager — never hardcoded in this module.
"""

from enum import Enum


class AgentRole(str, Enum):
    """Roles that an agent can assume in the debate."""

    PRO = "pro"
    CON = "con"
    JUDGE = "judge"


class MessageType(str, Enum):
    """Types of structured messages exchanged between agents."""

    DEBATE_TURN = "debate_turn"
    JUDGE_RELAY = "judge_relay"
    VERDICT = "verdict"


class DebateStatus(str, Enum):
    """Status of the overall debate."""

    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
