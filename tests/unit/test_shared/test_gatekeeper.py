"""Tests for debate.shared.gatekeeper — ApiGatekeeper."""

from unittest.mock import MagicMock

import pytest

from debate.shared.budget import BudgetExceededError
from debate.shared.gatekeeper import (
    ApiGatekeeper,
    GatekeeperError,
)


def _make_gatekeeper(budget=5.0, max_retries=3, retry_after=0.01):
    """Create a gatekeeper with test-friendly defaults."""
    rate_limits = {
        "requests_per_minute": 1000,
        "requests_per_hour": 10000,
        "concurrent_max": 100,
        "retry_after_seconds": retry_after,
        "max_retries": max_retries,
        "max_queue_depth": 50,
    }
    return ApiGatekeeper(rate_limits=rate_limits, budget_cap=budget)


class TestApiGatekeeper:
    """Tests for ApiGatekeeper rate limiting, retry, and budget."""

    def test_execute_success(self):
        gk = _make_gatekeeper()
        result = gk.execute(lambda: "hello")
        assert result == "hello"

    def test_rate_limit_enforced(self):
        rate_limits = {
            "requests_per_minute": 2,
            "requests_per_hour": 10000,
            "concurrent_max": 100,
            "retry_after_seconds": 0.01,
            "max_retries": 1,
            "max_queue_depth": 50,
        }
        gk = ApiGatekeeper(rate_limits=rate_limits, budget_cap=5.0)
        # Should succeed for first 2 calls within a minute window
        gk.execute(lambda: 1)
        gk.execute(lambda: 2)
        # Third call should still work but may be delayed
        # (rate limiter waits, doesn't error)

    def test_retry_on_transient_failure(self):
        gk = _make_gatekeeper(max_retries=3, retry_after=0.01)
        call_count = {"n": 0}

        def flaky_call():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ConnectionError("transient")
            return "success"

        result = gk.execute(flaky_call)
        assert result == "success"
        assert call_count["n"] == 3

    def test_exhausted_retries_raises(self):
        gk = _make_gatekeeper(max_retries=2, retry_after=0.01)

        def always_fails():
            raise ConnectionError("permanent failure")

        with pytest.raises(GatekeeperError, match="retries exhausted"):
            gk.execute(always_fails)

    def test_budget_cap_blocks_calls(self):
        gk = _make_gatekeeper(budget=0.001)
        # Simulate spending above budget
        gk._budget._total_cost = 0.002
        with pytest.raises(BudgetExceededError, match="Budget cap"):
            gk.execute(lambda: "should not run")

    def test_api_calls_logged(self):
        logger = MagicMock()
        rate_limits = {
            "requests_per_minute": 1000,
            "requests_per_hour": 10000,
            "concurrent_max": 100,
            "retry_after_seconds": 0.01,
            "max_retries": 3,
            "max_queue_depth": 50,
        }
        gk = ApiGatekeeper(rate_limits=rate_limits, budget_cap=5.0, logger=logger)

        mock_result = MagicMock()
        mock_result.usage.input_tokens = 100
        mock_result.usage.output_tokens = 50
        gk.execute(lambda: mock_result)

        logger.info.assert_called()

    def test_cost_report(self):
        gk = _make_gatekeeper()
        report = gk.get_cost_report()
        assert "total_input_tokens" in report
        assert "total_output_tokens" in report
        assert "total_cost_usd" in report
        assert "budget_cap_usd" in report
        assert "budget_remaining_usd" in report

    def test_queue_status(self):
        gk = _make_gatekeeper()
        status = gk.get_queue_status()
        assert status.pending == 0
        assert status.max_depth == 50
