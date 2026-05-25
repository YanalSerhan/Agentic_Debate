"""ProAgent — argues FOR the debate topic.

Uses ArgumentSkill to build pro-arguments. Includes mandatory
web search per turn. Never agrees with the opponent.
"""

from __future__ import annotations

import json

from debate.agents.base_agent import BaseAgent
from debate.constants import AgentRole
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.logger import StructuredLogger
from debate.skills import ArgumentSkill


class ProAgent(BaseAgent):
    """Agent that argues in favour of the debate topic.

    Args:
        gatekeeper: ApiGatekeeper for all API calls.
        logger: StructuredLogger instance.
        model: LLM model name.
        max_tokens: Max tokens per response.
        api_timeout: API call timeout in seconds.
    """

    def __init__(
        self,
        gatekeeper: ApiGatekeeper,
        logger: StructuredLogger,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 1000,
        api_timeout: int = 60,
    ) -> None:
        super().__init__(
            role=AgentRole.PRO,
            skills=[ArgumentSkill()],
            gatekeeper=gatekeeper,
            logger=logger,
            model=model,
            max_tokens=max_tokens,
            api_timeout=api_timeout,
        )

    def run(self, context: dict) -> str:
        """Generate a pro-argument for the current round.

        Args:
            context: Must contain 'topic' and 'round'.
                     May contain 'opponent_argument'.

        Returns:
            JSON string of a DebateTurnMessage.
        """
        skill = self.select_skill("construct argument for debate topic")
        prompt_json = skill.execute(context)
        prompt_data = json.loads(prompt_json)

        response = self._call_api(
            system=prompt_data["system"],
            user=prompt_data["user"],
            use_web_search=True,
        )

        argument_text, sources = self._extract_text_and_sources(response)

        if not sources:
            sources = ["https://search.performed.no.urls.returned"]

        turn = {
            "round": context.get("round", 1),
            "speaker": AgentRole.PRO.value,
            "argument": argument_text,
            "sources": sources,
        }

        self._logger.info(self._role.value, "turn_produced", {
            "round": turn["round"],
            "sources_count": len(sources),
        })

        return json.dumps(turn)
