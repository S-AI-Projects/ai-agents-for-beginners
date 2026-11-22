# Applied Lab: Request Router with Failure and Recovery (R17-T047)

## Overview & Lesson Alignment

In **Lesson 02: Exploring Agentic Frameworks**, building robust agentic systems requires understanding how frameworks manage routing, error boundaries, and state resilience. When user requests enter an agent framework:
1. **Dynamic Intent Routing**: Requests are parsed and directed to domain-specific agent handlers (`support` for help, `calculator` for math, `fallback` for unrecognized queries).
2. **Ambiguity Resolution**: When queries contain overlapping intents, framework routers follow a documented priority hierarchy.
3. **Failure Isolation & Non-Corrupting Recovery**: If a malformed, null, or empty query arrives, the router must reject it with an explicit exception without corrupting internal state or session lifecycles, guaranteeing that subsequent valid queries continue to route seamlessly.

This applied lab implements an in-memory **Framework Request Router** with explicit failure handling and recovery verification.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a zero-dependency educational module implemented exclusively with the Python 3 standard library (`dataclasses`, `typing`, `unittest`). No external cloud frameworks, live LLM endpoints, or databases are required.

---

## Core Routing Contract & Priority Hierarchy

Incoming requests are classified and dispatched according to:

| Category | Trigger Signals | Target Handler | Priority Rank |
| :--- | :--- | :--- | :---: |
| **`help` / `support`** | `help`, `support`, `assist`, `trouble`, `issue`, `login`, `password` | `support` | **1** (Highest) |
| **`calculate` / `calculator`** | `calculate`, `calc`, `math`, `sum`, arithmetic expressions (`\d+ [\+\-\*\/] \d+`) | `calculator` | **2** |
| **`unknown`** | Unrecognized queries without matching intent signals | `fallback` | **3** (Lowest) |

### Ambiguity Priority Rule
When a request exhibits signals for multiple domains (e.g., *"Help me calculate my travel budget"*), the router resolves the collision using:
$$\text{support} > \text{calculator} > \text{fallback}$$

---

## Failure & Recovery Contract

Robust agent frameworks must guard against malformed inputs:

1. **Validation Boundaries**:
   - `None` input $\to$ raises `InvalidRequestError("Request cannot be None")`
   - Non-string input (e.g., integers, lists) $\to$ raises `InvalidRequestError("Request must be a string")`
   - Empty or whitespace-only string (`""`, `"   "`) $\to$ raises `InvalidRequestError("Request cannot be empty or whitespace-only")`
2. **Resilience & State Recovery**:
   - Raising an `InvalidRequestError` is clean and side-effect free.
   - Internal memory, routing rules, and handlers are unaffected.
   - The immediate next request (e.g., `"Help me recover my account"`) succeeds without requiring framework restarts or resets.
3. **Audit Trail**:
   - Every transaction (successful routes and rejected errors) is recorded in an immutable structured audit log.

---

## Quick Invocation & Testing

```bash
# Run demonstration script and observe failure & recovery walkthrough
python3 02-explore-agentic-frameworks/applied-labs/r17-t047/example.py

# Run automated unit test suite
python3 -m unittest discover -s 02-explore-agentic-frameworks/applied-labs/r17-t047 -p "test_*.py" -v
```
