# TODO.md — Exercise 02: AI Agent Debate
**Course:** AI Agents (Dr. Yoram Segal)
**Assignment:** Exercise 02 — Debate between two AI agents supervised by a third (judge) agent
**Version:** 1.00
**Status tracking:** ⬜ Not started | 🔄 In progress | ✅ Done

---

## Phase 1 — Project Documents (must be completed and approved BEFORE any code)

### 1.1 PRD.md — Product Requirements Document
- ⬜ Write `docs/PRD.md` with the following sections:
  - Project overview: what the debate system does and why
  - User problem: demonstrating multi-agent orchestration via structured debate
  - Target audience: Dr. Segal and course evaluators
  - Measurable goals and KPIs (e.g., minimum 10 ping-pong exchanges, judge must deliver a verdict)
  - Functional requirements:
    - Three agents: `ProAgent` (for), `ConAgent` (against), `JudgeAgent` (father/supervisor)
    - All communication routed through JudgeAgent (child → father → child, never direct)
    - Each agent uses a different `Skill` with a unique `Description` so the agent auto-selects it
    - Mandatory internet search tool use per exchange
    - Minimum 10 debate rounds (ping = argument, pong = counter-argument)
    - JudgeAgent delivers final verdict based on persuasive power, not factual correctness
    - Judge cannot remain neutral (tie is forbidden)
  - Non-functional requirements:
    - Must use Python (no CLI-only solution; Claude CLI may be used only for manual testing)
    - JSON structured communication protocol between agents
    - Structured logs (FIFO, up to 20 log files, max 500 lines each)
    - Timeouts on every API request
    - Watchdog + keep-alive to restart crashed processes
    - Gatekeeper layer for token/cost control
  - Out-of-scope: GUI (optional bonus), direct child-to-child communication
  - Assumptions and dependencies: Anthropic API key, `uv` package manager
  - Timeline and milestones (see Phase breakdown below)
  - Acceptance criteria: debate runs end-to-end, judge delivers verdict, logs are structured, all tests pass

### 1.2 PRD_debate_engine.md — Algorithm-specific PRD
- ⬜ Write `docs/PRD_debate_engine.md`:
  - Describe the debate loop algorithm step by step
  - Define input/output for each agent call
  - Define the ping-pong message passing mechanism
  - Define how the judge monitors and when it intervenes
  - Define verdict logic (persuasive power criterion, not factual truth)
  - Edge cases: agent timeout, malformed JSON response, agent refuses to counter-argue

### 1.3 PRD_communication_protocol.md — IPC / JSON Protocol PRD
- ⬜ Write `docs/PRD_communication_protocol.md`:
  - Define the exact JSON schema for every message type:
    - `debate_turn`: `{ "round": int, "speaker": "pro"|"con", "argument": str, "sources": [str] }`
    - `judge_relay`: `{ "from": str, "to": str, "payload": debate_turn }`
    - `verdict`: `{ "winner": "pro"|"con", "reasoning": str, "score": { "pro": int, "con": int } }`
  - Define message validation rules
  - Define error message schema

### 1.4 PRD_gatekeeper.md — API Gatekeeper PRD
- ⬜ Write `docs/PRD_gatekeeper.md`:
  - Rate limit configuration structure
  - Queue management (FIFO, max depth)
  - Retry logic (max retries, backoff)
  - Monitoring and logging per API call
  - Budget cap enforcement

### 1.5 PLAN.md — Architecture Document
- ⬜ Write `docs/PLAN.md` with:
  - C4 Model diagrams (Context → Container → Component → Code level)
  - UML sequence diagram of one full debate round (Pro → Judge → Con → Judge → Pro)
  - UML class diagram for all classes
  - Deployment diagram (local process tree)
  - Architecture Decision Records (ADRs):
    - ADR-01: Why JSON over plain text for IPC
    - ADR-02: Why multiprocessing (not multithreading) for agent isolation
    - ADR-03: Why Gatekeeper pattern for API calls
  - API/SDK interface documentation
  - Data flow summary

### 1.6 TODO.md (this file)
- ✅ Create `docs/TODO.md` with full task breakdown, priorities, status, and definition-of-done per task

