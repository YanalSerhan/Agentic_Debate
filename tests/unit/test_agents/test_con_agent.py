"""Tests for debate.agents.con_agent — ConAgent."""

import json
from unittest.mock import MagicMock

from debate.agents.con_agent import ConAgent
from debate.constants import AgentRole


class TestConAgent:
    """Tests for ConAgent behavior."""

    def _make_mock_response(self, text="AI is harmful", urls=None):
        """Create a mock Anthropic response."""
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
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50
        return response

    def test_always_argues_against(self, mock_gatekeeper, mock_logger):
        mock_response = self._make_mock_response(urls=["https://example.com"])
        mock_gatekeeper.execute = MagicMock(return_value=mock_response)

        agent = ConAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        result = json.loads(agent.run({"topic": "AI is good", "round": 1}))

        assert result["speaker"] == AgentRole.CON.value

    def test_uses_counter_skill(self, mock_gatekeeper, mock_logger):
        agent = ConAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        skill = agent.select_skill("construct counter-argument against debate topic")
        assert type(skill).__name__ == "CounterSkill"

    def test_produces_valid_turn(self, mock_gatekeeper, mock_logger):
        mock_response = self._make_mock_response(
            text="Counter argument",
            urls=["https://counter.com"],
        )
        mock_gatekeeper.execute = MagicMock(return_value=mock_response)

        agent = ConAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        result = json.loads(agent.run({
            "topic": "AI is good", "round": 3,
            "opponent_argument": "AI increases productivity",
        }))

        assert result["round"] == 3
        assert result["speaker"] == "con"
        assert len(result["argument"]) > 0
        assert len(result["sources"]) >= 1

    def test_fallback_source(self, mock_gatekeeper, mock_logger):
        mock_response = self._make_mock_response(text="Counter", urls=None)
        mock_gatekeeper.execute = MagicMock(return_value=mock_response)

        agent = ConAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        result = json.loads(agent.run({"topic": "AI", "round": 1}))

        assert len(result["sources"]) >= 1
