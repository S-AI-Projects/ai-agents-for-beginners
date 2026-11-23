# Applied Lab: Trace Aggregation — Failure and Recovery Example (R17-T018)

## Overview & Lesson Alignment

In **Lesson 10: AI Agents in Production: Observability & Evaluation**, production telemetry collectors receive high volumes of asynchronous events across distributed nodes. In practice, event pipelines can suffer from dropped packets, out-of-order deliveries, or malformed payloads.

A robust observability processor must:
1. **Aggregate Distributed Spans**: Compute end-to-end duration and tool invocation count per request.
2. **Handle Incomplete Spans**: When a request start event lacks a matching completion or failure event, mark it as `incomplete` rather than reporting an erroneous duration of 0.
3. **Isolate Corrupted Records**: Flag malformed records (e.g. missing IDs, negative timestamps) without dropping subsequent events or throwing unhandled pipeline exceptions.
4. **Demonstrate Graceful Recovery**: Continue processing subsequent valid requests with zero state contamination.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic educational fixture using standard Python 3. It models telemetry resilience without requiring live Application Insights or OpenTelemetry collectors.

---

## Contract & Expected Behavior

| Case | Events | Status | Duration | Anomaly Handled |
| :--- | :--- | :--- | :--- | :--- |
| **Request A** | `start(100)` -> 2 tool calls -> `end(112)` | `success` | 12 ms | Canonical success |
| **Request B** | `start(150)` -> `failed(165)` | `failed` | 15 ms | Agent failure recorded |
| **Incomplete** | `start(200)` -> tool call (no end event) | `incomplete` | `None` (not 0) | Unfinished execution |
| **Corrupt Data**| `timestamp_ms = -99` | `corrupt_data` | `None` | Logged to anomaly list |
| **Recovery** | Subsequent valid request `req_recovery` | `success` | 15 ms | Clean immediate recovery |

---

## Running the Lab

### Run Demonstration
```bash
python3 10-ai-agents-production/applied-labs/r17-t018/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 10-ai-agents-production/applied-labs/r17-t018 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (Python standard library only).
- Zero external package dependencies.
