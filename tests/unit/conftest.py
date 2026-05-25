"""Shared test fixtures for the debate-agents test suite."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test artifacts."""
    return tmp_path


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory with valid config files."""
    config_path = tmp_path / "config"
    config_path.mkdir()

    setup = {
        "version": "1.00",
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "debate_topic": "",
        "max_rounds": 10,
        "api_timeout_seconds": 60,
        "max_restart_attempts": 3,
        "keepalive_interval_seconds": 10,
        "keepalive_timeout_seconds": 30,
        "budget_cap_usd": 5.0,
    }
    (config_path / "setup.json").write_text(json.dumps(setup))

    rate_limits = {
        "version": "1.00",
        "services": {
            "default": {
                "requests_per_minute": 30,
                "requests_per_hour": 500,
                "concurrent_max": 5,
                "retry_after_seconds": 0.01,
                "max_retries": 3,
                "max_queue_depth": 50,
            }
        },
    }
    (config_path / "rate_limits.json").write_text(json.dumps(rate_limits))

    logging_config = {
        "version": "1.00",
        "max_files": 20,
        "max_lines_per_file": 500,
        "log_dir": str(tmp_path / "logs"),
        "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
    }
    (config_path / "logging_config.json").write_text(json.dumps(logging_config))

    return str(config_path)


@pytest.fixture
def mock_logger():
    """Provide a mock StructuredLogger."""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


@pytest.fixture
def mock_gatekeeper():
    """Provide a mock ApiGatekeeper."""
    gk = MagicMock()
    gk.execute = MagicMock(side_effect=lambda fn, *a, **kw: fn(*a, **kw))
    gk.get_cost_report = MagicMock(return_value={
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost_usd": 0.0,
        "budget_cap_usd": 5.0,
        "budget_remaining_usd": 5.0,
    })
    return gk
