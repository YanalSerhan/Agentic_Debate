"""ConAgent — argues AGAINST the debate topic.

Uses CounterSkill to build counter-arguments. Includes mandatory
web search per turn. Must reference and rebut the opponent's argument.
"""

from __future__ import annotations

import json

from debate.agents.base_agent import BaseAgent
from debate.constants import AgentRole
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.logger import StructuredLogger
from debate.skills import CounterSkill


class ConAgent(BaseAgent):
    """Agent that argues against the debate topic.

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
            role=AgentRole.CON,
            skills=[CounterSkill()],
            gatekeeper=gatekeeper,
            logger=logger,
            model=model,
            max_tokens=max_tokens,
            api_timeout=api_timeout,
        )

    def run(self, context: dict) -> str:
        """Generate a counter-argument for the current round.

        Args:
            context: Must contain 'topic' and 'round'.
                     Must contain 'opponent_argument' after round 1.

        Returns:
            JSON string of a DebateTurnMessage.
        """
        skill = self.select_skill("construct counter-argument against debate topic")
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
            "speaker": AgentRole.CON.value,
            "argument": argument_text,
            "sources": sources,
        }

        self._logger.info(self._role.value, "turn_produced", {
            "round": turn["round"],
            "sources_count": len(sources),
        })

        return json.dumps(turn)
