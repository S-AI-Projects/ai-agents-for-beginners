# Applied Lab: Bounded Agent Loop — Boundary-Case Lesson Extension (R17-T012)

## Overview & Lesson Alignment

In **Lesson 14: Exploring Microsoft Agent Framework**, agents coordinate complex workflows across multi-turn executions. Without explicit step boundaries, an agent caught in a recursive reasoning cycle or looping prompt can consume unbounded compute and API tokens.

This applied lab implements a deterministic, boundary-checked agent execution loop:
1. **Explicit Step Budget**: The agent is bounded to at most three steps (`MAX_STEPS = 3`).
2. **Explicit Stop Control**: An explicit `stop` action terminates the agent loop gracefully.
3. **Budget Exceeded Protection**: If an execution loop does not signal `stop` within three steps, it is forcefully halted with `budget_exceeded`.
4. **Post-Stop Invariant**: Any actions scheduled after `stop` are strictly dropped and never executed.

> [!NOTE]
> **Simulation Disclaimer**: This fixture is an educational model implemented in Python 3 standard library. It demonstrates cycle bounding and lifecycle control without requiring Azure OpenAI quotas, hosted agent services, or external orchestrators.

---

## Boundary Decisions & Contract

| Scenario | Input Plan | Steps Executed | Exit Status | Invariant Verified |
| :--- | :--- | :--- | :--- | :--- |
| **Smallest Valid** | `["stop"]` | 1 | `terminated_normally` | Immediate clean halt |
| **Canonical Normal** | `["inspect", "answer", "stop"]` | 3 | `terminated_normally` | All actions executed up to stop |
| **Boundary Exceeded** | `["inspect", "inspect", "inspect", "inspect"]` | 3 | `budget_exceeded` | Truncated at exactly 3 steps |
| **Post-Stop Invariant** | `["inspect", "stop", "answer"]` | 2 | `terminated_normally` | `answer` is never called |

---

## Running the Lab

### Run Demonstration
```bash
python3 14-microsoft-agent-framework/applied-labs/r17-t012/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 14-microsoft-agent-framework/applied-labs/r17-t012 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (Python standard library only).
- No external packages or API keys required.
