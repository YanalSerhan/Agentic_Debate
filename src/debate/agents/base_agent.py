"""Abstract base agent — all agents inherit from this class.

Provides skill selection, API call routing through the gatekeeper,
and structured logging. Subclasses implement run() for their
specific debate role.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from debate.constants import AgentRole
from debate.shared.gatekeeper import ApiGatekeeper
from debate.shared.logger import StructuredLogger
from debate.skills.base_skill import BaseSkill


class BaseAgent(ABC):
    """Abstract agent with skill-based architecture.

    Args:
        role: The agent's role in the debate (PRO, CON, or JUDGE).
        skills: List of skills available to this agent.
        gatekeeper: ApiGatekeeper for routing all API calls.
        logger: StructuredLogger for logging agent actions.
        model: LLM model name to use.
        max_tokens: Max tokens per API response.
        api_timeout: Timeout in seconds for API calls.
    """

    def __init__(
        self,
        role: AgentRole,
        skills: list[BaseSkill],
        gatekeeper: ApiGatekeeper,
        logger: StructuredLogger,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 1000,
        api_timeout: int = 60,
    ) -> None:
        self._role = role
        self._skills = skills
        self._gatekeeper = gatekeeper
        self._logger = logger
        self._model = model
        self._max_tokens = max_tokens
        self._api_timeout = api_timeout

    @property
    def role(self) -> AgentRole:
        """Return this agent's role."""
        return self._role

    def select_skill(self, task_description: str) -> BaseSkill:
        """Select the best skill by matching description to task.

        Picks the skill whose description has the most keyword overlap
        with the task description.

        Args:
            task_description: Description of what needs to be done.

        Returns:
            The best-matching skill.

        Raises:
            ValueError: If no skills are available.
        """
        if not self._skills:
            msg = f"Agent {self._role} has no skills registered"
            raise ValueError(msg)

        best_skill = self._skills[0]
        best_score = -1

        task_words = set(task_description.lower().split())
        for skill in self._skills:
            skill_words = set(skill.description.lower().split())
            score = len(task_words & skill_words)
            if score > best_score:
                best_score = score
                best_skill = skill

        self._logger.debug(self._role.value, "skill_selected", {
            "skill": type(best_skill).__name__,
            "score": best_score,
        })
        return best_skill

    def _call_api(self, system: str, user: str, use_web_search: bool = False) -> Any:
        """Call the Anthropic API through the gatekeeper.

        All API calls MUST go through this method — never call Anthropic
        SDK directly.

        Args:
            system: System prompt.
            user: User message.
            use_web_search: Whether to include web_search tool.

        Returns:
            The API response object.
        """
        import anthropic

        client = anthropic.Anthropic()

        tools = []
        if use_web_search:
            tools.append({"type": "web_search_20250305"})

        def make_call():
            kwargs: dict[str, Any] = {
                "model": self._model,
                "max_tokens": self._max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
            if tools:
                kwargs["tools"] = tools
            return client.messages.create(**kwargs)

        self._logger.info(self._role.value, "api_call_start", {
            "model": self._model,
            "use_web_search": use_web_search,
        })

        result = self._gatekeeper.execute(make_call)

        self._logger.info(self._role.value, "api_call_complete", {
            "model": self._model,
        })

        return result

    def _extract_text_and_sources(self, response: Any) -> tuple[str, list[str]]:
        """Extract text content and source URLs from an API response.

        Args:
            response: Anthropic API response object.

        Returns:
            Tuple of (text_content, list_of_source_urls).
        """
        text_parts = []
        sources = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "web_search_tool_result":
                for result in getattr(block, "search_results", []):
                    url = getattr(result, "url", "")
                    if url:
                        sources.append(url)

        return "\n".join(text_parts), sources

    @abstractmethod
    def run(self, context: dict) -> str:
        """Execute the agent's role-specific logic.

        Args:
            context: Dict with topic, round, opponent_argument, etc.

        Returns:
            JSON string of the agent's message (DebateTurnMessage or VerdictMessage).
        """
