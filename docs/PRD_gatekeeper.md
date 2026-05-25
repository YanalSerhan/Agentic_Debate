# PRD: API Gatekeeper
## Exercise 02: AI Agent Debate System

### 1. Overview
The `ApiGatekeeper` is a mandatory security, cost-control, and resilience layer. **Every** call to the external Anthropic API must pass through this component. Direct API calls from agents or skills are forbidden.

### 2. Core Responsibilities
- **Rate Limiting:** Prevent 429 Too Many Requests errors.
- **Queueing:** Backpressure management for bursts of requests.
- **Retries & Backoff:** Graceful recovery from transient API errors.
- **Budget Tracking:** Prevent runaway costs by capping max spend in USD.
- **Telemetry:** Log token usage and cost for every call.

### 3. Rate Limit Configuration Structure

Rate limits are loaded dynamically from `config/rate_limits.json` and are never hardcoded.

```json
{
  "version": "1.00",
  "services": {
    "default": {
      "requests_per_minute": 30,
      "requests_per_hour": 500,
      "concurrent_max": 5,
      "retry_after_seconds": 30,
      "max_retries": 3,
      "max_queue_depth": 50
    }
  }
}
```

### 4. Queue Management & Backpressure
- When rate limits (e.g., `requests_per_minute` or `concurrent_max`) are saturated, incoming requests block efficiently.
- A thread-safe mechanism (`threading.Lock` and sleep intervals) is used to enqueue requests until capacity is available.
- If the waiting queue exceeds `max_queue_depth`, further requests could be rejected, though current design favors blocking indefinitely within timeout bounds.

### 5. Retry Logic
- On an API exception, the Gatekeeper catches it and retries up to `max_retries` times.
- Between retries, it waits for `retry_after_seconds`.
- If all retries are exhausted, it raises a `GatekeeperError`, which propagates up to crash the current action (and potentially trigger the Watchdog).

### 6. Budget Cap Enforcement
- The system has a hard `budget_cap_usd` configured in `config/setup.json`.
- After every successful call, the Gatekeeper estimates the cost:
  - Input tokens: ~$3.00 / 1M tokens
  - Output tokens: ~$15.00 / 1M tokens
- Cumulative cost is tracked in memory (`_total_cost`).
- Before initiating any new API call, `_check_budget()` runs. If `_total_cost >= budget_cap_usd`, a `BudgetExceededError` is raised immediately, halting all further API interactions.

### 7. Monitoring & Logging
- Every successful call triggers a `StructuredLogger` event: `"api_call_success"`, capturing:
  - `input_tokens`
  - `output_tokens`
  - `estimated_cost` (this call)
  - `total_cost` (cumulative)
- Every retry triggers an `"api_call_retry"` event, capturing the attempt number and error string.
