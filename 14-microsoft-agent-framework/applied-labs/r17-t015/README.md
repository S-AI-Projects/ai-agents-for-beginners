# Applied Lab: Bounded Agent Loop — Offline Service Adapter (R17-T015)

## Overview & Lesson Alignment

In **Lesson 14: Exploring Microsoft Agent Framework**, agents integrate with backend model and tool endpoints. Direct integration with live cloud services during early development or unit testing introduces test flakiness, latency, network dependencies, and quota costs.

This lab isolates agent loop execution using an **Offline Service Adapter**:
1. **Adapter Interface (`AgentServiceAdapter`)**: Establishes a standard contract for inspection, answering, and termination.
2. **Deterministic Implementation (`LocalDeterministicAdapter`)**: Provides zero-dependency, reproducible behavior.
3. **Step Budget Limit**: Halts execution at a maximum of 3 steps; endless plans stop with `budget_exceeded`.
4. **Post-Stop Invariant**: Guarantees no adapter methods are invoked once `stop` is signaled.

> [!NOTE]
> **Limitations of the Offline Mock**:
> While the deterministic adapter guarantees predictable loop semantics, it **does not establish**:
> - Real-world network latency or transient HTTP errors (e.g. 503, 429 rate limiting).
> - Azure Entra ID / OAuth credential expiration and token refresh logic.
> - LLM token limit truncation or model hallucination behaviors.
> Production verification still requires live smoke tests as discussed in Lesson 16.

---

## Contract & Expected Behavior

| Plan | Step Limit | Exit Status | Recorded Actions |
| :--- | :--- | :--- | :--- |
| `["inspect", "answer", "stop"]` | 3 | `terminated_normally` | `inspect`, `answer`, `stop` |
| `["inspect", "inspect", "inspect", "inspect"]` | 3 | `budget_exceeded` | `inspect`, `inspect`, `inspect` |
| `["inspect", "stop", "answer"]` | 3 | `terminated_normally` | `inspect`, `stop` (`answer` dropped) |

---

## Running the Lab

### Run Demonstration
```bash
python3 14-microsoft-agent-framework/applied-labs/r17-t015/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 14-microsoft-agent-framework/applied-labs/r17-t015 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (Python standard library only).
- Zero cloud credentials or external dependencies required.