### 1.7 Approval checkpoint
- ⬜ Review all docs with a peer or self-review checklist before proceeding to code

---

## Phase 2 — Project Skeleton & Configuration

### 2.1 Repository setup
- ⬜ Initialize git repository: `git init`
- ⬜ Create `.gitignore` — must include: `.env`, `*.key`, `*.pem`, `__pycache__/`, `.venv/`, `uv.lock` (committed separately), `results/`, `*.log`
- ⬜ Create initial commit with docs only

### 2.2 Package structure
Create the following directory tree:
```
debate-agents/
├── src/
│   └── debate/
│       ├── __init__.py          # exports __version__, __all__
│       ├── sdk/
│       │   └── sdk.py           # DebateSDK — single entry point for all logic
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base_agent.py    # Abstract BaseAgent class
│       │   ├── pro_agent.py     # ProAgent (for-side debater)
│       │   ├── con_agent.py     # ConAgent (against-side debater)
│       │   └── judge_agent.py   # JudgeAgent (father/supervisor)
│       ├── skills/
│       │   ├── __init__.py
│       │   ├── base_skill.py    # Abstract Skill interface
│       │   ├── argument_skill/
│       │   │   ├── SKILL.md     # Description used by agent auto-selection
│       │   │   └── argument_skill.py
│       │   ├── counter_skill/
│       │   │   ├── SKILL.md
│       │   │   └── counter_skill.py
│       │   └── judge_skill/
│       │       ├── SKILL.md
│       │       └── judge_skill.py
│       ├── commands/
│       │   ├── __init__.py
│       │   └── debate_command.md  # Saved prompt for /debate command
│       ├── shared/
│       │   ├── __init__.py
│       │   ├── gatekeeper.py    # API Gatekeeper (rate limits, queue, retry)
│       │   ├── config.py        # Config loader (reads JSON config files)
│       │   ├── logger.py        # Structured logger (FIFO, JSON Lines)
│       │   ├── watchdog.py      # Watchdog + keep-alive for agent processes
│       │   ├── ipc.py           # JSON message schema + validation
│       │   └── version.py       # __version__ = "1.00"
│       └── constants.py         # All immutable project constants (Enum)
├── tests/
│   ├── unit/
│   │   ├── test_agents/
│   │   ├── test_skills/
│   │   ├── test_shared/
│   │   └── conftest.py
│   └── integration/
│       └── test_debate_flow.py
├── docs/
│   ├── PRD.md
│   ├── PRD_debate_engine.md
│   ├── PRD_communication_protocol.md
│   ├── PRD_gatekeeper.md
│   ├── PLAN.md
│   └── TODO.md
├── config/
│   ├── setup.json               # Main app config (versioned)
│   ├── rate_limits.json         # API rate limits (versioned)
│   └── logging_config.json      # Log rotation settings
├── data/                        # Input topics for debates
├── results/                     # Saved debate transcripts and verdicts
├── assets/                      # Screenshots, diagrams
├── prompts/                     # Prompt Engineering Log
│   └── prompt_log.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .env-example
└── .gitignore
```
- ⬜ Create all directories and placeholder `__init__.py` files
- ⬜ Create `src/debate/shared/version.py` with `__version__ = "1.00"`

### 2.3 pyproject.toml
- ⬜ Create `pyproject.toml` with:
  - `[project]` section: name, version `"1.00"`, description, author, license
  - `[project.dependencies]`: `anthropic`, `python-dotenv`, `pydantic` (for message validation)
  - `[tool.ruff]`: `line-length = 100`, `target-version = "py310"`, select `["E","F","W","I","N","UP","B","C4","SIM"]`, ignore `["E501"]`
  - `[tool.coverage.run]`: `source = ["src"]`, omit test dirs and gui
  - `[tool.coverage.report]`: `fail_under = 85`
  - `[tool.pytest.ini_options]`: testpaths, verbosity

### 2.4 Configuration files
- ⬜ Create `config/setup.json`:
  ```json
  { "version": "1.00", "model": "claude-sonnet-4-20250514", "max_tokens": 1000, "debate_topic": "", "max_rounds": 10 }
  ```
