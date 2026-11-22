# Applied Lab: Production Trace Aggregation & Privacy Safeguarding (R17-T046)

## Overview & Lesson Alignment

In **Lesson 10: AI Agents in Production: Observability & Evaluation**, production multi-agent systems emit high-volume telemetry streams (traces and spans). To monitor agent health, detect latency bottlenecks, track tool usage, and evaluate failure rates:
1. **Trace Event Aggregation**: Unstructured raw event streams must be grouped by `request_id` to compute end-to-end request latency, tool invocations, and final completion status.
2. **Handling Incomplete Executions**: Production agents frequently suffer network disconnections, timeout kills, or unhandled crashes where no terminating `END` event is received. These must be marked as `INCOMPLETE` with a duration of `None` (not `0`), preventing skew in latency calculations.
3. **Data Minimization & Privacy Safeguarding**: Production telemetry pipelines must separate operational metrics from sensitive conversational payloads. Raw prompts and PII must be omitted from aggregated metrics exports.

This applied lab implements a **Production Trace Aggregator** with strict privacy safeguards and worked example verification.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a zero-dependency educational module implemented exclusively with the Python 3 standard library (`dataclasses`, `typing`, `unittest`). No external OpenTelemetry collectors, cloud APM services, or databases are required.

---

## Core Contract & Aggregation Rules

For every request $R$ in the telemetry event stream:
- **`tool_call_count`**: Number of `TOOL_CALL` events associated with $R$.
- **`status`**:
  - `SUCCESS`: Normal completion marked by an `END` event without error.
  - `FAILED`: Request aborted or terminated via an `ERROR` event.
  - `INCOMPLETE`: Request initiated (`START`), but neither an `END` nor `ERROR` event arrived.
- **`duration_ms`**:
  - For `SUCCESS` or `FAILED` requests: $\text{timestamp}_{\text{end}} - \text{timestamp}_{\text{start}}$.
  - For `INCOMPLETE` requests: `None` (explicitly **not** 0 or 0.0 to prevent corrupting latency averages).
- **Privacy Safeguard**:
  - `prompt`, `raw_input`, and user queries are completely excluded from the aggregated metrics schema.

---

## Worked Example: Input to Output Walkthrough

### 1. Raw Input Event Stream

| Request ID | Event Type | Timestamp (ms) | Payload / Attributes |
| :---: | :---: | :---: | :--- |
| `A` | `START` | `1000.0` | `prompt="calculate annual budget...", user_id="usr-123"` |
| `A` | `TOOL_CALL` | `1004.0` | `tool_name="currency_converter"` |
| `A` | `TOOL_CALL` | `1009.0` | `tool_name="budget_calculator"` |
| `A` | `END` | `1012.0` | `status="SUCCESS"` |
| `B` | `START` | `2000.0` | `prompt="execute confidential contract...", user_id="usr-456"` |
| `B` | `TOOL_CALL` | `2005.0` | `tool_name="smart_contract_signer"` |
| `B` | `ERROR` | `2018.0` | `error="AuthenticationFailedException"` |
| `C` | `START` | `3000.0` | `prompt="stream real-time sensor...", user_id="usr-789"` |
| `C` | `TOOL_CALL` | `3015.0` | `tool_name="iot_sensor_stream"` |
| *(None)* | *(None)* | *(None)* | *(Request C terminates abruptly without emitting an END or ERROR event)* |

### 2. Aggregated Output Metrics

| Request ID | Status | Tool Calls | Duration (ms) | Prompt Omitted? | Rationale |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **`A`** | `SUCCESS` | **2** | **12.0 ms** | **YES** | Started at 1000ms, completed at 1012ms ($1012 - 1000 = 12$). |
| **`B`** | `FAILED` | **1** | **18.0 ms** | **YES** | Started at 2000ms, terminated by error at 2018ms ($2018 - 2000 = 18$). |
| **`C`** | `INCOMPLETE` | **1** | `None` | **YES** | Started and called 1 tool, but missing end event. Duration is `None`, not 0. |

---

## Quick Invocation & Testing

```bash
# Run demonstration script and view worked example output
python3 10-ai-agents-production/applied-labs/r17-t046/example.py

# Run automated unit test suite
python3 -m unittest discover -s 10-ai-agents-production/applied-labs/r17-t046 -p "test_*.py" -v
```
