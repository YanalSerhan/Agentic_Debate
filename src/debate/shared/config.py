"""Configuration loader — reads all JSON config files from the config/ directory.

Provides typed getters for every configuration value. All runtime-configurable
values in the system come from here — nothing is hardcoded in business logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from debate.shared.version import __version__


class ConfigError(Exception):
    """Raised when a configuration file is invalid or missing."""


class ConfigManager:
    """Loads and validates JSON configuration files.

    Args:
        config_dir: Path to the directory containing JSON config files.
    """

    def __init__(self, config_dir: str = "config") -> None:
        self._config_dir = Path(config_dir)
        self._setup: dict[str, Any] = {}
        self._rate_limits: dict[str, Any] = {}
        self._logging: dict[str, Any] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load and validate all configuration files."""
        self._setup = self._load_file("setup.json")
        self._rate_limits = self._load_file("rate_limits.json")
        self._logging = self._load_file("logging_config.json")
        self._validate_versions()

    def _load_file(self, filename: str) -> dict[str, Any]:
        """Load a single JSON config file."""
        filepath = self._config_dir / filename
        if not filepath.exists():
            msg = f"Config file not found: {filepath}"
            raise ConfigError(msg)
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in {filepath}: {e}"
            raise ConfigError(msg) from e
        if "version" not in data:
            msg = f"Missing 'version' key in {filepath}"
            raise ConfigError(msg)
        return data

    def _validate_versions(self) -> None:
        """Ensure all config file versions match the package version."""
        for name, cfg in [
            ("setup", self._setup),
            ("rate_limits", self._rate_limits),
            ("logging", self._logging),
        ]:
            if cfg["version"] != __version__:
                msg = (
                    f"Config '{name}' version {cfg['version']} "
                    f"does not match package version {__version__}"
                )
                raise ConfigError(msg)

    # --- Setup getters ---

    def get_model(self) -> str:
        """Return the configured LLM model name."""
        return self._setup["model"]

    def get_max_tokens(self) -> int:
        """Return the max tokens per API call."""
        return self._setup["max_tokens"]

    def get_max_rounds(self) -> int:
        """Return the maximum number of debate rounds."""
        return self._setup["max_rounds"]

    def get_api_timeout(self) -> int:
        """Return the API call timeout in seconds."""
        return self._setup["api_timeout_seconds"]

    def get_budget_cap(self) -> float:
        """Return the budget cap in USD."""
        return self._setup["budget_cap_usd"]

    def get_max_restart_attempts(self) -> int:
        """Return the max watchdog restart attempts."""
        return self._setup["max_restart_attempts"]

    def get_keepalive_interval(self) -> int:
        """Return keep-alive ping interval in seconds."""
        return self._setup["keepalive_interval_seconds"]

    def get_keepalive_timeout(self) -> int:
        """Return keep-alive timeout in seconds."""
        return self._setup["keepalive_timeout_seconds"]

    # --- Rate limit getters ---

    def get_rate_limits(self, service: str = "default") -> dict[str, Any]:
        """Return rate limit config for a service."""
        services = self._rate_limits.get("services", {})
        if service not in services:
            msg = f"No rate limits configured for service '{service}'"
            raise ConfigError(msg)
        return services[service]

    # --- Logging getters ---

    def get_log_max_files(self) -> int:
        """Return maximum number of log files before FIFO rotation."""
        return self._logging["max_files"]

    def get_log_max_lines(self) -> int:
        """Return maximum lines per log file."""
        return self._logging["max_lines_per_file"]

    def get_log_dir(self) -> str:
        """Return the log directory path."""
        return self._logging["log_dir"]