- ⬜ Create `config/rate_limits.json`:
  ```json
  { "version": "1.00", "services": { "default": { "requests_per_minute": 30, "requests_per_hour": 500, "concurrent_max": 5, "retry_after_seconds": 30, "max_retries": 3 } } }
  ```
- ⬜ Create `config/logging_config.json`: max 20 log files, max 500 lines each, FIFO rotation
- ⬜ Create `.env-example`:
  ```
  ANTHROPIC_API_KEY=your_key_here
  DEBATE_TOPIC=Is artificial intelligence good for humanity?
  ```
- ⬜ Confirm `.env` is in `.gitignore` and never committed

### 2.5 Install dependencies with uv (never pip directly)
- ⬜ Run `uv sync` to create virtual environment from `pyproject.toml`
- ⬜ Run `uv add anthropic python-dotenv pydantic` for runtime deps
- ⬜ Run `uv add --dev pytest pytest-cov ruff` for dev deps
- ⬜ Verify `uv.lock` is generated and committed

---

## Phase 3 — Core Shared Infrastructure (TDD: write tests first)

### 3.1 `constants.py`
- ⬜ Write tests first: `tests/unit/test_shared/test_constants.py`
  - Test that all Enums are importable and have correct values
- ⬜ Implement `src/debate/constants.py`:
  - `AgentRole(Enum)`: PRO, CON, JUDGE
  - `MessageType(Enum)`: DEBATE_TURN, JUDGE_RELAY, VERDICT
  - `DebateStatus(Enum)`: RUNNING, FINISHED, ERROR
  - `MAX_ROUNDS = 10` (from config, not hardcoded — load via config.py)
  - All values sourced from config files, not hardcoded in logic

### 3.2 `shared/ipc.py` — JSON message schemas and validation
- ⬜ Write tests first: `tests/unit/test_shared/test_ipc.py`
  - Test valid DebateTurn creation
  - Test JudgeRelay wrapping
  - Test Verdict schema
  - Test validation rejects malformed messages
- ⬜ Implement using `pydantic` BaseModel:
  - `DebateTurnMessage`: round, speaker (AgentRole), argument (str), sources (list[str])
  - `JudgeRelayMessage`: from_agent, to_agent, payload (DebateTurnMessage)
  - `VerdictMessage`: winner (AgentRole), reasoning (str), score (dict)
  - `validate_message(raw: str) -> BaseModel` — parses and validates JSON

### 3.3 `shared/config.py` — Configuration loader
- ⬜ Write tests first: `tests/unit/test_shared/test_config.py`
  - Test loads `setup.json` correctly
  - Test loads `rate_limits.json` correctly
  - Test raises on missing required keys
  - Test version is read and accessible
- ⬜ Implement `ConfigManager`:
  - Loads all JSON config files from `config/` directory
  - Validates version fields exist
  - Provides typed getters: `get_model()`, `get_max_rounds()`, `get_rate_limits()`, etc.
  - Never reads hardcoded values — everything from config files
  - Validates config version matches `version.py` at startup

### 3.4 `shared/logger.py` — Structured logger
- ⬜ Write tests first: `tests/unit/test_shared/test_logger.py`
  - Test log entry is valid JSON Lines format
  - Test FIFO rotation triggers when file hits 500 lines
  - Test max 20 log files enforced (oldest deleted)
  - Test log levels: DEBUG, INFO, WARNING, ERROR
- ⬜ Implement `StructuredLogger`:
  - Each log entry is one JSON object per line (JSONL format)
  - Schema: `{ "timestamp": str, "level": str, "agent": str, "event": str, "data": dict }`
  - FIFO rotation: when current log file hits 500 lines, open new file
  - When 20 files exist, delete oldest before creating new
  - Log file naming: `results/logs/debate_YYYYMMDD_HHMMSS_NNN.jsonl`
  - Thread-safe logging

