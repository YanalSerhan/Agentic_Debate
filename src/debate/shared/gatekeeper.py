"""API Gatekeeper — rate limiting, queuing, retry, budget enforcement.

Every Anthropic API call in the system MUST go through
ApiGatekeeper.execute(). No other module may call the SDK directly.
"""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from typing import Any

from debate.shared.budget import BudgetTracker
from debate.shared.logger import StructuredLogger


class GatekeeperError(Exception):
    """Raised when the gatekeeper encounters a non-retryable error."""


class QueueStatus:
    """Snapshot of the gatekeeper queue state."""

    def __init__(self, pending: int, max_depth: int) -> None:
        self.pending = pending
        self.max_depth = max_depth


class ApiGatekeeper:
    """Controls all API access with rate limiting, retry, and budget tracking.

    Args:
        rate_limits: Dict with rate limit configuration values.
        budget_cap: Maximum total cost in USD before blocking further calls.
        logger: StructuredLogger instance for logging API calls.
    """

    def __init__(
        self,
        rate_limits: dict[str, Any],
        budget_cap: float = 5.0,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._rpm = rate_limits.get("requests_per_minute", 30)
        self._rph = rate_limits.get("requests_per_hour", 500)
        self._concurrent_max = rate_limits.get("concurrent_max", 5)
        self._retry_after = rate_limits.get("retry_after_seconds", 30)
        self._max_retries = rate_limits.get("max_retries", 3)
        self._max_queue_depth = rate_limits.get("max_queue_depth", 50)
        self._budget_cap = budget_cap
        self._logger = logger

        self._minute_timestamps: list[float] = []
        self._hour_timestamps: list[float] = []
        self._active_count = 0
        self._lock = threading.Lock()
        self._budget = BudgetTracker(budget_cap)
        self._queue: queue.Queue = queue.Queue(maxsize=self._max_queue_depth)

    def execute(self, api_call: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute an API call through the gatekeeper.

        Enforces rate limits, budget cap, and retry logic.

        Returns:
            The result of the api_call.

        Raises:
            BudgetExceededError: If budget cap is exceeded.
            GatekeeperError: If all retries are exhausted.
        """
        self._check_budget()
        self._wait_for_rate_limit()

        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                with self._lock:
                    self._active_count += 1
                result = api_call(*args, **kwargs)
                self._record_success(result)
                return result
            except Exception as e:
                last_error = e
                self._log_retry(attempt, e)
                if attempt < self._max_retries:
                    time.sleep(self._retry_after)
            finally:
                with self._lock:
                    self._active_count -= 1

        msg = f"All {self._max_retries} retries exhausted: {last_error}"
        raise GatekeeperError(msg) from last_error

    def _check_budget(self) -> None:
        """Raise BudgetExceededError if the total cost exceeds the cap."""
        self._budget.check_budget()

    def _wait_for_rate_limit(self) -> None:
        """Block until the rate limits allow a new request."""
        while True:
            now = time.time()
            with self._lock:
                self._minute_timestamps = [
                    t for t in self._minute_timestamps if now - t < 60
                ]
                self._hour_timestamps = [
                    t for t in self._hour_timestamps if now - t < 3600
                ]
                minute_ok = len(self._minute_timestamps) < self._rpm
                hour_ok = len(self._hour_timestamps) < self._rph
                concurrent_ok = self._active_count < self._concurrent_max
                if minute_ok and hour_ok and concurrent_ok:
                    self._minute_timestamps.append(now)
                    self._hour_timestamps.append(now)
                    break
            time.sleep(0.5)

    def _record_success(self, result: Any) -> None:
        """Record usage stats from a successful API response."""
        usage = getattr(result, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

        cost = self._budget.record_usage(input_tokens, output_tokens)

        if self._logger:
            self._logger.info("gatekeeper", "api_call_success", {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": round(cost, 6),
                "total_cost": round(self._budget.total_cost, 6),
            })

    def _log_retry(self, attempt: int, error: Exception) -> None:
        """Log a retry attempt."""
        if self._logger:
            self._logger.warning("gatekeeper", "api_call_retry", {
                "attempt": attempt,
                "max_retries": self._max_retries,
                "error": str(error),
            })

    def get_queue_status(self) -> QueueStatus:
        """Return the current queue status."""
        return QueueStatus(self._queue.qsize(), self._max_queue_depth)

    def get_cost_report(self) -> dict[str, Any]:
        """Return a summary of API usage and costs."""
        return self._budget.get_cost_report()
