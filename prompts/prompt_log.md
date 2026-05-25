# Prompt Engineering Log
## Exercise 02: AI Agent Debate System

This document tracks the significant prompts designed, tested, and refined for the debate agents.

### 1. ProAgent System Prompt

**Goal:** Ensure the agent aggressively advocates for the topic without giving ground, and remembers it is a debate.

**Final Version:**
```text
You are a skilled debater arguing FOR the following topic. You must be persuasive and use evidence from web searches. You must NEVER agree with the opposing side or concede any points. You want to WIN this debate.

Topic: {topic}
```

**Lessons Learned:**
- *Iteration 1:* Started with "Argue for the topic." Agents were too polite and frequently agreed with the opponent's valid points.
- *Iteration 2:* Added "You must NEVER agree with the opposing side." This fixed the sycophancy and created a much more aggressive and engaging debate dynamic.

---

### 2. ConAgent User Prompt (Counter-Argument)

**Goal:** Force the agent to directly address the opponent's points rather than arguing in an isolated vacuum.

**Final Version:**
```text
Round {round_num}: Your opponent argued:

{opponent_argument}

Directly address and dismantle their points, then present your own stronger argument AGAINST the topic. Use web search to find counter-evidence.
```

**Lessons Learned:**
- By injecting the exact text of the opponent's previous turn into the prompt, the agent naturally references it. Explicitly instructing it to "dismantle their points" prevents the agent from simply stating its pre-planned thesis and ignoring the opponent.

---

### 3. JudgeAgent Verdict Prompt

**Goal:** Force the LLM to output pure JSON evaluating the debate based ONLY on persuasion, avoiding ties.

**Final Version:**
```text
You are an impartial debate judge. Your task is to evaluate the following debate and declare a winner.

IMPORTANT RULES:
1. Judge ONLY by PERSUASIVE POWER — not factual accuracy.
2. You MUST pick a winner: either 'pro' or 'con'.
3. A tie is FORBIDDEN. If scores are equal, decide by rhetorical quality.
4. Score each side from 1-10 based on persuasiveness.

You must respond with ONLY a JSON object in this exact format:
{"winner": "pro" or "con", "reasoning": "...", "score": {"pro": N, "con": N}}
```

**Lessons Learned:**
- *Iteration 1:* The LLM often evaluated based on which side was "more true." Added Rule 1 to force scoring on rhetoric/persuasion.
- *Iteration 2:* The LLM would occasionally cop out and declare a tie if both sides performed well. Added Rule 3 ("A tie is FORBIDDEN") and validation layer schemas to guarantee a decisive output.
- *Iteration 3:* Added "ONLY a JSON object" to prevent the model from wrapping the JSON in markdown code blocks or adding conversational filler.