### 3.5 `shared/gatekeeper.py` — API Gatekeeper
- ⬜ Write tests first: `tests/unit/test_shared/test_gatekeeper.py`
  - Test rate limit is enforced (mock time)
  - Test queue fills up and blocks when limit reached
  - Test retry logic fires on transient failure (mock API error)
  - Test all API calls are logged
  - Test backpressure signal when queue is full
  - Test budget cap blocks further calls when exceeded
- ⬜ Implement `ApiGatekeeper`:
  - Reads limits from `config/rate_limits.json` via `ConfigManager`
  - `execute(api_call, *args, **kwargs)` — single entry point for all API calls
  - Checks rate limit before executing; if exceeded, routes to FIFO queue
  - Queue: thread-safe `queue.Queue`, max depth from config
  - Retry: up to `max_retries` times with `retry_after_seconds` backoff
  - Logs every call: timestamp, model, tokens in/out, cost estimate, success/failure
  - `get_queue_status() -> QueueStatus`
  - Budget cap: sum of estimated token costs; raises `BudgetExceededError` if cap hit
  - No direct API calls anywhere in the codebase except through `execute()`

### 3.6 `shared/watchdog.py` — Watchdog
- ⬜ Write tests first: `tests/unit/test_shared/test_watchdog.py`
  - Test watchdog detects a "dead" process and restarts it
  - Test keep-alive ping mechanism
  - Test watchdog respects max restart attempts
- ⬜ Implement `Watchdog`:
  - Monitors agent sub-processes
  - Sends keep-alive pings at configurable intervals
  - If a process doesn't respond within timeout: kill and restart
  - Max restart attempts before raising `WatchdogGaveUpError`
  - Logs all restart events

---

## Phase 4 — Skills Layer (TDD: tests first)

### 4.1 `skills/base_skill.py` — Abstract Skill
- ⬜ Write tests: `tests/unit/test_skills/test_base_skill.py`
  - Test that concrete skills must implement `execute()`
  - Test that `Description` is set and non-empty
- ⬜ Implement abstract `BaseSkill`:
  - `description: str` — used by agent to auto-select this skill
  - `execute(context: dict) -> str` — abstract method
  - `validate_input(context: dict)` — abstract method

### 4.2 `skills/argument_skill/` — ProAgent's primary skill
- ⬜ Write SKILL.md with description: "Constructs a well-sourced argument FOR the debate topic, citing internet sources."
- ⬜ Write tests: `tests/unit/test_skills/test_argument_skill.py`
  - Test execute() returns a non-empty string
  - Test sources list is populated
  - Test raises on missing topic in context
- ⬜ Implement `ArgumentSkill(BaseSkill)`:
  - Builds a prompt for the LLM to argue FOR the topic
  - Calls web search tool to find supporting sources
  - Returns structured argument with citations
  - Max 150 lines per file — split if needed

### 4.3 `skills/counter_skill/` — ConAgent's primary skill
- ⬜ Write SKILL.md with description: "Constructs a counter-argument AGAINST the debate topic, referencing the opponent's last argument."
- ⬜ Write tests: `tests/unit/test_skills/test_counter_skill.py`
  - Test execute() returns counter-argument referencing opponent's points
  - Test raises on missing opponent_argument in context
- ⬜ Implement `CounterSkill(BaseSkill)`:
  - Builds a prompt to argue AGAINST the topic
  - Must reference the opponent's previous argument (not ignore it)
  - Calls web search tool for counter-sources
  - Returns structured counter-argument

### 4.4 `skills/judge_skill/` — JudgeAgent's skill
- ⬜ Write SKILL.md with description: "Evaluates debate arguments for persuasive power and delivers a final verdict. Does not score on factual accuracy."
- ⬜ Write tests: `tests/unit/test_skills/test_judge_skill.py`
  - Test verdict is always pro or con (never tie)
  - Test reasoning is non-empty
  - Test score dict has both "pro" and "con" keys
- ⬜ Implement `JudgeSkill(BaseSkill)`:
  - Analyzes full debate transcript
  - Scores each round by persuasive power
  - Produces `VerdictMessage` — winner must be PRO or CON, never tie
  - If scores are equal, decides by rhetorical quality

---

## Phase 5 — Agents Layer (TDD: tests first)

