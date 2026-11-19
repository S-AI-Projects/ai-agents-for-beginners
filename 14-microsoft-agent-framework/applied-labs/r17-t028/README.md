# Applied Lab: Bounded Agent Loop — Failure and Recovery Example (R17-T028)

## Overview & Lesson Alignment

In **Microsoft Agent Framework (MAF)** and production agentic architectures, multi-step orchestration workflows (such as sequential, concurrent, or magnetic orchestration) must enforce strict operational boundaries:
1. **Bounded Step Budget**: Autonomous loops must enforce an upper bound on iterations (e.g. `max_steps=3`) to prevent infinite reasoning cycles and runaway resource consumption.
2. **Deterministic Termination & Guarding**: Explicit stop conditions ensure that once an agent issues a `stop` action, all execution terminates immediately and no subsequent tool calls are dispatched.
3. **Traceability**: Every lifecycle transition, parameter dictionary, execution status, and diagnostic message is captured in a structured telemetry trace (analogous to OpenTelemetry spans emitted in MAF).
4. **Failure Explanation & Recovery**: When encountering missing, malformed, or nonexistent data, the framework must record an explicit diagnostic error rather than failing silently, enabling the agent loop or user to recover on subsequent valid inputs.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic, self-contained educational simulation implemented entirely in Python 3 standard library. It models the core lifecycle and safety invariants of Microsoft Agent Framework without requiring an Azure subscription, live Foundry endpoints, or physical hardware.

---

## Architecture & Contract

### State & Actions
- **Supported Actions**:
  - `inspect`: Queries the local data store for a specific document or record (`target`).
  - `answer`: Emits a synthesised response (`text`) and stores it in final state.
  - `stop`: Signals intentional workflow completion and halts all subsequent execution.
- **Loop Status Outcomes**:
  - `completed`: Successfully reached termination or completed plan within budget.
  - `budget_exceeded`: Plan exceeded `max_steps` (default 3) without stopping.
  - `ExecutionHaltedError`: Raised if an external caller attempts `execute_step` after stopping.

### Trace Schema
Each executed step appends an `ActionTraceRecord` containing:
- `step_number`: 1-based sequential step counter.
- `action`: Dispatched action token (`inspect`, `answer`, `stop`).
- `payload`: Input arguments passed to the action.
- `status`: Execution result (`success`, `error`, `stopped`).
- `result`: Returned payload (if successful).
- `error_code` / `error_message` / `explanation`: Diagnostic feedback on failure.
- `timestamp`: UTC ISO 8601 timestamp.

---

## Scenarios Walkthrough

### 1. Normal Lifecycle (`[inspect, answer, stop]`)
- **Plan**: Inspect `doc_101` -> Answer -> Stop.
- **Outcome**: Status is `completed`, 3 steps executed, final answer populated.

### 2. Endless Plan Protection (`budget_exceeded`)
- **Plan**: 5 repeated `inspect` steps with no stop action.
- **Outcome**: Execution halts at step 3 with status `budget_exceeded`, preventing runaway execution.

### 3. Stop Guarantee (No Tool Called After Stop)
- **Plan**: `[inspect, stop, answer]`.
- **Outcome**: The agent halts immediately at step 2 (`stop`). The subsequent `answer` action is never invoked or recorded.

### 4. Invalid / Missing-Data Handling
- **Trigger**: `inspect` called with non-existent key (e.g., `unknown_entity_404`) or empty payload.
- **Diagnostic**: Emits `MISSING_DATA` error code with explicit explanation and remediation advice (`Available keys: ['doc_101', 'doc_102']`).

### 5. Recovery Flow
- **Step 1**: Tries inspecting `nonexistent_key` -> fails with `MISSING_DATA`.
- **Step 2**: Re-evaluates and inspects valid target `doc_102` -> succeeds.
- **Step 3**: Issues `stop` -> cleanly terminates with status `completed`.

---

## Running the Lab

### Run Demonstration Script
```bash
python3 14-microsoft-agent-framework/applied-labs/r17-t028/example.py
```

### Run Automated Unit Test Suite
```bash
python3 -m unittest discover -s 14-microsoft-agent-framework/applied-labs/r17-t028 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (standard library only).
- Zero external package dependencies, zero cloud API keys required.
