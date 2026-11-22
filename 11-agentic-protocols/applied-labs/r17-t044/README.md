# Applied Lab: Bounded Conversation Memory with State Trace (R17-T044)

## Overview & Lesson Alignment

In **Lesson 11: Using Agentic Protocols (MCP, A2A, and NLWeb)**, agents communicate across standardized boundaries. Whether passing context between an MCP Client and an MCP Server, or executing multi-turn handoffs via Agent-to-Agent (A2A) protocol exchanges, managing **bounded conversational memory** is a fundamental architectural requirement:
1. **Context Window Protection**: LLM context windows and protocol payloads have strict limits; unboundedly appending conversation history leads to token overflow and skyrocketing latency.
2. **Predictable Sliding Windows**: Agents must retain only the most recent relevant interactions (e.g., $N=3$ most recent turns) in strict chronological arrival order.
3. **State Isolation & Immutability**: Modifying memory views passed across protocol boundaries must not mutate the agent's internal storage (defensive copying).
4. **Auditability & State Tracing**: For safety and debugging, protocol adapters require an inspectable, immutable state trace recording intermediate snapshots after every discrete operation.

This applied lab implements a **Bounded Conversation Memory** with defensive copying and formal intermediate state tracing.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a zero-dependency educational module implemented exclusively with the Python 3 standard library (`collections`, `dataclasses`, `typing`, `unittest`). No external protocol servers, cloud APIs, GPUs, or trained model downloads are required.

---

## Canonical Scenario & Core Contract

### Scenario Specification
- **Maximum Capacity**: 3 records.
- **Arrival Sequence**: Add record `"A"`, then `"B"`, then `"C"`, then `"D"`.
- **Expected Outcome**: Memory retains `["B", "C", "D"]` in arrival order. Record `"A"` is evicted via FIFO sliding window.
- **Immutability Invariant**: Mutating the returned memory list externally (e.g., calling `.append("X")` or `.clear()`) has zero effect on internal memory.

---

## Intermediate State Trace Progression

The memory records an immutable `StateSnapshot` after each state transition:

| Step | Action | Item Added | Item Evicted | Memory State After Step | Current Size | Capacity Invariant |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | `INIT` | `None` | `None` | `[]` | 0 / 3 | **PASS** ($\le 3$) |
| **1** | `ADD` | `"A"` | `None` | `["A"]` | 1 / 3 | **PASS** ($\le 3$) |
| **2** | `ADD` | `"B"` | `None` | `["A", "B"]` | 2 / 3 | **PASS** ($\le 3$) |
| **3** | `ADD` | `"C"` | `None` | `["A", "B", "C"]` | 3 / 3 | **PASS** ($\le 3$) |
| **4** | `ADD` | `"D"` | `"A"` | `["B", "C", "D"]` | 3 / 3 | **PASS** ($\le 3$) |

---

## Formal Invariants & Guarantees

1. **Capacity Invariant**:
   $$\forall \text{ snapshot } s \in \text{trace}: \quad |s.\text{memory\_state}| \le \text{max\_capacity} \quad (3)$$
   Guaranteed before and after every operation (`add`, `clear`, `init`).
2. **Defensive Copy Immutability**:
   `memory.get_records()` returns a deep defensive copy. External callers cannot alter internal state by modifying the returned list or its elements.
3. **Arrival Order Invariant**:
   For any retained elements $x, y$, if $x$ was added before $y$, then $\text{index}(x) < \text{index}(y)$ in all snapshots and return values.

---

## Quick Invocation & Testing

```bash
# Run demonstration script and view intermediate state trace
python3 11-agentic-protocols/applied-labs/r17-t044/example.py

# Run automated unit test suite
python3 -m unittest discover -s 11-agentic-protocols/applied-labs/r17-t044 -p "test_*.py" -v
```
