"""JudgeAgent — supervisor that orchestrates the debate.

Routes all messages between ProAgent and ConAgent. No direct
child-to-child communication. Delivers the final verdict.
"""

from __future__ import annotations

import json

from debate.agents.base_agent import BaseAgent
from debate.constants import AgentRole
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.ipc import VerdictMessage
from debate.shared.logger import StructuredLogger
from debate.skills import JudgeSkill


class JudgeAgent(BaseAgent):
    """Supervisor agent that orchestrates the debate loop.

    All communication flows: child → JudgeAgent → child.
    After max_rounds, JudgeAgent evaluates and delivers a verdict.

    Args:
        pro_agent: The ProAgent instance.
        con_agent: The ConAgent instance.
        gatekeeper: ApiGatekeeper for all API calls.
        logger: StructuredLogger instance.
        max_rounds: Maximum debate rounds.
        model: LLM model name.
        max_tokens: Max tokens per response.
        api_timeout: API call timeout in seconds.
    """

    def __init__(
        self,
        pro_agent: BaseAgent,
        con_agent: BaseAgent,
        gatekeeper: ApiGatekeeper,
        logger: StructuredLogger,
        max_rounds: int = 10,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 1000,
        api_timeout: int = 60,
    ) -> None:
        super().__init__(
            role=AgentRole.JUDGE,
            skills=[JudgeSkill()],
            gatekeeper=gatekeeper,
            logger=logger,
            model=model,
            max_tokens=max_tokens,
            api_timeout=api_timeout,
        )
        self._pro_agent = pro_agent
        self._con_agent = con_agent
        self._max_rounds = max_rounds
        self._transcript: list[dict] = []

    @property
    def transcript(self) -> list[dict]:
        """Return the full debate transcript."""
        return self._transcript.copy()

    def run(self, context: dict) -> str:
        """Orchestrate the full debate loop.

        Args:
            context: Must contain 'topic'.

        Returns:
            JSON string of a VerdictMessage.
        """
        topic = context.get("topic", "")
        if not topic:
            msg = "Context must contain a non-empty 'topic'"
            raise ValueError(msg)

        self._logger.info("judge", "debate_start", {"topic": topic})
        self._transcript = []

        for round_num in range(1, self._max_rounds + 1):
            self._run_round(topic, round_num)

        verdict_json = self._deliver_verdict(topic)
        self._logger.info("judge", "debate_end", {"topic": topic})
        return verdict_json

    def _run_round(self, topic: str, round_num: int) -> None:
        """Run a single debate round: Pro turn → relay → Con turn."""
        self._logger.info("judge", "round_start", {"round": round_num})

        # Get the last con argument (if any) for pro to address
        last_con_arg = self._get_last_argument(AgentRole.CON)

        # --- Pro turn ---
        pro_context = {
            "topic": topic,
            "round": round_num,
            "opponent_argument": last_con_arg,
        }
        pro_turn_json = self._pro_agent.run(pro_context)
        pro_turn = json.loads(pro_turn_json)
        self._transcript.append(pro_turn)

        self._log_relay(AgentRole.PRO, AgentRole.CON, pro_turn)

        # --- Con turn ---
        con_context = {
            "topic": topic,
            "round": round_num,
            "opponent_argument": pro_turn.get("argument", ""),
        }
        con_turn_json = self._con_agent.run(con_context)
        con_turn = json.loads(con_turn_json)
        self._transcript.append(con_turn)

        self._log_relay(AgentRole.CON, AgentRole.PRO, con_turn)
        self._logger.info("judge", "round_complete", {"round": round_num})

    def _deliver_verdict(self, topic: str) -> str:
        """Use JudgeSkill to evaluate the transcript and deliver a verdict."""
        skill = self.select_skill("evaluate debate verdict")
        prompt_json = skill.execute({
            "topic": topic,
            "transcript": self._transcript,
        })
        prompt_data = json.loads(prompt_json)

        response = self._call_api(
            system=prompt_data["system"],
            user=prompt_data["user"],
            use_web_search=False,
        )

        verdict_text, _ = self._extract_text_and_sources(response)
        verdict_data = json.loads(verdict_text)

        # Validate verdict
        verdict = VerdictMessage.model_validate(verdict_data)

        self._logger.info("judge", "verdict_delivered", {
            "winner": verdict.winner.value,
            "score": verdict.score,
        })

        return verdict.model_dump_json()

    def _get_last_argument(self, speaker: AgentRole) -> str:
        """Get the last argument from a specific speaker."""
        for turn in reversed(self._transcript):
            if turn.get("speaker") == speaker.value:
                return turn.get("argument", "")
        return ""

    def _log_relay(self, from_agent: AgentRole, to_agent: AgentRole, turn: dict) -> None:
        """Log a message relay event."""
        self._logger.info("judge", "message_relay", {
            "from": from_agent.value,
            "to": to_agent.value,
            "round": turn.get("round"),
        })
