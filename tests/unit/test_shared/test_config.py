"""Tests for debate.shared.config — ConfigManager."""

import json

import pytest

from debate.shared.config import ConfigError, ConfigManager


class TestConfigManager:
    """Tests for ConfigManager loading and validation."""

    def test_loads_setup_json(self, config_dir):
        config = ConfigManager(config_dir)
        assert config.get_model() == "claude-sonnet-4-20250514"
        assert config.get_max_rounds() == 10
        assert config.get_max_tokens() == 1000

    def test_loads_rate_limits(self, config_dir):
        config = ConfigManager(config_dir)
        limits = config.get_rate_limits()
        assert limits["requests_per_minute"] == 30
        assert limits["requests_per_hour"] == 500

    def test_loads_logging_config(self, config_dir):
        config = ConfigManager(config_dir)
        assert config.get_log_max_files() == 20
        assert config.get_log_max_lines() == 500

    def test_raises_on_missing_file(self, tmp_path):
        config_path = tmp_path / "empty_config"
        config_path.mkdir()
        with pytest.raises(ConfigError, match="not found"):
            ConfigManager(str(config_path))

    def test_raises_on_missing_version(self, tmp_path):
        config_path = tmp_path / "bad_config"
        config_path.mkdir()
        (config_path / "setup.json").write_text(json.dumps({"model": "test"}))
        with pytest.raises(ConfigError, match="version"):
            ConfigManager(str(config_path))

    def test_raises_on_version_mismatch(self, tmp_path):
        config_path = tmp_path / "mismatch_config"
        config_path.mkdir()
        for fname in ["setup.json", "rate_limits.json", "logging_config.json"]:
            data = {"version": "9.99"}
            if fname == "rate_limits.json":
                data["services"] = {"default": {}}
            if fname == "logging_config.json":
                data.update({"max_files": 20, "max_lines_per_file": 500, "log_dir": "/tmp"})
            if fname == "setup.json":
                data.update({"model": "test", "max_tokens": 100, "max_rounds": 5,
                             "api_timeout_seconds": 60, "budget_cap_usd": 5.0,
                             "max_restart_attempts": 3, "keepalive_interval_seconds": 10,
                             "keepalive_timeout_seconds": 30})
            (config_path / fname).write_text(json.dumps(data))
        with pytest.raises(ConfigError, match="does not match"):
            ConfigManager(str(config_path))

    def test_raises_on_invalid_json(self, tmp_path):
        config_path = tmp_path / "invalid_json"
        config_path.mkdir()
        (config_path / "setup.json").write_text("not json at all")
        with pytest.raises(ConfigError, match="Invalid JSON"):
            ConfigManager(str(config_path))

    def test_version_is_accessible(self, config_dir):
        config = ConfigManager(config_dir)
        assert config.get_api_timeout() == 60
        assert config.get_budget_cap() == 5.0

    def test_unknown_rate_limit_service(self, config_dir):
        config = ConfigManager(config_dir)
        with pytest.raises(ConfigError, match="No rate limits"):
            config.get_rate_limits("nonexistent_service")
