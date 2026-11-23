# Applied Lab: Bounded Conversation Memory — Scenario Assessment (R17-T020)

## Overview & Lesson Alignment

In **Lesson 11: Using Agentic Protocols (MCP, A2A and NLWeb)**, agents communicate across standardized boundaries. In persistent multi-turn conversations, managing agent context size is critical to prevent context window saturation and memory leaks:
1. **Bounded FIFO Retention**: Memory capacity is bounded to at most 3 conversation records in arrival order. When a 4th record arrives, the oldest record is evicted (retaining `["B", "C", "D"]`).
2. **Encapsulation & Defensive Copying**: The memory store exposes defensive copies to external callers. Mutating, clearing, or modifying the returned collection has zero impact on internal state.
3. **Applied Scenario Assessments**: Contains 3 applied questions covering output prediction, failure diagnosis, and boundary policy decisions with executable unit test checks.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic educational fixture implemented in the Python 3 standard library. It models protocol message windowing without requiring live MCP servers or external vector databases.

---

## Contract & Expected Behavior

| Action | Stored IDs | Evicted | Invariant Verified |
| :--- | :--- | :--- | :--- |
| Initial state | `[]` | None | Clean initialization |
| Add `A, B, C` | `["A", "B", "C"]` | None | Within capacity (3/3) |
| Add `D` | `["B", "C", "D"]` | `A` | FIFO sliding window eviction |
| External `.clear()` | `["B", "C", "D"]` | None | Defensive copy preserves stored memory |

---

## Applied Scenario Assessment (Three Questions)

1. **Question 1: Predict an Output**
   - *Prompt*: Adding records A, B, C, D to a bounded store of capacity 3 retains which records in arrival order?
   - *Answer*: `["B", "C", "D"]`
   - *Rationale*: FIFO eviction discards the oldest record ("A") once capacity is saturated.

2. **Question 2: Diagnose a Failure**
   - *Prompt*: Why does modifying the list returned by `get_records()` not corrupt internal agent memory?
   - *Answer*: `DEFENSIVE_COPYING`
   - *Rationale*: `get_records()` returns a separate list instance, preventing external modification of internal state.

3. **Question 3: Choose a Boundary Policy**
   - *Prompt*: Which eviction policy preserves the most relevant conversational context when message capacity is saturated?
   - *Answer*: `FIFO_SLIDING_WINDOW`
   - *Rationale*: Most recent dialogue context is essential for downstream agent steps and tool dispatch.

---

## Running the Lab

### Run Demonstration & Questions
```bash
python3 11-agentic-protocols/applied-labs/r17-t020/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 11-agentic-protocols/applied-labs/r17-t020 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (standard library only).
- Zero external package dependencies.
