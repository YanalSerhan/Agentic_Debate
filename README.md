# AI Agent Debate System
**Exercise 02 — Multi-Agent Debate Simulation**

## Overview
This system orchestrates a multi-round debate between three independent AI agents (`ProAgent`, `ConAgent`, and `JudgeAgent`). Given a topic, the agents will argue back and forth, using web search to find evidence. A supervisor `JudgeAgent` enforces turn-taking, prevents direct communication between the debaters, and delivers a final binding verdict based strictly on persuasive power.

## Features
- **Multi-Process Architecture:** Each agent runs in its own OS process, using JSON-based IPC over `multiprocessing.Queue`.
- **Skill-Based Auto-Selection:** Agents dynamically select skills (like `ArgumentSkill` or `CounterSkill`) based on metadata matching, rather than hardcoded dispatch.
- **Production-Grade Resilience:**
  - **ApiGatekeeper:** Centralizes API calls with rate-limiting, retries, and budget caps.
  - **Watchdog:** Monitors agent processes via keep-alive pings and restarts crashed agents.
  - **Structured Logging:** Emits JSONL logs with automatic file rotation.

## System Requirements
- **Python 3.10+** (Required for `match` and modern typing features).
- **uv** (Required for package and virtual environment management).
- An active **Anthropic API Key** (for `claude-sonnet-4-20250514` with web_search tools).

## Setup & Installation

1. Clone the repository and navigate into it:
   ```bash
   cd Agentic_Debate
   ```

2. Initialize the environment using `uv`:
   ```bash
   uv sync
   ```

3. Configure your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

## Running the Debate

Run the main CLI script using `uv run`. Provide a debate topic in quotes:

```bash
uv run python src/main.py --topic "Is artificial intelligence a net positive for humanity?"
```

Optional arguments:
- `--rounds N`: Override the default number of debate rounds (e.g., `--rounds 5`).
- `--config PATH`: Path to a custom configuration directory (default: `config`).

### Expected Output
The system will run silently while the agents debate. At the end, it will print a final verdict and a cost report:

```text
============================================================
DEBATE VERDICT
============================================================
Topic:  Is artificial intelligence a net positive for humanity?
Winner: PRO
Score:  Pro 9 — Con 7

Reasoning:
The Pro side presented a highly persuasive and well-sourced
argument regarding the advancements in medical research...
============================================================

COST REPORT:
Total Input Tokens: 25,430
Total Output Tokens: 4,120
Total Cost (USD): $0.138
Remaining Budget: $4.862
```

## Running Tests and Quality Gates

The project maintains a strict >85% test coverage requirement and zero linter errors.

To run tests with coverage:
```bash
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

To run the linter:
```bash
uv run ruff check src/ tests/
```

## Project Structure
```text
Agentic_Debate/
├── config/              # Runtime configuration (rate limits, setup, logging)
├── docs/                # Architecture plans, PRDs, and task lists
├── prompts/             # Prompt engineering logs
├── results/logs/        # Generated JSONL structured logs
├── src/
│   ├── debate/
│   │   ├── agents/      # Pro, Con, and Judge Agent implementations
│   │   ├── sdk/         # The main entrypoint library
│   │   ├── shared/      # Infra: Gatekeeper, IPC, Logger, Watchdog, Config
│   │   └── skills/      # Tool-calling skills auto-selected by agents
│   └── main.py          # CLI entry point
└── tests/               # Unit and integration tests
```

*Developed as part of the AI Agents course (Dr. Yoram Segal).*