# PLAN.md — Architecture & Design Document
## Exercise 02: AI Agent Debate System

**Course:** AI Agents (Dr. Yoram Segal)
**Version:** 1.00
**Status:** ⬜ Draft — pending approval before development begins
**Related docs:** `docs/PRD.md`, `docs/TODO.md`, `docs/PRD_debate_engine.md`, `docs/PRD_communication_protocol.md`, `docs/PRD_gatekeeper.md`

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [C4 Model Diagrams](#2-c4-model-diagrams)
   - 2.1 Level 1 — Context
   - 2.2 Level 2 — Container
   - 2.3 Level 3 — Component
   - 2.4 Level 4 — Code (Key Classes)
3. [UML Diagrams](#3-uml-diagrams)
   - 3.1 Class Diagram
   - 3.2 Sequence Diagram — One Full Debate Round
   - 3.3 Deployment Diagram
4. [Architecture Decision Records (ADRs)](#4-architecture-decision-records-adrs)
5. [API / SDK Interface Documentation](#5-api--sdk-interface-documentation)
6. [Data Flow Summary](#6-data-flow-summary)
7. [Configuration & Secrets Architecture](#7-configuration--secrets-architecture)
8. [Error Handling & Resilience](#8-error-handling--resilience)

---

## 1. System Overview

The AI Agent Debate System is a multi-agent orchestration application in which three independent AI agents—`ProAgent`, `ConAgent`, and `JudgeAgent`—conduct a structured debate. All inter-agent communication is routed exclusively through the `JudgeAgent` (the "father"), which relays messages between the two debating child agents. The debate runs for a minimum of 10 rounds. At the end, the judge delivers a binding verdict based on persuasive power.

**Key architectural constraints (from assignment and course guidelines):**

- All business logic is exposed exclusively through `DebateSDK`
- All Anthropic API calls pass through `ApiGatekeeper` — no bypass allowed
- Agents are OS processes (`multiprocessing`), not threads
- Inter-agent messages use structured JSON (not plain text)
- Every source file is ≤ 150 lines of code
- No hardcoded values — all configuration from `config/*.json`
- No secrets in source code — environment variables only
- Package manager: `uv` exclusively

---

## 2. C4 Model Diagrams

### 2.1 Level 1 — Context Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       SYSTEM CONTEXT                         │
│                                                              │
│   ┌───────────┐        ┌──────────────────────────────────┐ │
│   │   User /  │        │     AI Agent Debate System       │ │
│   │ Evaluator │──────▶ │  (debate-agents Python package)  │ │
│   │           │  CLI   │                                  │ │
│   └───────────┘  args  │  Orchestrates 3 AI agents that   │ │
│                        │  conduct a structured debate on  │ │
│                        │  any topic and deliver a verdict │ │
│                        └──────────────┬───────────────────┘ │
│                                       │ HTTPS / REST         │
│                                       ▼                      │
│                        ┌─────────────────────────────────┐  │
│                        │     Anthropic Claude API        │  │
│                        │  (claude-sonnet-4-20250514)     │  │
│                        │  + web_search tool              │  │
│                        └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Actors:**
- **User / Evaluator** — runs the system via CLI, provides the debate topic
- **Anthropic Claude API** — external LLM provider powering all three agents and the web search tool

---

### 2.2 Level 2 — Container Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI Agent Debate System                           │
│                                                                      │
│  ┌──────────────┐    ┌─────────────────────────────────────────────┐│
│  │  CLI Entry   │    │              DebateSDK Container            ││
│  │  (main.py)  │───▶│  Single public entry point for all logic    ││
│  │             │    │  Initialises agents, gatekeeper, logger,    ││
│  └──────────────┘    │  watchdog. Returns VerdictMessage.          ││
│                      └──────────────────┬────────────────────────--┘│
│                                         │ spawns                    │
│             ┌───────────────────────────┼──────────────────────┐    │
│             ▼                           ▼                      ▼    │
│  ┌─────────────────┐     ┌──────────────────────┐  ┌───────────────┐│
│  │  JudgeAgent     │     │     ProAgent          │  │  ConAgent     ││
│  │  Process        │◀───▶│     Process           │  │  Process      ││
│  │  (supervisor)   │ IPC │  (argues FOR topic)   │  │ (argues AGAINST││
│  └────────┬────────┘     └──────────────────────┘  └───────────────┘│
│           │                                                          │
│           ▼                                                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     Shared Infrastructure                      │ │
│  │  ApiGatekeeper | StructuredLogger | ConfigManager | Watchdog   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                  │                                   │
│                                  ▼                                   │
│                     ┌────────────────────────┐                      │
│                     │  config/*.json         │                      │
│                     │  .env (secrets)        │                      │
│                     │  results/logs/*.jsonl  │                      │
│                     └────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Level 3 — Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          DebateSDK                                    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                        SDK Layer                               │  │
│  │   sdk/sdk.py  →  DebateSDK                                     │  │
│  │   run_debate() | get_transcript() | get_cost_report()          │  │
│  └──────────────────────────────┬─────────────────────────────────┘  │
│                                 │                                     │
│          ┌──────────────────────┼────────────────────┐               │
│          ▼                      ▼                     ▼               │
│  ┌──────────────┐    ┌──────────────────┐   ┌───────────────────┐   │
│  │  JudgeAgent  │    │    ProAgent      │   │    ConAgent       │   │
│  │  ├ JudgeSkill│    │    ├ ArgumentSkill│   │    ├ CounterSkill │   │
│  │  └ orchestrate│   │    └ web_search  │   │    └ web_search   │   │
│  └──────┬───────┘    └──────────────────┘   └───────────────────┘   │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Shared Infrastructure                      │   │
│  │                                                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │
│  │  │ ApiGatekeeper│  │  ipc.py      │  │ StructuredLogger  │   │   │
│  │  │ rate limits  │  │  JSON schemas│  │ FIFO / JSONL      │   │   │
│  │  │ FIFO queue   │  │  validation  │  │ 20 files max      │   │   │
│  │  │ retry logic  │  │  Pydantic    │  │ 500 lines each    │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │   │
│  │                                                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │
│  │  │ ConfigManager│  │  Watchdog    │  │  constants.py    │   │   │
│  │  │ setup.json   │  │  keep-alive  │  │  AgentRole Enum  │   │   │
│  │  │ rate_limits  │  │  auto-restart│  │  MessageType Enum│   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 2.4 Level 4 — Code Level (Key Class Responsibilities)

| Class | File | Responsibility |
|---|---|---|
| `DebateSDK` | `sdk/sdk.py` | Single public entry point; initialises all components |
| `BaseAgent` | `agents/base_agent.py` | Abstract agent: skill selection, API routing via gatekeeper |
| `ProAgent` | `agents/pro_agent.py` | Argues FOR the topic using `ArgumentSkill` |
| `ConAgent` | `agents/con_agent.py` | Argues AGAINST the topic using `CounterSkill` |
| `JudgeAgent` | `agents/judge_agent.py` | Orchestrates debate loop; routes all messages; delivers verdict |
| `BaseSkill` | `skills/base_skill.py` | Abstract skill: `execute()`, `validate_input()`, `description` |
| `ArgumentSkill` | `skills/argument_skill/` | Builds a sourced FOR-argument with web search |
| `CounterSkill` | `skills/counter_skill/` | Builds a sourced AGAINST-argument referencing opponent's last turn |
| `JudgeSkill` | `skills/judge_skill/` | Scores full transcript by persuasive power; returns `VerdictMessage` |
| `ApiGatekeeper` | `shared/gatekeeper.py` | Rate limiting, FIFO queue, retry, budget cap, logging of all API calls |
| `StructuredLogger` | `shared/logger.py` | JSONL logging, FIFO file rotation (20 files × 500 lines) |
| `ConfigManager` | `shared/config.py` | Loads and validates all `config/*.json` files; typed getters |
| `Watchdog` | `shared/watchdog.py` | Monitors agent processes; restarts on timeout or crash |
| `ipc.py` | `shared/ipc.py` | Pydantic message schemas + `validate_message()` |
| `constants.py` | `debate/constants.py` | `AgentRole`, `MessageType`, `DebateStatus` Enums |

---

## 3. UML Diagrams

### 3.1 Class Diagram

```
                    ┌─────────────────────────┐
                    │       BaseAgent          │
                    │─────────────────────────│
                    │ + role: AgentRole        │
                    │ + skills: list[BaseSkill]│
                    │─────────────────────────│
                    │ + select_skill(task)     │
                    │ + run(context) [abstract]│
                    │ # _call_api(prompt)      │
                    └────────────┬────────────┘
                                 │ inherits
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│    ProAgent      │  │    ConAgent      │  │   JudgeAgent     │
│──────────────────│  │──────────────────│  │──────────────────│
│ role = PRO       │  │ role = CON       │  │ role = JUDGE     │
│──────────────────│  │──────────────────│  │──────────────────│
│ + run(context)   │  │ + run(context)   │  │ + run_debate()   │
│                  │  │                  │  │ + relay(msg)     │
│ uses▼            │  │ uses▼            │  │ + deliver_verdict│
│ ArgumentSkill    │  │ CounterSkill     │  │ uses▼            │
└──────────────────┘  └──────────────────┘  │ JudgeSkill       │
                                             └──────────────────┘

                    ┌─────────────────────────┐
                    │       BaseSkill          │
                    │─────────────────────────│
                    │ + description: str       │
                    │─────────────────────────│
                    │ + execute(ctx) [abstract]│
                    │ + validate_input(ctx)    │
                    └────────────┬────────────┘
                                 │ inherits
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ ArgumentSkill    │  │  CounterSkill    │  │   JudgeSkill     │
│──────────────────│  │──────────────────│  │──────────────────│
│ + execute(ctx)   │  │ + execute(ctx)   │  │ + execute(ctx)   │
│ + validate_input │  │ + validate_input │  │ + score_round()  │
└──────────────────┘  └──────────────────┘  └──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      DebateSDK                               │
│─────────────────────────────────────────────────────────────│
│ - judge: JudgeAgent                                          │
│ - pro: ProAgent                                              │
│ - con: ConAgent                                              │
│ - gatekeeper: ApiGatekeeper                                  │
│ - logger: StructuredLogger                                   │
│ - config: ConfigManager                                      │
│ - watchdog: Watchdog                                         │
│─────────────────────────────────────────────────────────────│
│ + run_debate(topic, rounds) -> VerdictMessage                │
│ + get_transcript() -> list[DebateTurnMessage]                │
│ + get_cost_report() -> dict                                  │
│ + get_log_path() -> str                                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────────────────┐
│    ApiGatekeeper     │    │         StructuredLogger          │
│──────────────────────│    │──────────────────────────────────│
│ - config: RateLimits │    │ - current_file: Path             │
│ - queue: Queue       │    │ - line_count: int                │
│──────────────────────│    │ - file_count: int                │
│ + execute(fn, *args) │    │──────────────────────────────────│
│ + get_queue_status() │    │ + log(level, agent, event, data) │
└──────────────────────┘    │ - _rotate_if_needed()            │
                             └──────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     Pydantic Message Models (ipc.py)          │
│──────────────────────────────────────────────────────────────│
│  DebateTurnMessage   │  JudgeRelayMessage  │  VerdictMessage  │
│  - round: int        │  - from_agent: str  │  - winner: Role  │
│  - speaker: Role     │  - to_agent: str    │  - reasoning: str│
│  - argument: str     │  - payload: Turn    │  - score: dict   │
│  - sources: list[str]│                     │                  │
└──────────────────────────────────────────────────────────────┘
```

---

### 3.2 Sequence Diagram — One Full Debate Round

```
User/CLI    DebateSDK   JudgeAgent   ProAgent    ConAgent   ApiGatekeeper  AnthropicAPI
   │            │            │           │            │            │             │
   │─run_debate─▶            │           │            │            │             │
   │            │─start_round▶           │            │            │             │
   │            │            │─send_topic▶            │            │             │
   │            │            │           │─_call_api──▶            │             │
   │            │            │           │            │─execute()──▶             │
   │            │            │           │            │            │─POST /msgs──▶
   │            │            │           │            │            │◀──response──│
   │            │            │           │◀──DebateTurnMessage─────│             │
   │            │            │◀─pro_turn─│            │            │             │
   │            │            │─relay_to_con────────────▶           │             │
   │            │            │           │            │─_call_api──▶             │
   │            │            │           │            │            │─POST /msgs──▶
   │            │            │           │            │            │◀──response──│
   │            │            │◀──────────con_turn──────│            │             │
   │            │            │─log_round()             │            │             │
   │            │            │  (repeat for max_rounds)│            │             │
   │            │            │─JudgeSkill.execute()    │            │             │
   │            │            │─_call_api──────────────────────────▶│             │
   │            │            │                         │            │─POST /msgs──▶
   │            │            │                         │            │◀──response──│
   │            │◀─VerdictMessage────────────────────────────────────             │
   │◀─verdict───│            │           │            │            │             │
```

**Communication rule enforced:** `ProAgent` and `ConAgent` never communicate directly. Every message is routed through `JudgeAgent`. Direct child-to-child calls are a bug.

---

### 3.3 Deployment Diagram — Local Process Tree

```
┌───────────────────────────────────────────────────────────┐
│                   Local Machine                            │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Main Process (PID: N)                               │  │
│  │  uv run python src/main.py --topic "..."             │  │
│  │                                                       │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  DebateSDK                                     │  │  │
│  │  │  + ConfigManager (reads config/*.json)         │  │  │
│  │  │  + ApiGatekeeper (rate limits + FIFO queue)    │  │  │
│  │  │  + StructuredLogger (writes results/logs/)     │  │  │
│  │  │  + Watchdog (monitors child PIDs)              │  │  │
│  │  └────────────────┬───────────────────────────────┘  │  │
│  │                   │ multiprocessing.Process.start()   │  │
│  │       ┌───────────┼───────────────┐                  │  │
│  │       ▼           ▼               ▼                  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐            │  │
│  │  │ProAgent │ │ConAgent │ │ JudgeAgent  │            │  │
│  │  │(PID: N+1│ │(PID: N+2│ │ (PID: N+3)  │            │  │
│  │  └─────────┘ └─────────┘ └─────────────┘            │  │
│  │                                                       │  │
│  │  IPC via: multiprocessing.Queue (JSON messages)       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  File system:                                             │
│  ├── config/setup.json          (read-only at runtime)    │
│  ├── config/rate_limits.json    (read-only at runtime)    │
│  ├── .env                       (secrets, git-ignored)    │
│  └── results/logs/*.jsonl       (written at runtime)      │
│                                                            │
│  External:                                                │
│  └── api.anthropic.com (HTTPS outbound only)              │
└───────────────────────────────────────────────────────────┘
```

---

## 4. Architecture Decision Records (ADRs)

### ADR-01 — JSON over Plain Text for IPC

**Status:** Accepted
**Context:** Agents need to exchange structured data (round number, speaker role, argument text, cited sources). The lecture notes specify a structured communication protocol (slide 8.8: "JSON format — structured, can be monitored and verified, saves tokens").
**Decision:** All inter-agent messages use Pydantic-validated JSON objects serialised to JSON strings. Message types: `DebateTurnMessage`, `JudgeRelayMessage`, `VerdictMessage`.
**Consequences:**
- ✅ Messages are machine-readable and can be validated before processing
- ✅ Logs are parseable by any JSON tool
- ✅ Error in one line of JSONL does not corrupt the entire log file
- ✅ Enables automated testing of message structure
- ❌ Slight overhead vs. plain text; negligible at this scale

---

### ADR-02 — Multiprocessing over Multithreading for Agent Isolation

**Status:** Accepted
**Context:** Three agents run concurrently. The course guidelines (software submission guidelines §15.1) state that `multiprocessing` is suited to CPU-bound or isolation-sensitive tasks, while `multithreading` is suited for I/O-bound tasks. The lecture notes frame agents as OS processes (slide 2: "Agent = Process").
**Decision:** Each agent runs in a separate `multiprocessing.Process`. IPC uses `multiprocessing.Queue` for message passing.
**Consequences:**
- ✅ True process isolation — a crash in one agent does not kill others
- ✅ Watchdog can monitor PIDs and restart a dead process
- ✅ Matches the lecture's conceptual model exactly (Agent = Process)
- ✅ No GIL contention
- ❌ Higher memory overhead than threads; acceptable for 3 processes
- ❌ Cannot share Python objects directly; all data must be serialised (JSON over Queue)

---

### ADR-03 — Gatekeeper Pattern for All API Calls

**Status:** Accepted
**Context:** The course guidelines (§5.1) mandate a centralised `ApiGatekeeper` through which every external API call must pass. Direct calls to the Anthropic SDK anywhere in the codebase (except inside `ApiGatekeeper.execute()`) are forbidden.
**Decision:** `ApiGatekeeper` is the sole point that calls `anthropic.Anthropic().messages.create()`. All agents call `gatekeeper.execute(api_fn, *args)`. The gatekeeper enforces rate limits, queuing, retry, budget cap, and logging.
**Consequences:**
- ✅ Single place to change rate limit policy
- ✅ Accurate token-cost accounting across all agents
- ✅ Easy to mock in unit tests (mock `gatekeeper.execute`)
- ✅ Prevents runaway API spend
- ❌ Slight latency added by queue check; negligible at debate timescales

---

## 5. API / SDK Interface Documentation

### 5.1 `DebateSDK` — Public Interface

```python
class DebateSDK:
    """
    Single public entry point for the AI Agent Debate System.
    All consumers (CLI, tests) must use this interface exclusively.

    Args:
        config_path: Path to the config directory (default: "config/")
    """

    def __init__(self, config_path: str = "config/") -> None: ...

    def run_debate(self, topic: str, rounds: int | None = None) -> VerdictMessage:
        """
        Run a full debate on the given topic.

        Args:
            topic: The debate proposition (e.g. "AI is good for humanity")
            rounds: Override max_rounds from config (optional)

        Returns:
            VerdictMessage with winner ("pro"|"con"), reasoning, and score dict

        Raises:
            BudgetExceededError: if API cost cap is hit before debate ends
            WatchdogGaveUpError: if an agent process cannot be restarted
            DebateTimeoutError: if a round exceeds the configured timeout
        """

    def get_transcript(self) -> list[DebateTurnMessage]:
        """Return all debate turns in order."""

    def get_cost_report(self) -> dict:
        """
        Return token usage and cost breakdown.
        Format: {"model": str, "input_tokens": int, "output_tokens": int,
                 "total_cost_usd": float, "per_round": list[dict]}
        """

    def get_log_path(self) -> str:
        """Return path to the current structured log file."""
```

### 5.2 Message Schema Reference

```python
# DebateTurnMessage — produced by ProAgent or ConAgent each round
{
    "round": 3,                      # int, 1-indexed
    "speaker": "pro",                # "pro" | "con"
    "argument": "AI reduces poverty because...",  # str, non-empty
    "sources": ["https://...", "https://..."]      # list[str], ≥1 required
}

# JudgeRelayMessage — wraps a DebateTurnMessage for routing
{
    "from": "pro",
    "to": "con",
    "payload": { ...DebateTurnMessage... }
}

# VerdictMessage — produced by JudgeAgent after max_rounds
{
    "winner": "pro",                 # "pro" | "con" — never null or "tie"
    "reasoning": "Pro's arguments were...",
    "score": { "pro": 7, "con": 6 }
}
```

### 5.3 `ApiGatekeeper` Interface

```python
class ApiGatekeeper:
    def __init__(self, config: ConfigManager) -> None: ...

    def execute(self, api_call: Callable, *args, **kwargs) -> Any:
        """
        Execute any Anthropic API call through the gatekeeper.
        Enforces rate limits, queuing, retry, budget cap, and logging.
        This is the ONLY place that calls the Anthropic SDK directly.
        """

    def get_queue_status(self) -> QueueStatus:
        """Return current queue depth and stats."""
```

---

## 6. Data Flow Summary

```
CLI args (topic, rounds)
        │
        ▼
  DebateSDK.run_debate(topic)
        │
        ├─ ConfigManager loads config/*.json
        ├─ Watchdog starts monitoring
        ├─ JudgeAgent.run_debate(topic) ──spawns──▶ ProAgent Process
        │                                ──spawns──▶ ConAgent Process
        │
        │  For each round (1 to max_rounds):
        │
        ├─ Judge ──JudgeRelayMessage──▶ ProAgent
        │            ProAgent ──ArgumentSkill.execute()──▶ Anthropic API (via Gatekeeper)
        │            ProAgent ◀── LLM response (argument + sources)
        │            ProAgent ──DebateTurnMessage──▶ Judge
        │
        ├─ Judge ──JudgeRelayMessage──▶ ConAgent
        │            ConAgent ──CounterSkill.execute()──▶ Anthropic API (via Gatekeeper)
        │            ConAgent ◀── LLM response (counter-argument + sources)
        │            ConAgent ──DebateTurnMessage──▶ Judge
        │
        ├─ Judge logs both turns (StructuredLogger → JSONL)
        │
        │  After max_rounds:
        │
        ├─ Judge ──JudgeSkill.execute(transcript)──▶ Anthropic API (via Gatekeeper)
        │                                         ◀── VerdictMessage
        │
        └─ DebateSDK returns VerdictMessage to CLI
                  │
                  ├─ CLI prints verdict + cost report to terminal
                  └─ Logs written to results/logs/*.jsonl
```

**Forbidden data flows (enforced by design):**
- `ProAgent` → `ConAgent` (direct) — **FORBIDDEN**
- Any module → `anthropic.Anthropic().messages.create()` (direct) — **FORBIDDEN**
- Any hardcoded API key in source — **FORBIDDEN**

---

## 7. Configuration & Secrets Architecture

```
config/
├── setup.json          # Model, max_rounds, max_tokens, debate_topic (versioned)
├── rate_limits.json    # requests_per_minute, requests_per_hour, retry policy (versioned)
└── logging_config.json # max_files=20, max_lines_per_file=500, log_dir

.env                    # ANTHROPIC_API_KEY=... (git-ignored, never committed)
.env-example            # ANTHROPIC_API_KEY=your_key_here (committed, placeholder only)

src/debate/constants.py # AgentRole, MessageType, DebateStatus Enums (immutable)
src/debate/shared/version.py  # __version__ = "1.00"
```

**Rule:** No value that can change between environments or deployments may appear in source code. All such values live in `config/*.json` or `.env`.

---

## 8. Error Handling & Resilience

| Failure Scenario | Detection | Recovery |
|---|---|---|
| Agent API call times out | `asyncio.timeout` / `signal.alarm` on every `gatekeeper.execute()` | Retry up to `max_retries` with `retry_after_seconds` backoff |
| Agent process crashes | Watchdog monitors PID; detects missing keep-alive | Kill and restart process; resume from last logged turn |
| Watchdog exhausts retries | `WatchdogGaveUpError` raised | Propagates to `DebateSDK`; logged; CLI exits with code 1 |
| Malformed JSON from LLM | `validate_message()` raises `ValidationError` | Log error; request agent to retry the turn |
| Budget cap exceeded | `ApiGatekeeper` tracks cumulative cost | Raises `BudgetExceededError`; debate halts gracefully |
| Rate limit hit | `ApiGatekeeper` checks limit before each call | Route to FIFO queue; block caller until slot available |
| Log file rotation | `StructuredLogger` counts lines per file | On 500 lines: open new file. On 20 files: delete oldest (FIFO) |
| Agent refuses to counter | `JudgeAgent` checks that opponent's argument is referenced | Flags turn as invalid; prompts agent to retry with explicit instruction |

---

*© All rights reserved to Dr. Yoram Segal — student implementation document*
*PLAN.md version 1.00 — to be approved before Phase 3 development begins (see TODO.md §1.7)*
