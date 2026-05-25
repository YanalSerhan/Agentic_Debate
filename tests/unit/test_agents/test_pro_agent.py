"""Tests for debate.agents.pro_agent — ProAgent."""

import json
from unittest.mock import MagicMock

from debate.agents.pro_agent import ProAgent
from debate.constants import AgentRole


class TestProAgent:
    """Tests for ProAgent behavior."""

    def _make_mock_response(self, text="AI is great", urls=None):
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

    def test_always_argues_for(self, mock_gatekeeper, mock_logger):
        mock_response = self._make_mock_response(urls=["https://example.com"])
        mock_gatekeeper.execute = MagicMock(return_value=mock_response)

        agent = ProAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        result = json.loads(agent.run({"topic": "AI is good", "round": 1}))

        assert result["speaker"] == AgentRole.PRO.value

    def test_uses_argument_skill(self, mock_gatekeeper, mock_logger):
        agent = ProAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        skill = agent.select_skill("construct argument for debate topic")
        assert type(skill).__name__ == "ArgumentSkill"

    def test_produces_valid_turn(self, mock_gatekeeper, mock_logger):
        mock_response = self._make_mock_response(
            text="Strong argument for AI",
            urls=["https://source.com"],
        )
        mock_gatekeeper.execute = MagicMock(return_value=mock_response)

        agent = ProAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        result = json.loads(agent.run({"topic": "AI is good", "round": 2}))

        assert result["round"] == 2
        assert result["speaker"] == "pro"
        assert len(result["argument"]) > 0
        assert len(result["sources"]) >= 1

    def test_fallback_source_when_none_returned(self, mock_gatekeeper, mock_logger):
        mock_response = self._make_mock_response(text="Argument", urls=None)
        mock_gatekeeper.execute = MagicMock(return_value=mock_response)

        agent = ProAgent(gatekeeper=mock_gatekeeper, logger=mock_logger)
        result = json.loads(agent.run({"topic": "AI", "round": 1}))

        assert len(result["sources"]) >= 1
