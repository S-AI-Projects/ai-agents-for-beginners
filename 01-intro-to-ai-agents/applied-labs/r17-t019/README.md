# Applied Lab: Bounded Agent Loop — Evaluation Experiment (R17-T019)

## Overview & Lesson Alignment

In **Lesson 01: Introduction to AI Agents and Agent Use Cases**, agents are defined as autonomous systems that perceive their environment, reason over a goal, and execute actions in a loop. Because autonomous loops risk executing indefinitely when faced with ambiguous goals or unhandled states, bounding loop iterations is the most fundamental architectural guardrail.

This lab implements and evaluates a bounded agent execution loop:
1. **Loop Bounding**: Implements a strict step ceiling (default `MAX_STEPS = 3`).
2. **Normal Termination**: Allows graceful termination when the agent issues a `stop` action.
3. **Budget Exceeded Protection**: Endless plans halt strictly at the budget ceiling with `budget_exceeded`.
4. **Post-Stop Invariant**: Actions scheduled after `stop` are immediately dropped.
5. **Controlled Evaluation Experiment**: Evaluates three budget configurations (`budget=2`, `budget=3`, `budget=5`) measuring completion viability against runaway containment.

> [!NOTE]
> **Simulation Disclaimer**: This fixture is an educational model implemented in Python 3 standard library. It demonstrates deterministic lifecycle control without making claims about commercial foundation model accuracy or real-world inference latencies.

---

## Controlled Evaluation Experiment (Three Configurations)

| Configuration | Step Budget | Canonical 3-Step Completion | Endless Loop Containment | Evaluated Trade-off |
| :--- | :--- | :--- | :--- | :--- |
| **Conservative** | `budget = 2` | ❌ Fails (`budget_exceeded`) | Halts at Step 2 | Low compute risk, but causes false-positive truncation of valid 3-step goals. |
| **Optimal** | `budget = 3` | ✅ Passes (`terminated_normally`) | Halts at Step 3 | Exact fit for 3-step tasks; bounds runaway loops tightly. |
| **Permissive** | `budget = 5` | ✅ Passes (`terminated_normally`) | Halts at Step 5 | Accommodates larger valid tasks, but allows infinite loops to waste 5 steps. |

---

## Running the Lab

### Run Demonstration & Experiment
```bash
python3 01-intro-to-ai-agents/applied-labs/r17-t019/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 01-intro-to-ai-agents/applied-labs/r17-t019 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (standard library only).
- Zero external package dependencies.
