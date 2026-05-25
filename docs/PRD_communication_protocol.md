# PRD: Communication Protocol (IPC)
## Exercise 02: AI Agent Debate System

### 1. Overview
The communication protocol dictates how independent agent processes exchange information. All inter-agent data is passed via structured JSON over `multiprocessing.Queue`. `Pydantic` v2 is used to validate all incoming and outgoing messages.

### 2. Message Schemas

#### 2.1 `DebateTurnMessage`
Produced by `ProAgent` and `ConAgent` to represent a single argument in a given round.

**JSON Schema Definition:**
```json
{
  "round": "integer (>= 1)",
  "speaker": "string (enum: 'pro', 'con')",
  "argument": "string (min_length=1)",
  "sources": ["string (array of URLs, min_length=1)"]
}
```

**Validation Rules:**
- `speaker` must not be `"judge"`.
- `argument` cannot be empty.
- `sources` must contain at least one string.

#### 2.2 `JudgeRelayMessage`
Created internally by `JudgeAgent` to wrap a `DebateTurnMessage` for logical routing. Represents the rule that agents cannot communicate directly.

**JSON Schema Definition:**
```json
{
  "from_agent": "string (enum: 'pro', 'con', 'judge')",
  "to_agent": "string (enum: 'pro', 'con', 'judge')",
  "payload": { "... DebateTurnMessage schema ..." }
}
```

#### 2.3 `VerdictMessage`
Produced by `JudgeAgent` at the conclusion of the debate.

**JSON Schema Definition:**
```json
{
  "winner": "string (enum: 'pro', 'con')",
  "reasoning": "string (min_length=1)",
  "score": {
    "pro": "integer",
    "con": "integer"
  }
}
```

**Validation Rules:**
- `winner` MUST be `"pro"` or `"con"`. It CANNOT be `"judge"`, `"tie"`, or `null`.
- `score` dictionary MUST contain exactly both keys: `"pro"` and `"con"`.
- `reasoning` cannot be empty.

### 3. IPC Mechanism

1. **Format:** All inter-agent data is serialized to JSON string format before transmission.
2. **Transport:** Because agents run as separate OS processes, Python's `multiprocessing` abstractions (specifically `Queue` internally handled by the SDK process structure) are used to move strings between memory spaces.
3. **Parsing & Validation:**
   - The receiving entity calls `validate_message(raw_json_string)`.
   - The validation function automatically detects the message type by its keys (e.g., presence of `winner` implies `VerdictMessage`).
   - If parsing or validation fails, a `ValueError` (or `ValidationError`) is raised.

### 4. Error Handling
- If an agent generates an output that fails Pydantic validation (e.g., forgets to include sources), the validation function rejects it.
- In the current design, such failures are bubbled up and logged as errors, halting the specific agent action or relying on the Gatekeeper's retry loops if occurring inside the API boundary.
