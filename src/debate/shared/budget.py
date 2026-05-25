"""Budget tracking for API usage.

Tracks token counts and estimates cost, enforcing a hard budget cap.
"""

from __future__ import annotations

import threading
from typing import Any


class BudgetExceededError(Exception):
    """Raised when cumulative API cost exceeds the budget cap."""


class BudgetTracker:
    """Tracks token usage, estimates cost, and enforces a budget cap.

    Args:
        budget_cap: Maximum total cost in USD before blocking further calls.
    """

    def __init__(self, budget_cap: float = 5.0) -> None:
        self._budget_cap = budget_cap
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._lock = threading.Lock()

    @property
    def total_cost(self) -> float:
        """Return the current total cost."""
        with self._lock:
            return self._total_cost

    def check_budget(self) -> None:
        """Raise BudgetExceededError if the total cost exceeds the cap."""
        with self._lock:
            if self._total_cost >= self._budget_cap:
                msg = (
                    f"Budget cap of ${self._budget_cap:.2f} exceeded "
                    f"(current: ${self._total_cost:.2f})"
                )
                raise BudgetExceededError(msg)

    def record_usage(self, input_tokens: int, output_tokens: int) -> float:
        """Record usage stats and return the estimated cost of this transaction."""
        cost = self._estimate_cost(input_tokens, output_tokens)
        with self._lock:
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_cost += cost
        return cost

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD based on Claude Sonnet pricing."""
        input_cost = (input_tokens / 1_000_000) * 3.0
        output_cost = (output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost

    def get_cost_report(self) -> dict[str, Any]:
        """Return a summary of API usage and costs."""
        with self._lock:
            return {
                "total_input_tokens": self._total_input_tokens,
                "total_output_tokens": self._total_output_tokens,
                "total_cost_usd": round(self._total_cost, 6),
                "budget_cap_usd": self._budget_cap,
                "budget_remaining_usd": round(self._budget_cap - self._total_cost, 6),
            }