### 5.1 `agents/base_agent.py` — Abstract BaseAgent
- ⬜ Write tests: `tests/unit/test_agents/test_base_agent.py`
  - Test agent initializes with a role
  - Test `select_skill()` uses Description matching
  - Test `run()` is callable
- ⬜ Implement `BaseAgent`:
  - `role: AgentRole`
  - `skills: list[BaseSkill]` — list of available skills
  - `select_skill(task_description: str) -> BaseSkill` — picks skill whose Description best matches task
  - `run(context: dict) -> str` — abstract: selects skill, executes, returns result
  - `_call_api(prompt: str) -> str` — routes through `ApiGatekeeper.execute()`; never calls Anthropic SDK directly
  - All timeouts on every API call (from config)
  - Logs every action via `StructuredLogger`

### 5.2 `agents/pro_agent.py` — ProAgent
- ⬜ Write tests: `tests/unit/test_agents/test_pro_agent.py`
  - Test always argues FOR the topic
  - Test uses `ArgumentSkill`
  - Test never agrees with the con agent automatically (no sycophancy)
  - Test references opponent's argument (per assignment: must address it)
- ⬜ Implement `ProAgent(BaseAgent)`:
  - Role: `AgentRole.PRO`
  - Skills: `[ArgumentSkill()]`
  - `run(context)`: receives judge relay, extracts con's last argument, builds pro argument addressing it, returns JSON turn
  - Includes mandatory web search call per turn
  - "Wants to win" — does not capitulate to opponent

### 5.3 `agents/con_agent.py` — ConAgent
- ⬜ Write tests: `tests/unit/test_agents/test_con_agent.py`
  - Test always argues AGAINST the topic
  - Test uses `CounterSkill`
  - Test never agrees with pro agent automatically
- ⬜ Implement `ConAgent(BaseAgent)`:
  - Role: `AgentRole.CON`
  - Skills: `[CounterSkill()]`
  - Same structure as ProAgent but argues against
  - Must address pro's last argument, not ignore it

### 5.4 `agents/judge_agent.py` — JudgeAgent (father/supervisor)
- ⬜ Write tests: `tests/unit/test_agents/test_judge_agent.py`
  - Test all messages route through judge (no direct child-to-child)
  - Test judge relays pro turn to con and vice versa
  - Test judge delivers verdict after `max_rounds` rounds
  - Test judge intervenes if one agent dominates the entire exchange
  - Test verdict is never a tie
- ⬜ Implement `JudgeAgent(BaseAgent)`:
  - Role: `AgentRole.JUDGE`
  - Skills: `[JudgeSkill()]`
  - Orchestrates the debate loop:
    1. Send topic to ProAgent
    2. Receive pro's `DebateTurnMessage`
    3. Relay to ConAgent
    4. Receive con's `DebateTurnMessage`
    5. Log both turns
    6. Repeat until `max_rounds`
    7. Call `JudgeSkill` with full transcript → `VerdictMessage`
  - Enforces: agents respond to each other, not ignore (checks that opponent arg is referenced)
  - Monitors for timeouts — triggers Watchdog if agent hangs
  - Communication is always: child → JudgeAgent → child (no shortcuts)

---

## Phase 6 — SDK Layer

### 6.1 `sdk/sdk.py` — DebateSDK (single entry point)
- ⬜ Write tests: `tests/unit/test_agents/test_sdk.py`
  - Test `run_debate(topic)` returns a `VerdictMessage`
  - Test all logic is accessible through SDK (no bypass)
  - Test GUI/CLI can call SDK without importing internal modules
- ⬜ Implement `DebateSDK`:
  - `__init__(config_path: str)` — loads config, initializes all agents, gatekeeper, logger, watchdog
  - `run_debate(topic: str, rounds: int = None) -> VerdictMessage`
  - `get_transcript() -> list[DebateTurnMessage]`
  - `get_cost_report() -> dict` — token usage and cost breakdown
  - `get_log_path() -> str`
  - This is the ONLY public interface — GUI, CLI, tests all use this

---

## Phase 7 — Main Entry Point & CLI

