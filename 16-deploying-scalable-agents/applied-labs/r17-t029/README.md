# Applied Lab: Trace Aggregation — Evaluation Experiment (R17-T029)

## Overview & Lesson Alignment

In **Lesson 16: Deploying Scalable Agents with Microsoft Foundry**, transitioning an agent prototype to production requires comprehensive operational observability. Distributed agent workflows emit discrete telemetry events (spans) as tools are invoked, plans are generated, and responses are returned.

This applied lab implements a local, privacy-preserving **Trace Aggregator** that groups telemetry events by correlation ID (`request_id`) and computes key operational metrics:
1. **Correlation by Request ID**: Reconstructs execution lifecycles across distributed components.
2. **Execution Duration**: Computes total end-to-end latency from start and end events.
3. **Tool Call Accounting**: Tracks the frequency and names of tools invoked per request.
4. **Failure Tracking**: Captures terminal error codes and operational failure states.
5. **Incomplete Trace Detection**: Unclosed traces (e.g. from container crashes, network drops, or timeouts) are explicitly classified as `incomplete` with `duration_ms = None`, rather than falsely assigned duration zero.
6. **Telemetry Privacy**: Strict enforcement ensures raw prompt contents are excluded from aggregated reporting pipelines.
7. **Controlled Evaluation Experiment**: Compares 3 controlled input sizes (Small, Medium, Large) across processing latency, event throughput, completeness detection, and privacy compliance.

> [!NOTE]
> **Simulation Disclaimer**: This lab is a self-contained, deterministic educational simulation written using only the Python 3 standard library. It models the core aggregation and privacy mechanics of OpenTelemetry and Microsoft Foundry monitoring without requiring Azure Application Insights, Foundry cloud subscriptions, or physical cluster hardware.

---

## Canonical Contract & Key Scenarios

The aggregator validates the following canonical telemetry cases:

| Request ID | Milestones / Spans | Duration | Tool Calls | Outcome Status | Completeness |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `request_A` | Start (100.0ms), `get_user_profile` (104.0ms), `update_user_preference` (108.0ms), End (112.0ms) | **12.0 ms** | **2** | `success` | Complete (`True`) |
| `request_B` | Start (200.0ms), `process_payment` (205.0ms), End (215.0ms) with failure | **15.0 ms** | **1** | `failure` | Complete (`True`) |
| `request_C` | Start (300.0ms), `stream_query` (308.0ms), missing end event | **`None`** (not `0.0`) | **1** | `incomplete` | Incomplete (`False`) |

### Telemetry Privacy Guarantee
Raw events may contain sensitive customer prompt contents (e.g., `"CONFIDENTIAL_PATIENT_SSN_12345"`). The `AggregatedRequestSummary` data contract completely omits the `prompt` field, ensuring aggregated analytics dashboards do not leak PII.

---

## Controlled Evaluation Experiment

The lab benchmarks trace aggregation across 3 controlled configurations:

- **Config S (Small)**: 3 canonical requests (9 discrete events)
- **Config M (Medium)**: 25 synthetic requests (approx 81 events, including 5 incomplete spans and 3 failures)
- **Config L (Large)**: 100 synthetic requests (approx 330 events, including 20 incomplete spans and 12 failures)

### Observed Trade-Offs
- **Latency Scaling**: Average processing latency scales linearly with event count ($O(N)$), exhibiting sub-millisecond execution even on large event batches.
- **Throughput Stability**: Event throughput remains steady across batch sizes (~4.8M to ~5.9M events/second in local memory).
- **Correctness Invariants**: 100% of incomplete traces are detected without zero-duration corruption, and zero prompt contents leak across all configurations.

---

## Running the Lab

### Run Demonstration & Experiment
```bash
python3 16-deploying-scalable-agents/applied-labs/r17-t029/example.py
```

### Run Automated Unit Test Suite
```bash
python3 -m unittest discover -s 16-deploying-scalable-agents/applied-labs/r17-t029 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (standard library only).
- Zero external package dependencies, zero cloud API keys required.
