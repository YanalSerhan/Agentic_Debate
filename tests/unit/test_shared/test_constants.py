"""Tests for debate.constants — enumerations."""

from debate.constants import AgentRole, DebateStatus, MessageType


class TestAgentRole:
    """Tests for the AgentRole enum."""

    def test_pro_value(self):
        assert AgentRole.PRO.value == "pro"

    def test_con_value(self):
        assert AgentRole.CON.value == "con"

    def test_judge_value(self):
        assert AgentRole.JUDGE.value == "judge"

    def test_all_roles_importable(self):
        roles = [AgentRole.PRO, AgentRole.CON, AgentRole.JUDGE]
        assert len(roles) == 3

    def test_is_string_enum(self):
        assert isinstance(AgentRole.PRO, str)
        assert AgentRole.PRO == "pro"


class TestMessageType:
    """Tests for the MessageType enum."""

    def test_debate_turn(self):
        assert MessageType.DEBATE_TURN.value == "debate_turn"

    def test_judge_relay(self):
        assert MessageType.JUDGE_RELAY.value == "judge_relay"

    def test_verdict(self):
        assert MessageType.VERDICT.value == "verdict"


class TestDebateStatus:
    """Tests for the DebateStatus enum."""

    def test_running(self):
        assert DebateStatus.RUNNING.value == "running"

    def test_finished(self):
        assert DebateStatus.FINISHED.value == "finished"

    def test_error(self):
        assert DebateStatus.ERROR.value == "error"
