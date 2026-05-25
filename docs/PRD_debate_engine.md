# PRD: Debate Engine Algorithm
## Exercise 02: AI Agent Debate System

### 1. Overview
The debate engine orchestrates a structured, multi-round argument between two independent agents (`ProAgent` and `ConAgent`), supervised by a third agent (`JudgeAgent`). It ensures proper turn-taking, forces opponents to directly address each other's points, and concludes with a definitive verdict.

### 2. The Debate Loop Algorithm

The debate loop executes sequentially for a configured `max_rounds`. One "round" consists of exactly one `ProAgent` turn and one `ConAgent` turn.

#### Step-by-Step Flow:
1. **Initialization:**
   - The user inputs the debate topic via the CLI (`DebateSDK.run_debate(topic)`).
   - The SDK passes the topic to `JudgeAgent.run()`.
   - `JudgeAgent` logs the debate start and initializes an empty transcript.

2. **Loop Iteration (Round `N`):**
   - **Pro Turn:**
     - `JudgeAgent` retrieves the ConAgent's last argument from the transcript (empty for Round 1).
     - `JudgeAgent` invokes `ProAgent.run(context)` passing `topic`, `round`, and `opponent_argument`.
     - `ProAgent` builds an argument, performs a web search for sources, and returns a JSON `DebateTurnMessage`.
     - `JudgeAgent` appends the pro turn to the transcript and logs a `JudgeRelayMessage` event representing routing from PRO to CON.
   - **Con Turn:**
     - `JudgeAgent` retrieves the `ProAgent`'s argument from the turn just completed.
     - `JudgeAgent` invokes `ConAgent.run(context)` passing `topic`, `round`, and `opponent_argument`.
     - `ConAgent` builds a counter-argument directly referencing the pro argument, performs a web search, and returns a JSON `DebateTurnMessage`.
     - `JudgeAgent` appends the con turn to the transcript and logs a `JudgeRelayMessage` event representing routing from CON to PRO.

3. **Termination & Verdict:**
   - After `max_rounds` iterations, the loop terminates.
   - `JudgeAgent` invokes `JudgeSkill` with the full transcript.
   - The LLM acts as an impartial judge and evaluates the debate based entirely on **persuasive power**.
   - `JudgeAgent` receives the verdict, validates it against the `VerdictMessage` schema, logs the end of the debate, and returns the JSON string to the SDK.

### 3. Agent Inputs and Outputs

| Agent | Input Context (`dict`) | Output (`str` / JSON) |
|---|---|---|
| **ProAgent** | `{"topic": str, "round": int, "opponent_argument": str}` | `DebateTurnMessage` |
| **ConAgent** | `{"topic": str, "round": int, "opponent_argument": str}` | `DebateTurnMessage` |
| **JudgeAgent** | `{"topic": str}` | `VerdictMessage` |

### 4. Judge Monitoring & Intervention

- **Turn Discipline:** The `JudgeAgent` enforces that the `ConAgent` receives the `ProAgent`'s argument, and vice versa. It prevents agents from arguing in a vacuum.
- **Message Validation:** If a child agent returns invalid JSON or fails to include required fields (like `sources`), the IPC validation layer raises an error, which the Gatekeeper/SDK layer can handle or retry.
- **Timeout Monitoring:** The `Watchdog` service runs in parallel to the `JudgeAgent`. If an agent process hangs during its turn, the watchdog kills and restarts the process. The debate engine expects API-level timeouts (handled by the Gatekeeper) to prevent silent stalls.

### 5. Verdict Logic
- **Criteria:** The verdict is evaluated strictly on **persuasive power**, rhetorical quality, and effective use of cited evidence.
- **Factual Truth:** The judge explicitly ignores objective factual correctness; an agent arguing a falsehood brilliantly beats an agent arguing the truth poorly.
- **No Ties Allowed:** The judge MUST select a definitive winner. If scores are equal, the tie is broken based on rhetorical delivery.

### 6. Edge Cases Handled

| Edge Case | Handled By | Behavior |
|---|---|---|
| **Agent API Timeout** | API Gatekeeper | Retries up to `max_retries`, then raises `GatekeeperError`. |
| **Process Crash** | Watchdog | Detects missing keep-alive, restarts agent. Raises `WatchdogGaveUpError` after max attempts. |
| **Malformed JSON** | `validate_message` | Pydantic raises `ValidationError`. |
| **Empty Sources** | `validate_message` | Fails schema validation (requires `min_length=1`). Agents use a fallback placeholder if the API returns no sources. |
| **Budget Exceeded** | API Gatekeeper | Halts debate immediately with `BudgetExceededError`. |
