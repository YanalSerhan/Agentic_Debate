"""Tests for debate.agents.base_agent — BaseAgent abstract class."""


import pytest

from debate.agents.base_agent import BaseAgent
from debate.constants import AgentRole
from debate.skills.base_skill import BaseSkill


class _MockSkill(BaseSkill):
    """Concrete skill for testing base agent."""

    def __init__(self, desc="test skill for arguments"):
        self._test_desc = desc
        super().__init__()

    def _load_description(self):
        return self._test_desc

    def execute(self, context):
        return '{"result": "ok"}'

    def validate_input(self, context):
        pass


class _ConcreteAgent(BaseAgent):
    """Concrete agent for testing."""

    def run(self, context):
        skill = self.select_skill("test task")
        return skill.execute(context)


class TestBaseAgent:
    """Tests for the abstract BaseAgent."""

    def test_agent_has_role(self, mock_gatekeeper, mock_logger):
        agent = _ConcreteAgent(
            role=AgentRole.PRO,
            skills=[_MockSkill()],
            gatekeeper=mock_gatekeeper,
            logger=mock_logger,
        )
        assert agent.role == AgentRole.PRO

    def test_select_skill_by_description(self, mock_gatekeeper, mock_logger):
        skill_a = _MockSkill("skill for building arguments in debate")
        skill_b = _MockSkill("skill for counter arguments against topic")
        agent = _ConcreteAgent(
            role=AgentRole.PRO,
            skills=[skill_a, skill_b],
            gatekeeper=mock_gatekeeper,
            logger=mock_logger,
        )
        selected = agent.select_skill("arguments in debate for topic")
        assert selected is skill_a

    def test_select_skill_raises_with_no_skills(self, mock_gatekeeper, mock_logger):
        agent = _ConcreteAgent(
            role=AgentRole.PRO,
            skills=[],
            gatekeeper=mock_gatekeeper,
            logger=mock_logger,
        )
        with pytest.raises(ValueError, match="no skills"):
            agent.select_skill("any task")

    def test_run_is_callable(self, mock_gatekeeper, mock_logger):
        agent = _ConcreteAgent(
            role=AgentRole.CON,
            skills=[_MockSkill()],
            gatekeeper=mock_gatekeeper,
            logger=mock_logger,
        )
        result = agent.run({})
        assert result == '{"result": "ok"}'
