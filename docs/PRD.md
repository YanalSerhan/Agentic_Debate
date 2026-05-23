# PRD.md — Product Requirements Document
## Exercise 02: AI Agent Debate System

**Course:** AI Agents (Dr. Yoram Segal)
**Assignment:** Exercise 02 — Debate between two AI agents supervised by a third (judge) agent
**Version:** 1.00
**Status:** ⬜ Draft — pending approval before development begins
**Related docs:** `docs/PLAN.md`, `docs/TODO.md`, `docs/PRD_debate_engine.md`, `docs/PRD_communication_protocol.md`, `docs/PRD_gatekeeper.md`

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [User Problem](#2-user-problem)
3. [Target Audience](#3-target-audience)
4. [Measurable Goals & KPIs](#4-measurable-goals--kpis)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Out of Scope](#7-out-of-scope)
8. [Assumptions & Dependencies](#8-assumptions--dependencies)
9. [Timeline & Milestones](#9-timeline--milestones)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. Project Overview

The **AI Agent Debate System** is a multi-agent orchestration application in which three independent AI agents — `ProAgent`, `ConAgent`, and `JudgeAgent` — conduct a structured, supervised debate on any user-provided topic.

- `ProAgent` argues **FOR** the topic using sourced arguments retrieved via web search.
- `ConAgent` argues **AGAINST** the topic, referencing and directly addressing the opponent's last argument.
- `JudgeAgent` acts as the **father/supervisor**: it routes all inter-agent communication (no agent may communicate directly with another), monitors the debate, enforces turn discipline, and delivers a binding final verdict.

The system demonstrates **multi-agent orchestration**, **structured IPC via JSON**, **resilience patterns** (gatekeeper, watchdog, structured logging), and the **skill-based agent architecture** taught in the course.

The entry point is a Python CLI (`uv run python src/main.py --topic "..."`) that initialises a `DebateSDK`, runs the debate, and prints the verdict and cost report to the terminal.

---

## 2. User Problem

University AI courses often describe multi-agent systems theoretically. This project provides a **concrete, working demonstration** of:

- How multiple autonomous AI agents can collaborate/compete on a shared task.
- How a supervisor (judge) agent can orchestrate child agents without allowing direct peer-to-peer communication.
- How production-grade concerns — rate limiting, retry logic, structured logging, process isolation, budget caps — are applied to an agentic system.
- How skills and tool use (web search) are integrated into each agent's workflow.

The problem solved is: **given a debate topic, automatically produce a multi-round, evidence-based, AI-driven debate with a decisive verdict**, without any human intervention once the topic is entered.

---

## 3. Target Audience

| Audience | Role |
|---|---|
| **Dr. Yoram Segal** | Primary evaluator — grades correctness, architecture, and adherence to course guidelines |
| **Course Evaluators / TAs** | Review code quality, test coverage, documentation completeness |
| **Development Team** | Student(s) implementing and testing the system |

The system is not a consumer product. It is an **academic submission** evaluated against explicit course criteria. All design decisions must therefore satisfy course guidelines as the primary constraint.

---

## 4. Measurable Goals & KPIs

| # | Goal | KPI | Pass Threshold |
|---|---|---|---|
| G1 | Debate runs end-to-end without manual intervention | Debate completes on `uv run python src/main.py --topic "..."` | 100% of runs complete or exit with error code 1 |
| G2 | Minimum number of debate exchanges | Round count in final transcript | ≥ 10 rounds (ping = argument, pong = counter-argument) |
| G3 | Judge delivers a decisive verdict | `VerdictMessage.winner` is `"pro"` or `"con"` | Never `null`, never `"tie"` |
| G4 | Every turn includes a web search | `sources` list in every `DebateTurnMessage` | ≥ 1 URL per turn, 0 exceptions |
| G5 | All inter-agent messages are valid JSON | Pydantic validation pass rate | 100% — zero invalid messages accepted |
| G6 | All API calls pass through the gatekeeper | Direct SDK calls outside `ApiGatekeeper.execute()` | 0 direct calls detected (verified by grep) |
| G7 | Structured logs are written correctly | JSONL log files in `results/logs/` | FIFO rotation at 500 lines; max 20 files enforced |
| G8 | Test coverage | `pytest --cov` result | ≥ 85% across `src/` |
| G9 | Code quality | `ruff check src/ tests/` exit code | 0 errors |
| G10 | No hardcoded secrets or values | Grep for keys, URLs, limits in `src/` | 0 matches |

---

## 5. Functional Requirements

### 5.1 Agent Architecture

The system consists of exactly **three agents**, each running as a separate OS process (`multiprocessing.Process`):

#### FR-01 — ProAgent
- Role: `AgentRole.PRO`
- **Always** argues FOR the debate topic.
- Uses `ArgumentSkill` (auto-selected by matching its `Description` to the task).
- Must include a mandatory web search tool call every turn to find supporting sources.
- Must address the opponent's (ConAgent's) last argument — sycophancy and capitulation are forbidden.
- Never communicates directly with ConAgent; all output is sent to JudgeAgent.

#### FR-02 — ConAgent
- Role: `AgentRole.CON`
- **Always** argues AGAINST the debate topic.
- Uses `CounterSkill` (auto-selected by `Description` matching).
- Must include a mandatory web search tool call every turn.
- Must directly reference and rebut ProAgent's last argument (not ignore it).
- Never communicates directly with ProAgent.

#### FR-03 — JudgeAgent (Father / Supervisor)
- Role: `AgentRole.JUDGE`
- Uses `JudgeSkill` to evaluate the debate at the end.
- **All inter-agent communication is routed exclusively through JudgeAgent.** The message flow is always: `ChildAgent → JudgeAgent → ChildAgent`. Direct `ProAgent ↔ ConAgent` communication is a **bug**.
- Orchestrates the debate loop: sends topic to ProAgent → relays ProAgent's turn to ConAgent → relays ConAgent's turn back to ProAgent → repeats until `max_rounds`.
- Validates that each agent's response references the opponent's last argument; if not, prompts the agent to retry.
- Monitors for per-turn timeouts; triggers Watchdog if an agent hangs.
- After `max_rounds`, invokes `JudgeSkill` with the full transcript to produce a `VerdictMessage`.
- The verdict is **never a tie** — JudgeAgent must pick PRO or CON. If scores are equal, winner is decided by rhetorical quality.

### 5.2 Skill-Based Architecture

#### FR-04 — Skill Auto-Selection
- Each agent has a list of `BaseSkill` instances.
- `BaseAgent.select_skill(task_description: str)` picks the skill whose `description` field best matches the incoming task. This is not a hard-coded dispatch — the agent reads the skill's `Description` and selects automatically.
- Each skill must have a unique, non-empty `description` stored in its `SKILL.md` file.

#### FR-05 — Skill Definitions

| Skill | Used By | Description |
|---|---|---|
| `ArgumentSkill` | ProAgent | "Constructs a well-sourced argument FOR the debate topic, citing internet sources." |
| `CounterSkill` | ConAgent | "Constructs a counter-argument AGAINST the debate topic, referencing the opponent's last argument." |
| `JudgeSkill` | JudgeAgent | "Evaluates debate arguments for persuasive power and delivers a final verdict. Does not score on factual accuracy." |

### 5.3 Communication Protocol

#### FR-06 — JSON Message Types
All messages between agents are structured JSON objects validated by Pydantic. Three message types exist:

**`DebateTurnMessage`** — produced by ProAgent or ConAgent each round:
```json
{
  "round": 3,
  "speaker": "pro",
  "argument": "AI reduces poverty because...",
  "sources": ["https://...", "https://..."]
}
```

**`JudgeRelayMessage`** — wraps a DebateTurnMessage for routing by JudgeAgent:
```json
{
  "from": "pro",
  "to": "con",
  "payload": { "...DebateTurnMessage..." }
}
```

**`VerdictMessage`** — produced by JudgeAgent after `max_rounds`:
```json
{
  "winner": "pro",
  "reasoning": "Pro's arguments were more persuasive because...",
  "score": { "pro": 7, "con": 6 }
}
```

#### FR-07 — Message Validation
- Every message must be validated by `validate_message()` in `shared/ipc.py` before it is acted upon.
- Malformed or invalid messages cause the receiving agent to log an error and request a retry from the sender.
- `VerdictMessage.winner` must be `"pro"` or `"con"` — any other value (including `null`) is a validation failure.

### 5.4 Debate Flow

#### FR-08 — Debate Loop
1. `DebateSDK.run_debate(topic)` is called.
2. JudgeAgent receives the topic and sends it to ProAgent via a `JudgeRelayMessage`.
3. ProAgent calls `ArgumentSkill`, performs a mandatory web search, and returns a `DebateTurnMessage` to JudgeAgent.
4. JudgeAgent wraps it in a `JudgeRelayMessage` and sends it to ConAgent.
5. ConAgent calls `CounterSkill`, performs a mandatory web search, and returns a `DebateTurnMessage` to JudgeAgent.
6. JudgeAgent logs both turns via `StructuredLogger`.
7. Steps 2–6 repeat until `max_rounds` (default: 10) are complete.
8. JudgeAgent calls `JudgeSkill.execute(transcript)` → receives `VerdictMessage`.
9. `VerdictMessage` is returned to `DebateSDK`, which returns it to the CLI.

#### FR-09 — Minimum Rounds
- The debate MUST complete at least 10 full rounds (configurable via `config/setup.json`).
- A "round" = one ProAgent turn + one ConAgent turn.
- If the API budget cap is reached before `max_rounds`, the debate halts gracefully with a `BudgetExceededError`.

#### FR-10 — Internet Search Requirement
- Every call to `ArgumentSkill.execute()` and `CounterSkill.execute()` MUST include a web search tool call to the Anthropic API.
- The `sources` field in the resulting `DebateTurnMessage` must contain at least one URL.
- A turn with an empty `sources` list is invalid and will be retried.

### 5.5 SDK Layer

#### FR-11 — DebateSDK (Single Entry Point)
All business logic is accessible exclusively through `DebateSDK`. No consumer (CLI, tests, GUI) may import internal modules directly.

```python
class DebateSDK:
    def __init__(self, config_path: str = "config/") -> None
    def run_debate(self, topic: str, rounds: int | None = None) -> VerdictMessage
    def get_transcript(self) -> list[DebateTurnMessage]
    def get_cost_report(self) -> dict
    def get_log_path(self) -> str
```

### 5.6 CLI Entry Point

#### FR-12 — `main.py`
- Parses CLI arguments: `--topic`, `--rounds`, `--config`.
- Instantiates `DebateSDK` and calls `sdk.run_debate(topic)`.
- Prints the verdict (winner, reasoning, scores) to the terminal.
- Prints the cost report (model, tokens in/out, total cost in USD).
- Exits with code `0` on success, code `1` on any unhandled error.
- Invoked as: `uv run python src/main.py --topic "Is artificial intelligence good for humanity?"`

---

## 6. Non-Functional Requirements

### 6.1 Language & Runtime

#### NFR-01 — Python Only
- The final submission must be a Python program, not a shell script or Claude CLI command.
- Claude CLI may be used only for development and manual testing purposes.
- All script and test execution uses `uv run`.

#### NFR-02 — Package Manager
- `uv` is the **only** permitted package manager. `pip install` and `python -m venv` are forbidden.
- Dependencies are declared in `pyproject.toml` and locked in `uv.lock`.
- Environment is reproduced with `uv sync`.

### 6.2 Communication & IPC

#### NFR-03 — JSON Structured Communication
- All inter-agent messages use JSON serialised over `multiprocessing.Queue`.
- No plain-text messages between agents.
- Messages are validated by Pydantic before use.

#### NFR-04 — Process Isolation
- Each agent runs in a separate `multiprocessing.Process` (not a thread).
- This ensures a crash in one agent does not kill the others.
- IPC exclusively via `multiprocessing.Queue`; no shared Python objects across processes.

### 6.3 Logging

#### NFR-05 — Structured Logs (JSONL)
- All logs are written in JSON Lines format (one JSON object per line).
- Log entry schema: `{ "timestamp": str, "level": str, "agent": str, "event": str, "data": dict }`
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- Log files are named: `results/logs/debate_YYYYMMDD_HHMMSS_NNN.jsonl`.

#### NFR-06 — FIFO Log Rotation
- When the current log file reaches **500 lines**, a new file is opened automatically.
- When **20 log files** exist, the oldest is deleted before a new one is created (FIFO).
- This behaviour must be covered by unit tests.

### 6.4 API Access & Rate Control

#### NFR-07 — API Gatekeeper (Mandatory)
- Every call to the Anthropic SDK must pass through `ApiGatekeeper.execute()`.
- **No module** other than `ApiGatekeeper` may call `anthropic.Anthropic().messages.create()` directly.
- This is enforced by code review and verified by grep during quality gate checks.

#### NFR-08 — Rate Limiting
- Rate limits are read from `config/rate_limits.json` (never hardcoded).
- Default limits: 30 requests/minute, 500 requests/hour, max 5 concurrent.
- When a limit is reached, the request is placed in a FIFO queue (thread-safe `queue.Queue`).
- Maximum queue depth is configurable.

#### NFR-09 — Retry Logic
- On transient API failure, the gatekeeper retries up to `max_retries` times.
- Backoff interval: `retry_after_seconds` (from config).
- Failure after max retries is logged and propagated as an exception.

#### NFR-10 — Budget Cap
- `ApiGatekeeper` tracks cumulative estimated token cost across all API calls.
- If the total cost exceeds the configured budget cap, `BudgetExceededError` is raised.
- The debate halts gracefully; all completed turns are preserved in the transcript.

### 6.5 Resilience

#### NFR-11 — Per-Call Timeouts
- Every API call has a timeout (value from config).
- A call that exceeds the timeout is treated as a transient failure and retried per NFR-09.

#### NFR-12 — Watchdog & Keep-Alive
- `Watchdog` monitors all agent sub-processes by PID.
- Agents emit keep-alive pings at a configurable interval.
- If an agent fails to ping within the timeout window, the Watchdog kills and restarts the process.
- Maximum restart attempts: configurable. Exceeding this limit raises `WatchdogGaveUpError`.
- All restart events are logged via `StructuredLogger`.

### 6.6 Configuration

#### NFR-13 — No Hardcoded Values
- No API URLs, keys, model names, rate limits, timeouts, or round counts may appear in source code.
- All such values must come from `config/*.json` files or environment variables.
- A grep for hardcoded values during quality gates must return zero matches.

#### NFR-14 — Configuration Files
| File | Contents |
|---|---|
| `config/setup.json` | `version`, `model`, `max_tokens`, `debate_topic`, `max_rounds` |
| `config/rate_limits.json` | `version`, rate limit settings per service |
| `config/logging_config.json` | `max_files=20`, `max_lines_per_file=500`, `log_dir` |

#### NFR-15 — Secrets Management
- The Anthropic API key is stored in `.env` only — never in source code.
- `.env` is listed in `.gitignore` and must never be committed.
- `.env-example` with placeholder values only is committed as a reference.

### 6.7 Code Quality

#### NFR-16 — File Size Limit
- Every source file must be ≤ 150 lines of code (comments and blank lines excluded).
- Files that exceed this limit must be split into sub-modules.

#### NFR-17 — Test-Driven Development (TDD)
- Unit tests must be written **before or alongside** the implementation (TDD discipline).
- Test coverage must be ≥ 85% across `src/` (`fail_under = 85` enforced in `pyproject.toml`).
- Tests use `pytest`; coverage via `pytest-cov`.

#### NFR-18 — Linting
- Linting enforced by `ruff` with:
  - `line-length = 100`
  - `target-version = "py310"`
  - Selected rules: `["E","F","W","I","N","UP","B","C4","SIM"]`
  - Ignored: `["E501"]`
- `ruff check src/ tests/` must return exit code 0 before submission.

#### NFR-19 — Docstrings
- Every public class and function must have a docstring.
- All variable and function names must be descriptive and written in English.

#### NFR-20 — No Code Duplication (DRY)
- Logic appearing in two or more files must be extracted to a shared base class or mixin.
- OOP inheritance and mixins must be used wherever appropriate.

---

## 7. Out of Scope

| Feature | Status | Notes |
|---|---|---|
| Graphical User Interface (GUI) | Out of scope | Optional bonus only; not required for full grade |
| Direct child-to-child communication | Permanently out of scope | Forbidden by design — any `ProAgent → ConAgent` direct call is a bug |
| Web deployment / server | Out of scope | Local CLI execution only |
| Persistent database | Out of scope | Debate transcripts saved as JSONL files in `results/` |
| Multi-language support | Out of scope | Code and docs in English (or Hebrew per assignment) |
| Real-time streaming output | Out of scope | Terminal output is printed after each round completes |
| Fine-tuned or custom LLM models | Out of scope | Uses Anthropic Claude API only (`claude-sonnet-4-20250514`) |

---

## 8. Assumptions & Dependencies

### 8.1 External Dependencies

| Dependency | Version | Purpose |
|---|---|---|
| Python | ≥ 3.10 | Runtime (required for `match`, `X \| Y` union syntax) |
| `uv` | Latest | Package manager and virtual environment management |
| `anthropic` | Latest stable | Anthropic Claude API client (messages + web_search tool) |
| `pydantic` | v2 | JSON message schema validation |
| `python-dotenv` | Latest stable | Loading `.env` secrets |
| `pytest` | Latest stable | Test runner |
| `pytest-cov` | Latest stable | Coverage reporting |
| `ruff` | Latest stable | Linting |

### 8.2 Assumptions

| # | Assumption |
|---|---|
| A1 | A valid `ANTHROPIC_API_KEY` with sufficient credits is available in the `.env` file |
| A2 | The Anthropic `claude-sonnet-4-20250514` model supports the `web_search` tool |
| A3 | The local machine has outbound HTTPS access to `api.anthropic.com` |
| A4 | `uv` is installed globally on the development machine |
| A5 | The debate topic is provided as a non-empty string via CLI or `.env` |
| A6 | If the API budget is limited, `max_rounds` may be reduced to 5 (documented in README, no grade penalty) |
| A7 | The system is run on a single local machine; distributed deployment is not required |

---

## 9. Timeline & Milestones

| Phase | Deliverable | Status |
|---|---|---|
| **Phase 1** | All project documents written and self-reviewed | ⬜ |
| **Phase 2** | Repository setup, package structure, configuration files, dependencies installed | ⬜ |
| **Phase 3** | Core shared infrastructure: `constants`, `ipc`, `config`, `logger`, `gatekeeper`, `watchdog` | ⬜ |
| **Phase 4** | Skills layer: `BaseSkill`, `ArgumentSkill`, `CounterSkill`, `JudgeSkill` | ⬜ |
| **Phase 5** | Agents layer: `BaseAgent`, `ProAgent`, `ConAgent`, `JudgeAgent` | ⬜ |
| **Phase 6** | SDK layer: `DebateSDK` | ⬜ |
| **Phase 7** | Main entry point and CLI | ⬜ |
| **Phase 8** | Integration tests: full debate flow, watchdog flow | ⬜ |
| **Phase 9** | Code quality gates: ruff clean, coverage ≥ 85%, no hardcoded values, no secrets | ⬜ |
| **Phase 10** | README, prompt log, architecture diagrams, cost analysis, screenshots | ⬜ |
| **Phase 11** | Final submission checklist complete — submit PDF link via Moodle | ⬜ |

> **Critical constraint:** No code may be written until Phase 1 documents are complete and approved (self-review checklist in TODO.md §1.7).

---

## 10. Acceptance Criteria

A submission is considered **accepted** only when ALL of the following are true:

### 10.1 Functional Acceptance

| # | Criterion |
|---|---|
| AC-01 | Running `uv run python src/main.py --topic "..."` completes end-to-end without crashing |
| AC-02 | The debate produces ≥ 10 rounds in the transcript |
| AC-03 | Every `DebateTurnMessage` contains a non-empty `sources` list (≥ 1 URL) |
| AC-04 | `VerdictMessage.winner` is exactly `"pro"` or `"con"` — never `null` or `"tie"` |
| AC-05 | ProAgent and ConAgent never communicate directly; all messages routed through JudgeAgent |
| AC-06 | Each agent used a different `Skill` and that skill was auto-selected by `Description` matching |
| AC-07 | The terminal prints the verdict (winner, reasoning, score) and cost report |

### 10.2 Non-Functional Acceptance

| # | Criterion |
|---|---|
| AC-08 | `ruff check src/ tests/` returns exit code 0 (zero linter errors) |
| AC-09 | `uv run pytest tests/ --cov=src --cov-report=term-missing` shows ≥ 85% coverage |
| AC-10 | JSONL log files are created in `results/logs/`; FIFO rotation verified by integration test |
| AC-11 | `grep -r "anthropic.Anthropic().messages.create" src/` returns 0 matches outside `gatekeeper.py` |
| AC-12 | `grep -rE "(sk-ant-|ANTHROPIC_API_KEY=sk)" src/ tests/` returns 0 matches |
| AC-13 | All source files are ≤ 150 lines of code |
| AC-14 | `.env` is not present in the committed repository |
| AC-15 | `uv sync` on a clean checkout installs all dependencies and `uv run python src/main.py --help` works |

### 10.3 Documentation Acceptance

| # | Criterion |
|---|---|
| AC-16 | `docs/PRD.md` — this document — is complete |
| AC-17 | `docs/PRD_debate_engine.md` is complete |
| AC-18 | `docs/PRD_communication_protocol.md` is complete |
| AC-19 | `docs/PRD_gatekeeper.md` is complete |
| AC-20 | `docs/PLAN.md` with C4 diagrams, UML diagrams, and ADRs is complete |
| AC-21 | `README.md` is complete with install guide, run instructions, and sample output |
| AC-22 | `prompts/prompt_log.md` documents all significant prompts used during development |

---

*© All rights reserved to Dr. Yoram Segal — student implementation document*
*PRD.md version 1.00 — to be approved before Phase 3 development begins (see TODO.md §1.7)*
