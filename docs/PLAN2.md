# PLAN.md — Architecture Document
## Exercise 02: AI Agent Debate System

**Course:** AI Agents (Dr. Yoram Segal)
**Authors:** Exercise 02 Team
**Version:** 1.00
**Status:** Draft → In Review

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [C4 Model Diagrams](#2-c4-model-diagrams)
   - 2.1 [Level 1 — Context Diagram](#21-level-1--context-diagram)
   - 2.2 [Level 2 — Container Diagram](#22-level-2--container-diagram)
   - 2.3 [Level 3 — Component Diagram](#23-level-3--component-diagram)
   - 2.4 [Level 4 — Code Diagram (Key Classes)](#24-level-4--code-diagram-key-classes)
3. [UML Sequence Diagram — One Full Debate Round](#3-uml-sequence-diagram--one-full-debate-round)
4. [UML Class Diagram](#4-uml-class-diagram)
5. [Deployment Diagram — Local Process Tree](#5-deployment-diagram--local-process-tree)
6. [Data Flow Summary](#6-data-flow-summary)
7. [API / SDK Interface Documentation](#7-api--sdk-interface-documentation)
8. [Architecture Decision Records (ADRs)](#8-architecture-decision-records-adrs)
   - ADR-01: JSON over Plain Text for IPC
   - ADR-02: Multiprocessing over Multithreading
   - ADR-03: Gatekeeper Pattern for API Calls
   - ADR-04: Pydantic for Message Validation
   - ADR-05: uv as Package Manager
9. [Directory Structure & Module Responsibilities](#9-directory-structure--module-responsibilities)
10. [Configuration Strategy](#10-configuration-strategy)
11. [Logging Strategy](#11-logging-strategy)
12. [Error Handling & Resilience Strategy](#12-error-handling--resilience-strategy)
13. [Security Considerations](#13-security-considerations)
14. [Testing Strategy](#14-testing-strategy)
15. [Open Questions & Future Decisions](#15-open-questions--future-decisions)

---

## 1. System Overview

The **AI Agent Debate System** is a Python multi-agent orchestration platform that simulates a structured, autonomous debate between two opposing AI agents, supervised by a third judge agent. It is built as a professional-grade software system demonstrating:

- Hierarchical agent orchestration
- Structured JSON-based IPC (Inter-Process Communication)
- API gatekeeper pattern for cost and rate control
- Watchdog-monitored autonomous processes
- Rotating structured logs
- Full TDD development methodology

### Core Actors

| Actor | Role | Description |
|-------|------|-------------|
| `JudgeAgent` | Orchestrator / Father | Manages all turns, routes messages, enforces rules, delivers final verdict |
| `ProAgent` | Debater (FOR) | Argues in favor of the debate topic using internet-backed evidence |
| `ConAgent` | Debater (AGAINST) | Argues against the debate topic, rebuts ProAgent with sourced counter-claims |
| Human Operator | CLI / SDK caller | Provides the debate topic, triggers execution, reads verdict |

### Core Invariants

- Child agents **never communicate directly** — all messages route through `JudgeAgent`
- **Minimum 10 ping-pong exchanges** per debate
- **No tie** verdicts — the judge must always pick a winner
- **Every agent turn** must include an internet search (mandatory tool use)
- **All configuration** comes from `config/*.json` or `.env` — no hardcoded values

---

## 2. C4 Model Diagrams

### 2.1 Level 1 — Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SYSTEM CONTEXT                               │
│                                                                     │
│   ┌─────────────┐                                                   │
│   │   Human     │  --topic "..."-->  ┌──────────────────────────┐   │
│   │  Operator   │                   │   AI Agent Debate System  │   │
│   │  (CLI/SDK)  │  <---verdict---   │   (Python Application)   │   │
│   └─────────────┘                   └──────────┬───────────────┘   │
│                                                │                   │
│                                    ┌───────────▼────────────┐      │
│                                    │   Anthropic Claude API │      │
│                                    │   (External LLM)       │      │
│                                    └────────────────────────┘      │
│                                                │                   │
│                                    ┌───────────▼────────────┐      │
│                                    │   Web Search API       │      │
│                                    │   (Tavily / SerpAPI)   │      │
│                                    └────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

**External Systems:**
- **Anthropic Claude API**: LLM backbone for all three agents
- **Web Search API**: Each agent turn must include internet evidence retrieval (Tavily or SerpAPI)
- **File System**: Structured JSONL log files written to `results/logs/`

---

### 2.2 Level 2 — Container Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      AI Agent Debate System                              │
│                                                                          │
│  ┌─────────────────┐   SDK calls    ┌────────────────────────────────┐  │
│  │   CLI / main.py │ ─────────────> │        DebateSDK               │  │
│  │  (Entry Point)  │ <─ verdict ─── │  (Single Public Interface)     │  │
│  └─────────────────┘                └──────────────┬─────────────────┘  │
│                                                    │                    │
│                          ┌─────────────────────────▼──────────────────┐ │
│                          │          JudgeAgent (Orchestrator)         │ │
│                          │   - Manages debate session lifecycle       │ │
│                          │   - Routes all inter-agent messages        │ │
│                          │   - Enforces turn order & ping count       │ │
│                          │   - Delivers final verdict (no tie)        │ │
│                          └──────────┬──────────────────┬─────────────┘ │
│                                     │ relays           │ relays        │
│                          ┌──────────▼──────┐  ┌────────▼───────────┐  │
│                          │    ProAgent     │  │     ConAgent       │  │
│                          │  (Argues FOR)   │  │  (Argues AGAINST)  │  │
│                          │  ArgumentSkill  │  │   CounterSkill     │  │
│                          └────────┬────────┘  └────────┬───────────┘  │
│                                   │                    │              │
│                    ┌──────────────▼────────────────────▼────────────┐ │
│                    │            Shared Infrastructure                │ │
│                    │  ApiGatekeeper | StructuredLogger | Watchdog    │ │
│                    │  ConfigManager | IPC Message Bus                │ │
│                    └──────────────────────────────────┬─────────────┘ │
│                                                       │               │
│                    ┌──────────────────────────────────▼─────────────┐ │
│                    │               LLM SDK Layer                    │ │
│                    │      (Anthropic / OpenAI / Gemini adapter)     │ │
│                    └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Level 3 — Component Diagram

```
src/debate/
├── sdk/
│   └── sdk.py ──────────────────────────► DebateSDK
│                                           ├── run_debate(topic)
│                                           ├── get_transcript()
│                                           └── get_cost_report()
│
├── agents/
│   ├── base_agent.py ───────────────────► BaseAgent (abstract)
│   │                                       ├── select_skill(task)
│   │                                       ├── run(context)
│   │                                       └── _call_api(prompt) → Gatekeeper
│   ├── judge_agent.py ──────────────────► JudgeAgent(BaseAgent)
│   │                                       ├── orchestrate_debate()
│   │                                       ├── relay_message()
│   │                                       └── deliver_verdict()
│   ├── pro_agent.py ────────────────────► ProAgent(BaseAgent)
│   │                                       └── run() → ArgumentSkill
│   └── con_agent.py ────────────────────► ConAgent(BaseAgent)
│                                           └── run() → CounterSkill
│
├── skills/
│   ├── base_skill.py ───────────────────► BaseSkill (abstract)
│   │                                       ├── description: str
│   │                                       ├── execute(context)
│   │                                       └── validate_input(context)
│   ├── argument_skill/ ─────────────────► ArgumentSkill(BaseSkill)
│   │   ├── SKILL.md  ← "Constructs a well-sourced argument FOR the debate topic, citing internet sources."
│   │   └── argument_skill.py
│   ├── counter_skill/ ──────────────────► CounterSkill(BaseSkill)
│   │   ├── SKILL.md  ← "Constructs a counter-argument AGAINST the debate topic, referencing the opponent's last argument."
│   │   └── counter_skill.py
│   └── judge_skill/ ────────────────────► JudgeSkill(BaseSkill)
│       ├── SKILL.md  ← "Evaluates debate arguments for persuasive power and delivers a final verdict. Does not score on factual accuracy."
│       └── judge_skill.py
│
├── shared/
│   ├── gatekeeper.py ───────────────────► ApiGatekeeper
│   │                                       ├── execute(api_call, ...)
│   │                                       ├── get_queue_status()
│   │                                       └── enforce_budget_cap()
│   ├── config.py ───────────────────────► ConfigManager
│   │                                       ├── get_model()
│   │                                       ├── get_max_rounds()
│   │                                       └── get_rate_limits()
│   ├── logger.py ───────────────────────► StructuredLogger
│   │                                       ├── log(level, event, data)
│   │                                       └── FIFO rotation (20 files × 500 lines)
│   ├── watchdog.py ─────────────────────► Watchdog
│   │                                       ├── monitor(process)
│   │                                       └── restart_on_failure()
│   └── ipc.py ──────────────────────────► Message Schemas (Pydantic)
│                                           ├── DebateTurnMessage
│                                           ├── JudgeRelayMessage
│                                           └── VerdictMessage
│
└── constants.py ────────────────────────► AgentRole, MessageType, DebateStatus enums
```

---

### 2.4 Level 4 — Code Diagram (Key Classes)

```
BaseAgent (abstract)
│  role: AgentRole
│  skills: list[BaseSkill]
│  gatekeeper: ApiGatekeeper
│  logger: StructuredLogger
│  config: ConfigManager
│
│  + select_skill(task: str) → BaseSkill
│  + run(context: dict) → str           [abstract]
│  # _call_api(prompt: str) → str       [routes through gatekeeper ONLY]
│
├─► JudgeAgent
│     + orchestrate_debate(topic: str) → VerdictMessage
│     + relay_message(msg: JudgeRelayMessage) → None
│     + deliver_verdict(transcript: list) → VerdictMessage
│     + _enforce_no_tie(verdict: VerdictMessage) → VerdictMessage
│
├─► ProAgent
│     + run(context: dict) → DebateTurnMessage
│     # _build_argument_prompt(topic, opponent_arg, round_num) → str
│
└─► ConAgent
      + run(context: dict) → DebateTurnMessage
      # _build_counter_prompt(topic, opponent_arg, round_num) → str
```

---

## 3. UML Sequence Diagram — One Full Debate Round

```
Human     DebateSDK    JudgeAgent    ProAgent     ConAgent    AnthropicAPI   WebSearch
  │           │             │            │            │             │             │
  │ run_debate│             │            │            │             │             │
  │──────────►│             │            │            │             │             │
  │           │orchestrate()│            │            │             │             │
  │           │────────────►│            │            │             │             │
  │           │             │            │            │             │             │
  │           │   ── ROUND N ─────────────────────────────────────────────────── │
  │           │             │            │            │             │             │
  │           │             │ relay(topic│            │             │             │
  │           │             │ + con_prev)│            │             │             │
  │           │             │───────────►│            │             │             │
  │           │             │            │ web_search │             │             │
  │           │             │            │────────────────────────────────────────►│
  │           │             │            │◄───────────────────────────────────────│
  │           │             │            │ _call_api()│             │             │
  │           │             │            │────────────────────────►│             │
  │           │             │            │◄───────────────────────│             │
  │           │             │            │ DebateTurn │             │             │
  │           │             │◄───────────│            │             │             │
  │           │             │ log(turn)  │            │             │             │
  │           │             │            │            │             │             │
  │           │             │ relay(pro_ │            │             │             │
  │           │             │  argument) │            │             │             │
  │           │             │────────────────────────►│             │             │
  │           │             │            │            │ web_search  │             │
  │           │             │            │            │─────────────────────────►│
  │           │             │            │            │◄─────────────────────────│
  │           │             │            │            │ _call_api() │             │
  │           │             │            │            │─────────────►│            │
  │           │             │            │            │◄─────────────│            │
  │           │             │            │ DebateTurn │             │             │
  │           │             │◄───────────────────────│             │             │
  │           │             │ log(turn)  │            │             │             │
  │           │             │            │            │             │             │
  │           │   ── ROUND N+1 (repeats until max_rounds) ─────────────────────  │
  │           │             │            │            │             │             │
  │           │   ── VERDICT PHASE ──────────────────────────────────────────── │
  │           │             │ judge_skill│            │             │             │
  │           │             │ .execute() │            │             │             │
  │           │             │────────────────────────────────────►│             │
  │           │             │◄───────────────────────────────────│             │
  │           │ VerdictMsg  │            │            │             │             │
  │           │◄────────────│            │            │             │             │
  │ verdict   │             │            │            │             │             │
  │◄──────────│             │            │            │             │             │
```

**Key Invariants Visible in Sequence:**
- `ProAgent` and `ConAgent` **never interact directly** — all arrows pass through `JudgeAgent`
- Every agent call fans out to both `WebSearch` AND `AnthropicAPI`
- `JudgeAgent` logs every turn immediately after receipt
- Verdict is generated only after all rounds complete

---

## 4. UML Class Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                          <<abstract>>                             │
│                           BaseSkill                               │
│───────────────────────────────────────────────────────────────────│
│  + description: str                                               │
│───────────────────────────────────────────────────────────────────│
│  + execute(context: dict) → str           [abstract]              │
│  + validate_input(context: dict) → None   [abstract]              │
└───────────────────────────────────────────────────────────────────┘
          ▲                   ▲                      ▲
          │                   │                      │
┌─────────┴──────┐  ┌─────────┴──────┐  ┌───────────┴──────┐
│ ArgumentSkill  │  │  CounterSkill  │  │   JudgeSkill     │
│────────────────│  │────────────────│  │──────────────────│
│description:str │  │description:str │  │description:str   │
│────────────────│  │────────────────│  │──────────────────│
│+execute()→str  │  │+execute()→str  │  │+execute()→str    │
│+validate()     │  │+validate()     │  │ Returns Verdict  │
└────────────────┘  └────────────────┘  └──────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                          <<abstract>>                             │
│                           BaseAgent                               │
│───────────────────────────────────────────────────────────────────│
│  + role: AgentRole                                                │
│  + skills: list[BaseSkill]                                        │
│  - _gatekeeper: ApiGatekeeper                                     │
│  - _logger: StructuredLogger                                      │
│  - _config: ConfigManager                                         │
│───────────────────────────────────────────────────────────────────│
│  + select_skill(task: str) → BaseSkill                            │
│  + run(context: dict) → str              [abstract]               │
│  # _call_api(prompt: str) → str                                   │
└───────────────────────────────────────────────────────────────────┘
     ▲                    ▲                        ▲
     │                    │                        │
┌────┴────────┐  ┌────────┴────────┐  ┌────────────┴──────────────┐
│  JudgeAgent │  │   ProAgent      │  │       ConAgent            │
│─────────────│  │─────────────────│  │───────────────────────────│
│role: JUDGE  │  │role: PRO        │  │role: CON                  │
│─────────────│  │─────────────────│  │───────────────────────────│
│+orchestrate │  │+run(ctx)        │  │+run(ctx)                  │
│+relay_msg() │  │ →DebateTurnMsg  │  │ →DebateTurnMsg            │
│+deliver_    │  └─────────────────┘  └───────────────────────────┘
│  verdict()  │
│+_enforce_   │
│  no_tie()   │
└─────────────┘

┌───────────────────────────┐  ┌──────────────────────────────────┐
│     ApiGatekeeper         │  │        StructuredLogger          │
│───────────────────────────│  │──────────────────────────────────│
│-_rate_limits: dict        │  │-_current_file: Path              │
│-_queue: Queue             │  │-_line_count: int                 │
│-_budget_used: float       │  │-_file_index: int                 │
│───────────────────────────│  │──────────────────────────────────│
│+execute(fn, *args) →any   │  │+log(level, agent, event, data)   │
│+get_queue_status()→Status │  │-_rotate_if_needed()              │
│+get_cost_report()→dict    │  │-_delete_oldest_if_over_limit()   │
└───────────────────────────┘  └──────────────────────────────────┘

┌────────────────────────────┐  ┌───────────────────────────────────┐
│       ConfigManager        │  │           Watchdog                │
│────────────────────────────│  │───────────────────────────────────│
│-_setup: dict               │  │-_processes: dict[str,Process]     │
│-_rate_limits: dict         │  │-_max_restarts: int                │
│────────────────────────────│  │-_restart_counts: dict             │
│+get_model()→str            │  │───────────────────────────────────│
│+get_max_rounds()→int       │  │+monitor(name, fn, args)           │
│+get_rate_limits()→dict     │  │+stop_all()                        │
│+get_log_config()→dict      │  │-_restart(name)                    │
│+get_budget_cap()→float     │  │-_keep_alive_loop()                │
└────────────────────────────┘  └───────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      Pydantic Message Models                       │
├──────────────────────┬─────────────────────┬───────────────────────┤
│   DebateTurnMessage  │  JudgeRelayMessage   │    VerdictMessage     │
│──────────────────────│─────────────────────│───────────────────────│
│session_id: str       │from_agent: str       │winner: AgentRole      │
│round: int            │to_agent: str         │reasoning: str         │
│speaker: AgentRole    │payload:              │score: dict[str,int]   │
│argument: str         │  DebateTurnMessage   │session_id: str        │
│sources: list[str]    │timestamp: str        │timestamp: str         │
│timestamp: str        │                      │                       │
└──────────────────────┴─────────────────────┴───────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                           DebateSDK                              │
│──────────────────────────────────────────────────────────────────│
│-_judge: JudgeAgent                                               │
│-_pro: ProAgent                                                   │
│-_con: ConAgent                                                   │
│-_gatekeeper: ApiGatekeeper                                       │
│-_logger: StructuredLogger                                        │
│-_watchdog: Watchdog                                              │
│-_config: ConfigManager                                           │
│──────────────────────────────────────────────────────────────────│
│+run_debate(topic, rounds?) → VerdictMessage                      │
│+get_transcript() → list[DebateTurnMessage]                       │
│+get_cost_report() → dict                                         │
│+get_log_path() → str                                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Deployment Diagram — Local Process Tree

```
┌──────────────────────────────────────────────────────────────────┐
│  Host Machine (Developer Laptop)                                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Python Runtime (uv virtual environment)                   │  │
│  │                                                            │  │
│  │   Process: main.py (PID: parent)                          │  │
│  │   ┌─────────────────────────────────────────────────────┐ │  │
│  │   │  DebateSDK                                          │ │  │
│  │   │   ├── JudgeAgent (main thread)                      │ │  │
│  │   │   │     ├── IPC MessageBus (threading.Queue)        │ │  │
│  │   │   │     └── JudgeSkill                              │ │  │
│  │   │   │                                                 │ │  │
│  │   │   ├── ProAgent  (multiprocessing.Process)          │ │  │
│  │   │   │     └── ArgumentSkill                          │ │  │
│  │   │   │                                                 │ │  │
│  │   │   ├── ConAgent  (multiprocessing.Process)          │ │  │
│  │   │   │     └── CounterSkill                           │ │  │
│  │   │   │                                                 │ │  │
│  │   │   ├── ApiGatekeeper (shared, thread-safe)          │ │  │
│  │   │   ├── StructuredLogger (thread-safe, FIFO)         │ │  │
│  │   │   └── Watchdog (background thread)                 │ │  │
│  │   └─────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  File System:                                              │  │
│  │   ├── config/setup.json        (read-only at startup)     │  │
│  │   ├── config/rate_limits.json  (read-only at startup)     │  │
│  │   ├── .env                     (read-only at startup)     │  │
│  │   └── results/logs/*.jsonl     (written during runtime)   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │  External Network                                           ││
│  │   ├── api.anthropic.com  (HTTPS, port 443)                  ││
│  │   └── api.tavily.com     (HTTPS, port 443)                  ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

**Process Isolation Model:**
- `JudgeAgent` runs in the **main process** — it owns the debate loop
- `ProAgent` and `ConAgent` run as **`multiprocessing.Process`** instances — true isolation
- `Watchdog` runs as a **background `threading.Thread`** inside the main process
- IPC between processes uses **`multiprocessing.Queue`** (not threading.Queue)
- `ApiGatekeeper` and `StructuredLogger` are **shared within each process** (not cross-process singletons)

---

## 6. Data Flow Summary

### 6.1 Startup Flow

```
1. Human → CLI → main.py --topic "..." --rounds 10
2. main.py → DebateSDK.__init__(config_path)
3. DebateSDK → ConfigManager.load() → reads config/*.json + .env
4. DebateSDK → ApiGatekeeper.__init__(rate_limits)
5. DebateSDK → StructuredLogger.__init__(log_config)
6. DebateSDK → JudgeAgent(gatekeeper, logger, config)
7. DebateSDK → ProAgent(gatekeeper, logger, config) + spawn Process
8. DebateSDK → ConAgent(gatekeeper, logger, config) + spawn Process
9. DebateSDK → Watchdog.monitor([pro_process, con_process])
10. DebateSDK → JudgeAgent.orchestrate_debate(topic)
```

### 6.2 Debate Turn Flow

```
Turn N (Pro speaks):
  JudgeAgent
    → builds JudgeRelayMessage(from=JUDGE, to=PRO, payload={topic, con_prev_arg})
    → places on pro_inbox queue
  ProAgent (in subprocess)
    → reads from pro_inbox queue
    → select_skill("argue FOR topic") → ArgumentSkill
    → ArgumentSkill.execute({topic, opponent_arg, round_num})
      → web_search(topic + opponent_arg)  [mandatory]
      → _call_api(prompt)  [through ApiGatekeeper]
      → returns DebateTurnMessage(round=N, speaker=PRO, argument=..., sources=[...])
    → places DebateTurnMessage on judge_inbox queue
  JudgeAgent
    → reads from judge_inbox queue
    → validates JSON schema (Pydantic)
    → logs turn (StructuredLogger)
    → appends to transcript list
    → proceeds to Con's turn
```

### 6.3 Verdict Flow

```
After max_rounds:
  JudgeAgent
    → JudgeSkill.execute({transcript: list[DebateTurnMessage]})
      → builds evaluation prompt from full transcript
      → _call_api(evaluation_prompt) [through ApiGatekeeper]
      → parses VerdictMessage from LLM response
      → enforces no-tie rule (picks higher scorer if equal → rhetorical quality tiebreaker)
    → logs VerdictMessage
    → returns VerdictMessage to DebateSDK
  DebateSDK
    → returns VerdictMessage to main.py
  main.py
    → prints formatted verdict to terminal
    → prints cost report
    → exit code 0
```

---

## 7. API / SDK Interface Documentation

### 7.1 DebateSDK — Public Interface

```python
class DebateSDK:
    """Single public entry point for all debate system functionality.

    All external callers (CLI, GUI, tests) MUST use this class.
    No internal module should be imported directly by callers.
    """

    def __init__(self, config_path: str = "config/") -> None:
        """Initialize the SDK, load all config, spin up agents and infrastructure.

        Args:
            config_path: Path to config directory containing setup.json and rate_limits.json.

        Raises:
            ConfigError: If required config files are missing or malformed.
            EnvironmentError: If required environment variables (e.g., ANTHROPIC_API_KEY) are absent.
        """

    def run_debate(self, topic: str, rounds: int | None = None) -> VerdictMessage:
        """Run a full debate on the given topic.

        Args:
            topic: The debate proposition (e.g., "Is AI good for humanity?").
            rounds: Number of ping-pong rounds. Defaults to config value (min 10).

        Returns:
            VerdictMessage: Structured verdict with winner (PRO|CON), reasoning, scores.

        Raises:
            DebateError: If debate cannot be completed (all retries exhausted).
            BudgetExceededError: If API budget cap is hit before debate ends.
        """

    def get_transcript(self) -> list[DebateTurnMessage]:
        """Return all recorded debate turns in chronological order."""

    def get_cost_report(self) -> dict:
        """Return token usage and estimated cost breakdown by agent and round.

        Returns:
            {
                "total_input_tokens": int,
                "total_output_tokens": int,
                "estimated_cost_usd": float,
                "per_agent": {"pro": {...}, "con": {...}, "judge": {...}},
                "per_round": [{"round": int, "tokens": int, "cost": float}, ...]
            }
        """

    def get_log_path(self) -> str:
        """Return absolute path to the current session's log file."""
```

### 7.2 Message Schemas (Pydantic)

Canonical schema definitions from TODO.md §1.3 — all validated via `shared/ipc.py`:

**`debate_turn`** — emitted by ProAgent / ConAgent each round:
```python
class DebateTurnMessage(BaseModel):
    session_id: str
    round: int                  # 1-indexed
    speaker: AgentRole          # AgentRole.PRO | AgentRole.CON  ("pro" | "con")
    argument: str               # The actual argument text
    sources: list[str]          # URLs from web search (min 1 required)
    timestamp: str              # ISO 8601
```

**`judge_relay`** — emitted by JudgeAgent when routing a turn to the next debater:
```python
class JudgeRelayMessage(BaseModel):
    session_id: str
    from_agent: str             # "judge_agent"
    to_agent: str               # "pro_agent" | "con_agent"
    payload: DebateTurnMessage  # The turn being relayed (the opponent's last argument)
    instruction: str            # Context/instruction for the receiving agent
    timestamp: str
```

**`verdict`** — emitted by JudgeAgent after all rounds complete:
```python
class VerdictMessage(BaseModel):
    session_id: str
    winner: AgentRole           # NEVER TIE — always PRO or CON
    reasoning: str              # Full explanation of the verdict
    score: dict[str, int]       # {"pro": int, "con": int} — winner has the higher value
    timestamp: str
```

**`validate_message()`** — entry point for all inbound JSON parsing:
```python
def validate_message(raw: str) -> DebateTurnMessage | JudgeRelayMessage | VerdictMessage:
    """Parse raw JSON string and return the appropriate validated Pydantic model.

    Raises:
        MessageValidationError: If the JSON is malformed or fails schema validation.
    """
```

### 7.3 ApiGatekeeper — Internal Interface

```python
class ApiGatekeeper:
    """Rate-limiting and cost-control wrapper for all external API calls.

    EVERY external API call in the system MUST go through execute().
    Direct SDK/HTTP calls outside this class are forbidden.
    """

    def execute(self, api_call: Callable, *args, **kwargs) -> Any:
        """Execute an API call through the gatekeeper.

        Enforces: rate limits, retry logic, budget cap, logging.
        """

    def get_queue_status(self) -> QueueStatus:
        """Return current queue depth, processing rate, backpressure state."""

    def get_cost_report(self) -> dict:
        """Return cumulative token usage and cost estimates."""
```

---

## 8. Architecture Decision Records (ADRs)

---

### ADR-01: JSON over Plain Text for IPC

**Status:** Accepted
**Date:** 2026-05-22

**Context:**
Agents need to exchange structured information (round number, speaker identity, argument text, source URLs, session ID, timestamps). This information has multiple fields with different types and validation requirements.

**Decision:**
Use structured JSON (validated via Pydantic models) for all inter-agent messages, not raw text strings or Python objects.

**Rationale:**
- JSON is self-describing — a message can be inspected, logged, and validated without additional context
- Pydantic provides compile-time-like type safety at runtime without boilerplate
- JSON is wire-format compatible — the same message format works for in-process queues, sockets, and future REST/gRPC expansion
- Structured messages enable systematic validation: schema violations are caught before an agent acts on bad data
- JSON logs are directly parseable by tools like `jq`, Splunk, Datadog — professional observability standard
- Dr. Segal's assignment explicitly requires JSON communication format

**Consequences:**
- Small serialization overhead per message (negligible at 10 rounds)
- All agents must serialize/deserialize (handled by Pydantic — one-liner)
- Schema changes require migration (versioned message format recommended)

**Alternatives Rejected:**
- Raw strings: no structure, no validation, error-prone parsing
- Python objects (pickle): process-unsafe, security risk, not portable
- CSV: no nested structures, no type safety

---

### ADR-02: Multiprocessing over Multithreading for Agent Isolation

**Status:** Accepted
**Date:** 2026-05-22

**Context:**
ProAgent and ConAgent are autonomous actors that make blocking external API calls (Anthropic, web search). They need to run independently so one agent's latency or crash doesn't block the other.

**Decision:**
Run `ProAgent` and `ConAgent` as `multiprocessing.Process` instances, not as `threading.Thread` instances.

**Rationale:**
- Python's GIL prevents true parallelism with threads for CPU-bound or I/O-bound tasks at the Python bytecode level
- Processes provide true memory isolation — a crash in `ProAgent` does not corrupt `ConAgent`'s state
- The Watchdog can use `process.is_alive()` and `process.exitcode` for reliable health checking — threads lack these guarantees
- Multiprocessing forces clean message-passing (via `multiprocessing.Queue`) rather than shared state — aligns with the assignment's "no direct communication" requirement
- Assignment explicitly lists "multiprocessing IPC" as a production-grade communication mechanism
- Subprocess isolation maps naturally to the hierarchical Parent → Child mental model in the assignment

**Consequences:**
- Higher memory overhead (each process loads Python interpreter)
- IPC must be serializable (solved by JSON/Pydantic)
- Shared resources (logger, gatekeeper) cannot be naively shared — each process gets its own instance, with logs written to the same rotating file set

**Alternatives Rejected:**
- `asyncio` coroutines: suitable for I/O concurrency but lacks true isolation; crash in one coroutine can corrupt entire event loop
- `threading.Thread`: GIL limits parallelism; shared memory makes it harder to enforce the "no direct communication" invariant

---

### ADR-03: Gatekeeper Pattern for API Calls

**Status:** Accepted
**Date:** 2026-05-22

**Context:**
The system makes multiple Anthropic API calls (2 per debate round × 10 rounds = 20+ calls minimum) plus web search calls. Without control, costs can spiral, rate limits can be exceeded, and failed calls can crash the debate.

**Decision:**
Introduce an `ApiGatekeeper` class as the single, mandatory entry point for ALL external API calls. No module may call `anthropic.Anthropic().messages.create()` or any HTTP client directly.

**Rationale:**
- Centralized control point enables rate-limit enforcement without duplicating logic in each agent
- Retry logic (exponential backoff) implemented once, tested once, applied everywhere
- Budget cap enforcement is only possible if all calls are centralized
- Every API call is logged with token counts and cost estimates — impossible without centralization
- Dr. Segal's assignment explicitly requires a "Gatekeeper — economic and consumption barrier layer"
- SOLID Single Responsibility: API communication policy belongs to one class, not scattered across agents

**Consequences:**
- All API calls are slightly more verbose (wrapped in `gatekeeper.execute(lambda: ...)`)
- Gatekeeper becomes a potential bottleneck — mitigated by async queue design
- If Gatekeeper crashes, all agents stop — mitigated by Watchdog and try/except in Gatekeeper itself

**Alternatives Rejected:**
- Per-agent rate limiting: duplicated logic, inconsistent enforcement, harder to test
- No rate limiting: unacceptable — costs could exceed budget in minutes
- Middleware decorators: harder to test, opaque to callers

---

### ADR-04: Pydantic for Message Validation

**Status:** Accepted
**Date:** 2026-05-22

**Context:**
LLM responses are inherently unpredictable. Agents may return malformed JSON, missing fields, or wrong types. The debate system must handle this gracefully without crashing.

**Decision:**
Use `pydantic` v2 `BaseModel` for all inter-agent message schemas. Validation is applied at every deserialization point.

**Rationale:**
- Pydantic v2 provides fast, declarative validation with clear error messages
- Type annotations serve as live documentation of the message contract
- `model_validate_json()` replaces `json.loads()` + manual checks in one call
- Validation errors are caught and logged — JudgeAgent can retry or flag the offending agent
- Pydantic is already listed as a project dependency

**Consequences:**
- Minor learning curve for team members unfamiliar with Pydantic
- Schema changes require updating model classes (desirable — enforces intentional change)

---

### ADR-05: uv as Package Manager

**Status:** Accepted
**Date:** 2026-05-22

**Context:**
The assignment requires a reproducible Python environment that any evaluator can set up with a single command.

**Decision:**
Use `uv` (Astral) as the exclusive package manager. `pip` and `venv` are forbidden.

**Rationale:**
- `uv` resolves and installs dependencies 10-100× faster than `pip`
- `uv.lock` provides deterministic, reproducible installs — same versions on every machine
- `pyproject.toml` is the modern Python packaging standard (PEP 517/518/621)
- `uv run python src/main.py` executes scripts inside the virtual environment without explicit activation
- Assignment explicitly mandates `uv` and `pyproject.toml`

**Consequences:**
- Evaluator must have `uv` installed (installation: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `uv.lock` must be committed to the repository

---

## 9. Directory Structure & Module Responsibilities

```
Agentic_Debate/
│
├── src/
│   └── debate/
│       ├── __init__.py              # Exports __version__, DebateSDK
│       ├── constants.py             # Enums: AgentRole, MessageType, DebateStatus
│       │
│       ├── sdk/
│       │   └── sdk.py               # DebateSDK — ONLY public interface
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base_agent.py        # Abstract BaseAgent; _call_api routes via gatekeeper
│       │   ├── judge_agent.py       # JudgeAgent: orchestrates, relays, verdicts
│       │   ├── pro_agent.py         # ProAgent: argues FOR, uses ArgumentSkill
│       │   └── con_agent.py         # ConAgent: argues AGAINST, uses CounterSkill
│       │
│       ├── skills/
│       │   ├── __init__.py
│       │   ├── base_skill.py        # Abstract BaseSkill; description + execute()
│       │   ├── argument_skill/
│       │   │   ├── SKILL.md         # Description for auto-selection
│       │   │   └── argument_skill.py
│       │   ├── counter_skill/
│       │   │   ├── SKILL.md
│       │   │   └── counter_skill.py
│       │   └── judge_skill/
│       │       ├── SKILL.md
│       │       └── judge_skill.py
│       │
│       ├── shared/
│       │   ├── __init__.py
│       │   ├── gatekeeper.py        # ApiGatekeeper: rate limits, retries, budget
│       │   ├── config.py            # ConfigManager: loads JSON config + env vars
│       │   ├── logger.py            # StructuredLogger: JSONL, FIFO rotation
│       │   ├── watchdog.py          # Watchdog: monitors processes, restarts on failure
│       │   ├── ipc.py               # Pydantic message models + validate_message()
│       │   └── version.py           # __version__ = "1.00"
│       │
│       └── commands/
│           ├── __init__.py
│           └── debate_command.md    # Saved prompt for manual /debate CLI testing
│
├── tests/
│   ├── unit/
│   │   ├── conftest.py              # Shared fixtures (mock gatekeeper, config, logger)
│   │   ├── test_agents/
│   │   │   ├── test_base_agent.py
│   │   │   ├── test_judge_agent.py
│   │   │   ├── test_pro_agent.py
│   │   │   ├── test_con_agent.py
│   │   │   └── test_sdk.py          # DebateSDK unit tests (§6.1 of TODO)
│   │   ├── test_skills/
│   │   │   ├── test_base_skill.py
│   │   │   ├── test_argument_skill.py
│   │   │   ├── test_counter_skill.py
│   │   │   └── test_judge_skill.py
│   │   └── test_shared/
│   │       ├── test_constants.py
│   │       ├── test_ipc.py
│   │       ├── test_config.py
│   │       ├── test_logger.py
│   │       ├── test_gatekeeper.py
│   │       └── test_watchdog.py
│   └── integration/
│       ├── test_debate_flow.py      # Full end-to-end with mocked Anthropic API
│       └── test_watchdog_flow.py    # Watchdog restart + resume integration test
│
├── config/
│   ├── setup.json                   # Model, max_rounds, max_tokens, budget_cap
│   ├── rate_limits.json             # RPM, RPH, retry config per service
│   └── logging_config.json          # Max files, max lines, log directory
│
├── data/                            # Sample debate topics (JSON)
├── results/
│   └── logs/                        # Rotating JSONL logs written at runtime
├── assets/                          # Screenshots, architecture diagram exports
├── prompts/
│   └── prompt_log.md                # Prompt engineering log
├── docs/
│   ├── PRD.md
│   ├── PRD_debate_engine.md
│   ├── PRD_communication_protocol.md
│   ├── PRD_gatekeeper.md
│   ├── PLAN.md                      # This file
│   └── TODO.md
│
├── README.md
├── pyproject.toml
├── uv.lock
├── .env-example
└── .gitignore
```

---

### 9a. pyproject.toml Configuration

The project uses a single `pyproject.toml` at the repository root for all build, lint, test, and coverage tooling.

```toml
[project]
name = "debate-agents"
version = "1.00"
description = "AI multi-agent debate system — Exercise 02 (Dr. Yoram Segal)"
requires-python = ">=3.10"

[project.dependencies]
anthopic = "*"
python-dotenv = "*"
pydantic = "*"

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/gui/*"]

[tool.coverage.report]
fail_under = 85

[tool.pytest.ini_options]
testpaths = ["tests"]
verbose = true
```

> **Never use `pip install` directly.** All dependency management goes through `uv`:
> ```bash
> uv add anthropic python-dotenv pydantic          # runtime deps
> uv add --dev pytest pytest-cov ruff freezegun    # dev deps
> uv sync                                          # install everything
> ```

---

### Module Dependency Rules

```
ALLOWED IMPORTS (top → bottom only):

main.py
  └──► sdk.py
         └──► agents/ (judge, pro, con)
                └──► skills/ (argument, counter, judge)
                       └──► shared/ (gatekeeper, logger, config, ipc)
                              └──► constants.py
                                     └──► (no imports from project)

FORBIDDEN:
  - shared/ importing from agents/ or skills/
  - skills/ importing from agents/
  - agents/ importing from sdk/
  - main.py importing from agents/, skills/, or shared/ directly
```

---

## 10. Configuration Strategy

All runtime parameters are loaded from the following sources (in priority order):

| Priority | Source | Examples |
|----------|--------|---------|
| 1 (highest) | Environment variables (`.env`) | `ANTHROPIC_API_KEY`, `DEBATE_TOPIC` |
| 2 | `config/setup.json` | `model`, `max_rounds`, `max_tokens`, `budget_cap_usd` |
| 3 | `config/rate_limits.json` | `requests_per_minute`, `max_retries`, `retry_after_seconds` |
| 4 | `config/logging_config.json` | `max_files`, `max_lines_per_file`, `log_directory` |
| 5 (lowest) | `constants.py` Enums | Role names, message type strings (never numeric limits) |

**`config/setup.json`** — main app config (versioned, committed to git):
```json
{
  "version": "1.00",
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1000,
  "debate_topic": "",
  "max_rounds": 10
}
```
> `debate_topic` may be left blank here and overridden by the `DEBATE_TOPIC` env var or `--topic` CLI flag.

**`config/rate_limits.json`** — API rate limits (versioned, committed to git):
```json
{
  "version": "1.00",
  "services": {
    "default": {
      "requests_per_minute": 30,
      "requests_per_hour": 500,
      "concurrent_max": 5,
      "retry_after_seconds": 30,
      "max_retries": 3
    }
  }
}
```
> The `"default"` service key applies to all API providers unless overridden per-service in future versions.

**`config/logging_config.json`** — log rotation settings (versioned, committed to git):
```json
{
  "version": "1.00",
  "log_directory": "results/logs",
  "max_files": 20,
  "max_lines_per_file": 500,
  "rotation_policy": "fifo"
}
```

**`.env-example`** — placeholder file committed to git (never the real `.env`):
```
ANTHROPIC_API_KEY=your_key_here
DEBATE_TOPIC=Is artificial intelligence good for humanity?
```

---

## 11. Logging Strategy

### Log Format (JSONL — one JSON object per line)

```json
{
  "timestamp": "2026-05-22T15:30:00.123Z",
  "level": "INFO",
  "agent": "judge_agent",
  "session_id": "abc-123",
  "event": "debate_turn_received",
  "round": 3,
  "data": {
    "speaker": "pro_agent",
    "argument_length": 420,
    "sources_count": 3,
    "tokens_used": 312
  }
}
```

### Log Event Taxonomy

| Event | Level | Description |
|-------|-------|-------------|
| `debate_session_started` | INFO | Topic, session_id, config snapshot |
| `debate_turn_sent` | INFO | Which agent received relay, round number |
| `debate_turn_received` | INFO | Speaker, argument length, source count |
| `api_call_started` | DEBUG | Model, prompt tokens estimate |
| `api_call_completed` | INFO | Tokens in/out, cost, latency |
| `api_call_failed` | ERROR | Exception type, retry count |
| `rate_limit_hit` | WARNING | Queue depth, wait time |
| `budget_cap_warning` | WARNING | % of budget used |
| `budget_cap_exceeded` | ERROR | Total spent, cap, session_id |
| `watchdog_restart` | WARNING | Process name, restart count, reason |
| `watchdog_gave_up` | ERROR | Max restarts exceeded |
| `verdict_delivered` | INFO | Winner, scores, reasoning length |
| `debate_session_ended` | INFO | Duration, total tokens, total cost |

### FIFO Rotation Policy

- Log files: `results/logs/debate_YYYYMMDD_HHMMSS_NNN.jsonl`
- Rotate when: current file reaches **500 lines**
- Maximum files: **20**
- When limit reached: delete oldest file, create new file
- Thread-safe: uses `threading.Lock` around file operations

---

## 12. Error Handling & Resilience Strategy

### Exception Hierarchy

```
DebateSystemError (base)
├── ConfigError          — missing/malformed config file
├── EnvironmentError     — missing required env var
├── MessageValidationError — invalid JSON schema from agent
├── AgentTimeoutError    — agent exceeded timeout_seconds
├── BudgetExceededError  — API cost cap hit
├── WatchdogGaveUpError  — max restart attempts exhausted
└── DebateError          — unrecoverable debate flow error
```

### Retry Policy (via ApiGatekeeper)

| Scenario | Max Retries | Backoff | Action After Exhaustion |
|---------|-------------|---------|------------------------|
| Anthropic API 429 (rate limit) | 3 | 30s, 60s, 120s | Raise `BudgetExceededError` |
| Anthropic API 500 (server error) | 3 | 5s, 15s, 30s | Raise `DebateError` |
| Web search timeout | 2 | 10s, 20s | Continue without sources (log warning) |
| Agent response timeout | 3 | 0s (immediate restart) | Watchdog restarts process |
| Malformed JSON from agent | 2 | 0s (re-prompt) | Log error, skip turn, continue |

### Watchdog Behaviour

```
Every 5 seconds:
  for process in [pro_process, con_process]:
    if not process.is_alive():
      if restart_count[process] < max_restarts:
        restart_count[process] += 1
        restart(process)
        log(WARNING, "watchdog_restart", {...})
      else:
        raise WatchdogGaveUpError(f"Process {process.name} failed {max_restarts} times")
```

---

## 13. Security Considerations

| Risk | Mitigation |
|------|------------|
| API key exposure | Keys only in `.env`; `.env` in `.gitignore`; `.env-example` has placeholders only |
| Secrets in logs | Logger redacts any value containing `key`, `secret`, `token` in key name |
| Prompt injection | Agent prompts include role-locking prefix; LLM outputs validated before use |
| Budget runaway | `ApiGatekeeper` enforces `budget_cap_usd` hard stop |
| Process escape | Child agents run as `multiprocessing.Process`, limited to standard library + project deps |
| Dependency supply chain | `uv.lock` pins exact versions; `pyproject.toml` pins minimum versions |

---

## 14. Testing Strategy

### Philosophy: TDD — Tests Written Before Code

Every module follows: **write failing test → implement code → green → refactor**

### Test Pyramid

```
         ┌───────────────┐
         │  Integration  │  2 files, ~15 tests
         │     Tests     │  (full debate flow, watchdog)
         ├───────────────┤
         │  Unit Tests   │  ~12 files, ~80+ tests
         │  (per module) │  (each class tested in isolation)
         └───────────────┘
```

### Coverage Requirements

| Module | Target Coverage |
|--------|----------------|
| `shared/gatekeeper.py` | ≥ 90% |
| `shared/ipc.py` | ≥ 95% |
| `shared/config.py` | ≥ 90% |
| `shared/logger.py` | ≥ 85% |
| `agents/*.py` | ≥ 85% |
| `skills/*.py` | ≥ 85% |
| Overall | ≥ 85% |

### Mocking Strategy

- **Anthropic API**: Mocked via `unittest.mock.patch` on `gatekeeper.execute()`
- **Web Search API**: Mocked via fixture returning `[{"url": "...", "snippet": "..."}]`
- **Time**: Mocked via `freezegun` for rate-limit and timeout tests
- **File System**: Tmp directories via `pytest`'s `tmp_path` fixture
- **Multiprocessing**: Integration tests use `multiprocessing.Process` directly; unit tests mock agent `run()`

### Key Test Cases

```python
# tests/integration/test_debate_flow.py

def test_full_debate_runs_10_rounds():
    """End-to-end: all 10 rounds complete with mocked Anthropic API."""

def test_verdict_is_never_tie():
    """Judge always picks PRO or CON — VerdictMessage.winner is never None or 'tie'."""

def test_all_messages_are_valid_json():
    """Every DebateTurnMessage in transcript validates against Pydantic schema."""

def test_gatekeeper_invoked_for_every_api_call():
    """Mock gatekeeper.execute() and assert call count == expected API calls (no bypass)."""

def test_logs_written_and_rotated():
    """After 500 lines, logger creates new file. After 20 files, oldest deleted (FIFO)."""

def test_cost_report_is_generated():
    """DebateSDK.get_cost_report() returns non-empty dict after debate completes."""

def test_no_direct_agent_to_agent_communication():
    """Assert ProAgent and ConAgent queues are never written to by each other."""


# tests/integration/test_watchdog_flow.py

def test_watchdog_restarts_crashed_agent():
    """Simulate agent process crash → assert watchdog restarts and debate resumes."""

def test_watchdog_raises_after_max_restarts():
    """Simulate repeated agent crashes → assert WatchdogGaveUpError is raised."""
```

### SDK Unit Tests (tests/unit/test_agents/test_sdk.py)

```python
def test_run_debate_returns_verdict_message():
    """sdk.run_debate(topic) returns a VerdictMessage (mocked agents)."""

def test_all_logic_accessible_through_sdk():
    """All public functionality is reachable via DebateSDK — no internal bypass needed."""

def test_gui_cli_do_not_need_internal_imports():
    """Calling sdk.run_debate() requires only importing DebateSDK, nothing from internals."""
```

---

## 15. Open Questions & Future Decisions

| # | Question | Decision Needed By | Impact |
|---|----------|-------------------|--------|
| Q1 | Which web search provider? Tavily vs SerpAPI vs Brave Search | Before Phase 4 (Skills) | Affects `argument_skill.py` and `counter_skill.py` |
| Q2 | Should `ProAgent` and `ConAgent` use the same LLM model, or different models (e.g., Claude for one, GPT for the other)? | Before Phase 5 | Affects `sdk.py` configuration |
| Q3 | Should the debate topic be injected at runtime via `--topic` CLI arg, or read from `config/setup.json`? | Before Phase 7 | CLI design; `--topic` takes priority over config |
| Q4 | Should debate transcripts be saved to `results/` automatically, or only on `--save` flag? | Before Phase 7 | Storage hygiene |
| Q5 | Should the GUI (optional bonus) be a separate process or embedded in the main process? | After Phase 7 | Deployment diagram update needed |
| Q6 | Reduce rounds to 5 if API budget is constrained? | Before first full run | Documented in README, no grade penalty |

---

*Document maintained by the Exercise 02 team. Last updated: 2026-05-22. Version: 1.00.*
