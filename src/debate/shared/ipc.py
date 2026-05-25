"""JSON message schemas and validation for inter-agent communication.

All messages between agents are Pydantic v2 models validated here.
Three message types: DebateTurnMessage, JudgeRelayMessage, VerdictMessage.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, field_validator

from debate.constants import AgentRole


class DebateTurnMessage(BaseModel):
    """A single debate turn produced by ProAgent or ConAgent."""

    round: int = Field(ge=1, description="Round number (1-indexed)")
    speaker: AgentRole = Field(description="Which agent produced this turn")
    argument: str = Field(min_length=1, description="The argument text")
    sources: list[str] = Field(
        min_length=1, description="URLs from web search (at least one required)"
    )

    @field_validator("speaker")
    @classmethod
    def speaker_must_be_debater(cls, v: AgentRole) -> AgentRole:
        """Ensure speaker is PRO or CON, not JUDGE."""
        if v not in (AgentRole.PRO, AgentRole.CON):
            msg = f"Speaker must be PRO or CON, got {v}"
            raise ValueError(msg)
        return v


class JudgeRelayMessage(BaseModel):
    """Wrapper for routing a DebateTurnMessage through JudgeAgent."""

    from_agent: AgentRole = Field(description="Sending agent role")
    to_agent: AgentRole = Field(description="Receiving agent role")
    payload: DebateTurnMessage = Field(description="The debate turn being relayed")


class VerdictMessage(BaseModel):
    """Final verdict delivered by JudgeAgent after all rounds."""

    winner: AgentRole = Field(description="Must be PRO or CON, never JUDGE")
    reasoning: str = Field(min_length=1, description="Why this agent won")
    score: dict[str, int] = Field(description="Scores for pro and con")

    @field_validator("winner")
    @classmethod
    def winner_must_not_be_judge(cls, v: AgentRole) -> AgentRole:
        """Verdict winner must be PRO or CON — tie is forbidden."""
        if v not in (AgentRole.PRO, AgentRole.CON):
            msg = f"Winner must be PRO or CON, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("score")
    @classmethod
    def score_must_have_both_keys(cls, v: dict[str, int]) -> dict[str, int]:
        """Score dict must contain both 'pro' and 'con' keys."""
        if "pro" not in v or "con" not in v:
            msg = "Score must contain both 'pro' and 'con' keys"
            raise ValueError(msg)
        return v


def validate_message(raw: str) -> BaseModel:
    """Parse raw JSON string and return the appropriate validated message.

    Tries each message type in order: VerdictMessage, JudgeRelayMessage,
    DebateTurnMessage. Returns the first one that validates.

    Raises:
        ValueError: If raw JSON does not match any known message schema.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON: {e}"
        raise ValueError(msg) from e

    if not isinstance(data, dict):
        msg = "Message must be a JSON object"
        raise ValueError(msg)

    # Try to determine message type by unique keys
    if "winner" in data:
        return VerdictMessage.model_validate(data)
    if "from_agent" in data or "to_agent" in data:
        return JudgeRelayMessage.model_validate(data)
    if "speaker" in data or "argument" in data:
        return DebateTurnMessage.model_validate(data)

    msg = "Cannot determine message type from keys"
    raise ValueError(msg)
