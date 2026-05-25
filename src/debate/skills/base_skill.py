"""Abstract base class for all debate skills.

Each skill has a description (used for auto-selection by agents)
and an execute method that performs the skill's core logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseSkill(ABC):
    """Abstract skill interface.

    Subclasses must set a description and implement execute() and
    validate_input(). The description is loaded from SKILL.md in the
    skill's directory.
    """

    def __init__(self) -> None:
        self._description: str = self._load_description()

    @property
    def description(self) -> str:
        """Return the skill's description for agent auto-selection."""
        return self._description

    def _load_description(self) -> str:
        """Load the skill description from SKILL.md in the skill's directory."""
        # Subclasses are in subdirectories (e.g., argument_skill/)
        # This base class is in skills/ — subclasses override _get_skill_dir
        skill_md = self._get_skill_dir() / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text(encoding="utf-8").strip()
        return ""

    def _get_skill_dir(self) -> Path:
        """Return the directory containing this skill's SKILL.md.

        Subclasses should override this if they are not in the default location.
        Default: the directory containing the subclass's source file.
        """
        import inspect
        subclass_file = inspect.getfile(type(self))
        return Path(subclass_file).parent

    @abstractmethod
    def execute(self, context: dict) -> str:
        """Execute the skill with the given context.

        Args:
            context: Dict containing topic, opponent_argument, transcript, etc.

        Returns:
            The skill's output as a string (typically JSON).
        """

    @abstractmethod
    def validate_input(self, context: dict) -> None:
        """Validate that the context has all required keys.

        Raises:
            ValueError: If required keys are missing.
        """
