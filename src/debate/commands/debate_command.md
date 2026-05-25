# /debate — Run a Debate Between AI Agents

Use this command to trigger a multi-round debate between two AI agents
supervised by a judge agent.

## Usage

```
/debate "Is artificial intelligence good for humanity?"
```

## What it does

1. **ProAgent** receives the topic and argues **for** it, citing web sources.
2. **ConAgent** receives ProAgent's argument via **JudgeAgent** and argues **against** it.
3. The process repeats for the configured number of rounds (default: 10).
4. **JudgeAgent** evaluates all arguments by **persuasive power** (not factual accuracy).
5. JudgeAgent delivers a final **verdict** with scores and reasoning.

## Under the Hood

- All communication is routed: `Child → JudgeAgent → Child`. No direct Pro ↔ Con.
- Each turn includes a mandatory **web search** for evidence.
- All API calls go through the **ApiGatekeeper** (rate limits, retry, budget).
- Structured **JSONL logs** are written to `results/logs/`.
- A **cost report** is printed at the end.

## Example Output

```
============================================================
DEBATE VERDICT
============================================================
Topic:  Is artificial intelligence good for humanity?
Winner: PRO
Score:  Pro 8 — Con 6

Reasoning:
The Pro side demonstrated more compelling arguments with stronger
evidence from recent studies...
============================================================
```
