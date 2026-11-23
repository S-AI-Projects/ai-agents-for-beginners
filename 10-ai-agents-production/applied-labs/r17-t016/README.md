# Applied Lab: Trace Aggregation — Refactor the Teaching Example (R17-T016)

## Overview & Lesson Alignment

In **Lesson 10: AI Agents in Production: Observability & Evaluation**, monitoring real-world agent deployments requires structured telemetry and trace aggregation:
1. **Trace Roll-ups**: Distributed agent events (start, tool executions, completions, failures) must be aggregated by correlation ID (`request_id`).
2. **Privacy Guarantees**: Aggregated metrics must never include sensitive user prompt or message payloads.
3. **Incomplete Trace Handling**: Telemetry pipelines occasionally experience dropped network packets or abrupt process kills. Missing end events must be marked as `incomplete` rather than falsely reported with `duration = 0`.
4. **Refactoring Equivalence**: Demonstrates extracting span timing and completeness logic into a dedicated component (`SpanMetricsResolver`), rigorously maintaining 100% before-and-after functional equivalence.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic educational fixture using standard Python 3. It simulates OpenTelemetry / Azure Monitor trace collection semantics locally without requiring an Application Insights workspace or cloud connection.

---

## Contract & Expected Behavior

| Request ID | Event Sequence | Tool Calls | Duration | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `req_A` | `start(100)` -> `tool(104)` -> `tool(108)` -> `end(112)` | 2 | 12 ms | `success` | Canonical successful trace |
| `req_B` | `start(140)` -> `tool(145)` -> `failed(150)` | 1 | 10 ms | `failed` | Failure captured with true duration |
| `req_C` | `start(200)` -> `tool(205)` (no end/fail) | 1 | `None` | `incomplete` | Missing end marked incomplete, not 0 |

---

## Architectural Refactoring
- **Baseline**: Monolithic function `baseline_aggregate_traces` mixing event group routing, duration calculation, and tool counting.
- **Refactored**: Single-responsibility `SpanMetricsResolver` handling span lifecycle and completeness, invoked by `RefactoredTraceAggregator`.

---

## Running the Lab

### Run Demonstration
```bash
python3 10-ai-agents-production/applied-labs/r17-t016/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 10-ai-agents-production/applied-labs/r17-t016 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (standard library only).
- Zero external package dependencies.