### 7.1 `src/main.py` — CLI entry point
- ⬜ Implement `main.py`:
  - Parses CLI args: `--topic`, `--rounds`, `--config`
  - Instantiates `DebateSDK`
  - Calls `sdk.run_debate(topic)`
  - Prints verdict to terminal
  - Prints cost report
  - Exits with code 0 on success, 1 on error
  - All run via `uv run python src/main.py --topic "..."`

### 7.2 Commands directory
- ⬜ Create `src/debate/commands/debate_command.md` — saved prompt that triggers the debate via `/debate` command in Claude CLI (manual testing only, not the submission)

---

## Phase 8 — Integration Tests

### 8.1 Full debate flow test
- ⬜ Write `tests/integration/test_debate_flow.py`:
  - Test full debate runs end-to-end with mocked Anthropic API
  - Test minimum 10 rounds are completed
  - Test judge delivers verdict (not tie)
  - Test all messages are valid JSON
  - Test logs are written and FIFO rotation works
  - Test cost report is generated
  - Test gatekeeper is invoked for every API call (assert no direct SDK calls bypass it)

### 8.2 Watchdog integration test
- ⬜ Write `tests/integration/test_watchdog_flow.py`:
  - Simulate agent timeout → assert watchdog restarts process
  - Assert debate resumes after restart

---

## Phase 9 — Code Quality Gates (must all pass before submission)

### 9.1 Ruff linter
- ⬜ Run `uv run ruff check src/ tests/`
- ⬜ Fix ALL errors — zero tolerance for linter failures
- ⬜ Re-run until clean: `ruff check` returns exit code 0

### 9.2 Test coverage
- ⬜ Run `uv run pytest tests/ --cov=src --cov-report=term-missing`
- ⬜ Confirm coverage ≥ 85% (enforced by `fail_under = 85` in pyproject.toml)
- ⬜ Cover statement, branch, and path coverage for all critical paths

### 9.3 No hardcoded values check
- ⬜ Grep source for hardcoded API URLs, keys, rate limits, timeouts — must be zero
- ⬜ All values must come from `config/*.json` or `constants.py`

### 9.4 No secrets check
- ⬜ Confirm `.env` is not committed
- ⬜ Confirm no API keys appear anywhere in `src/` or `tests/`
- ⬜ Confirm `.env-example` exists with placeholder values only

### 9.5 File size check
- ⬜ Confirm every source file is ≤ 150 lines of code (comments and blank lines excluded)
- ⬜ Split any file that exceeds the limit

### 9.6 No code duplication check
- ⬜ Review for copy-paste code across files — extract to shared module
- ⬜ DRY principle: same logic in 2+ files → extract to base class or mixin

---

## Phase 10 — README & Documentation Finalization

### 10.1 README.md
- ⬜ Write complete `README.md` (English or Hebrew, not Arabic):
  - System requirements: Python 3.10+, `uv`, Anthropic API key
  - Installation instructions (step-by-step using `uv sync`)
  - Environment setup (copy `.env-example` to `.env`, fill API key)
  - How to run: `uv run python src/main.py --topic "Is AI good for humanity?"`
  - Expected output (sample terminal output with verdict)
  - How to run tests: `uv run pytest tests/ --cov=src`
  - How to check linter: `uv run ruff check src/`
  - Configuration guide: what each config key does
  - Project structure overview
  - Screenshots of terminal output (attach to `assets/`)
  - Sample debate transcript snippet
  - Cost report example
  - Contribution guidelines
  - License

### 10.2 Prompt Engineering Log
- ⬜ Write `prompts/prompt_log.md`:
  - List all significant prompts used during development
  - For each prompt: goal, context, the prompt text, result received, lessons learned
  - Iterative improvements made to prompts

### 10.3 Architecture diagrams
- ⬜ Add diagrams to `docs/PLAN.md`:
  - Class diagram (all agents, skills, shared classes)
  - Sequence diagram (one full debate round)
  - Component diagram (SDK → Agents → Gatekeeper → Anthropic API)
- ⬜ Export diagrams as images to `assets/`

