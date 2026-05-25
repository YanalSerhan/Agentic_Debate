"""Shared infrastructure package — exports all shared classes."""

from debate.shared.config import ConfigError, ConfigManager
from debate.shared.gatekeeper import ApiGatekeeper, GatekeeperError
from debate.shared.budget import BudgetExceededError
from debate.shared.logger import StructuredLogger
from debate.shared.version import __version__
from debate.shared.watchdog import Watchdog, WatchdogGaveUpError

__all__ = [
    "ApiGatekeeper",
    "BudgetExceededError",
    "ConfigError",
    "ConfigManager",
    "GatekeeperError",
    "StructuredLogger",
    "Watchdog",
    "WatchdogGaveUpError",
    "__version__",
]