### 10.4 Cost analysis
- ⬜ Run one full debate and record token usage
- ⬜ Add cost table to README.md:
  | Model | Input Tokens | Output Tokens | Total Cost |
  |-------|-------------|---------------|------------|
  | claude-sonnet-4 | ... | ... | $... |
- ⬜ Document optimization strategies used (e.g., prompt compression, caching)

### 10.5 Screenshots
- ⬜ Take screenshots of:
  - Debate running in terminal
  - Final verdict display
  - Test coverage report
  - Ruff passing clean
- ⬜ Save to `assets/` and reference in README.md

---

## Phase 11 — Final Checklist Before Submission

### 11.1 Documentation checklist
- ⬜ `README.md` is complete with screenshots, examples, install guide
- ⬜ `docs/PRD.md` — complete
- ⬜ `docs/PRD_debate_engine.md` — complete
- ⬜ `docs/PRD_communication_protocol.md` — complete
- ⬜ `docs/PRD_gatekeeper.md` — complete
- ⬜ `docs/PLAN.md` with architecture diagrams — complete
- ⬜ `docs/TODO.md` (this file) — updated with all statuses
- ⬜ `prompts/prompt_log.md` — complete

### 11.2 Architecture checklist
- ⬜ All business logic accessible through `DebateSDK` only
- ⬜ No logic in `GUI` or `CLI` layers (they only call SDK)
- ⬜ `ApiGatekeeper` wraps every external API call — no bypass
- ⬜ OOP design: no code duplication, inheritance and mixins used where appropriate
- ⬜ Rate limits from config file only, never hardcoded

### 11.3 Code quality checklist
- ⬜ `ruff check` → 0 errors
- ⬜ `pytest --cov` → ≥ 85% coverage
- ⬜ All files ≤ 150 lines of code
- ⬜ Every public function/class has a `docstring`
- ⬜ All variable and function names are descriptive and in English

### 11.4 Security checklist
- ⬜ `.env` is in `.gitignore` and not committed
- ⬜ No API keys in source code
- ⬜ `.env-example` exists with placeholder values
- ⬜ `gitignore` is up-to-date

### 11.5 Dependency checklist
- ⬜ `pyproject.toml` exists with all dependencies and versions pinned
- ⬜ `uv.lock` exists and is committed
- ⬜ No direct `pip install` used anywhere (only `uv add` / `uv sync`)
- ⬜ `uv run` used for all script and test execution
- ⬜ Reviewer can run `uv sync` and get a full working environment

### 11.6 Submission checklist (per assignment requirements)
- ⬜ Submit as a pair (both partners submit individually on Moodle)
- ⬜ Each partner submits a PDF link to the shared repository
- ⬜ Repository is public (or shared with lecturer)
- ⬜ Do NOT share submission link publicly or with lecturer via chat — Moodle only
- ⬜ Submission via GitHub (public repository recommended)
- ⬜ Once submitted, no re-submission is possible — verify everything before submitting
- ⬜ If using reduced budget: reduce `max_rounds` from 10 to 5 and document in README (no grade penalty)

---

## Definition of Done (per task)

A task is **Done** only when ALL of the following are true:
1. Code is written and committed
2. Tests written BEFORE or alongside the code (TDD)
3. Coverage ≥ 85% for this module
4. `ruff check` passes with 0 errors
5. Docstrings present on all public classes and functions
6. No hardcoded values
7. File is ≤ 150 lines of code
8. Relevant documentation updated (README, PRD, PLAN as applicable)

---

## Notes

- **Agent communication rule:** Every message goes child → JudgeAgent → child. Direct Pro ↔ Con is forbidden.
- **Skill auto-selection:** Agents pick skills based on `Description` in `SKILL.md`, not explicit calls.
- **Verdict rule:** Judge MUST pick a winner. Tie = bug.
- **Web search:** Every debate turn MUST include an internet search (mandatory tool use).
- **Budget note:** If API budget is limited, reduce rounds to 5 and note in README — will not affect grade.
- **No CLI submission:** The final submission must be driven by Python code, not by running Claude CLI manually. Claude CLI may be used for development/testing only.
- **uv only:** Never use `pip install` or `python -m venv` — use `uv` exclusively.
