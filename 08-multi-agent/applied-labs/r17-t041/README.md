# Applied Lab: Dependency-Plan Validation & Topological Ordering (R17-T041)

## Overview & Lesson Alignment

In **Lesson 08: Multi-agent design patterns**, complex workflows are decomposed into specialized subtasks assigned to different collaborating agents (e.g., flight, hotel, and car rental booking agents, or refund, seller, and payment agents). In any multi-agent architecture:
1. **Dependency Graphs**: Certain subtasks depend on results from prior tasks (e.g., hotel booking requires flight arrival dates).
2. **Missing Dependencies**: If an agent requests data from an undefined or unknown task, the workflow cannot be scheduled.
3. **Deadlock / Circular Dependencies**: If Agent A awaits Agent B while Agent B awaits Agent A ($A \to B \to A$), execution enters an unrecoverable deadlock.
4. **Execution Ordering**: Agents must execute in valid topological order so prerequisites are satisfied before consumers start.

This applied lab implements an in-memory, deterministic **Dependency-Plan Validator and Topological Scheduler** that verifies multi-agent plans prior to execution.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a zero-dependency educational module implemented exclusively with the Python 3 standard library (`dataclasses`, `typing`, `unittest`). The tasks, agents, and dependencies are synthetic teaching fixtures designed to illustrate DAG validation and boundary conditions. No external APIs, cloud services, GPUs, or trained model downloads are required.

---

## Canonical Task Fixture & Contract

### Canonical Scenario
```python
CANONICAL_PLAN = {
    "A": [],        # Task A: Independent initial task (e.g. Flight Finder)
    "B": ["A"],     # Task B: Depends on A (e.g. Hotel Booker)
    "C": ["B"],     # Task C: Depends on B (e.g. Rental Car Booker)
}
```

- **Topological Order**: `["A", "B", "C"]`
- **Execution Invariant**: Task A completes first, unlocking Task B; Task B completes, unlocking Task C.

---

## Boundary and Invalid Case Decisions

| Scenario | Input Fixture | Expected Decision | Rationale |
| :--- | :--- | :--- | :--- |
| **Smallest Valid (Empty)** | `{}` | `[]` (Empty order) | A workflow with 0 tasks is vacuously valid and requires no agent actions. |
| **Single Task** | `{"A": []}` | `["A"]` | Single isolated task has all prerequisites satisfied immediately. |
| **Independent Tasks** | `{"B": [], "A": []}` | `["A", "B"]` | Tasks with equal zero-dependency rank are scheduled deterministically using alphabetical tie-breaking. |
| **Diamond DAG** | `{"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}` | `["A", "B", "C", "D"]` | Both branches must complete before the sink task `D` is scheduled. |
| **Missing Dependency** | `{"B": ["UNKNOWN_X"]}` | `MissingDependencyError` | Task `B` requires task `UNKNOWN_X`, which does not exist in the plan. The error explicitly surfaces `UNKNOWN_X`. |
| **Direct Cycle** | `{"A": ["B"], "B": ["A"]}` | `CycleDetectedError` | Direct circular dependency ($A \leftrightarrow B$) is rejected before any agent starts. |
| **Self-Dependency** | `{"A": ["A"]}` | `CycleDetectedError` | A task cannot wait on its own completion. |
| **Indirect Cycle** | `{"A": ["C"], "B": ["A"], "C": ["B"]}` | `CycleDetectedError` | Multi-hop cycle ($A \to C \to B \to A$) is detected and rejected. |

---

## Applied Scenario Assessment (Three Questions)

### Question 1: Output Prediction
- **Scenario**: Given `CANONICAL_PLAN = {"A": [], "B": ["A"], "C": ["B"]}`, what is the exact execution order?
- **Predicted Output**: `["A", "B", "C"]`
- **Rationale**: Task A has in-degree 0 and executes first. Its completion decrements B's in-degree to 0. B executes, decrementing C's in-degree to 0. Finally C executes.

### Question 2: Cycle Rejection
- **Scenario**: Given `plan = {"A": ["B"], "B": ["A"]}`, how does the scheduler respond?
- **Outcome**: Raises `CycleDetectedError`.
- **Rationale**: Mutual dependency prevents in-degree from reaching 0 for either task; Kahn's algorithm detects remaining tasks and halts before execution to avoid deadlocks.

### Question 3: Missing Dependency Reporting
- **Scenario**: Given `plan = {"task_1": ["missing_step"]}`, how does the scheduler diagnose the failure?
- **Outcome**: Raises `MissingDependencyError(task_id="task_1", missing_dep_id="missing_step")`.
- **Rationale**: Validates that all referenced keys exist in the plan catalog before attempting graph construction.

---

## Quick Invocation & Testing

```bash
# Run the local example and boundary-case demonstrations
python3 08-multi-agent/applied-labs/r17-t041/example.py

# Run the automated unit test suite
python3 -m unittest discover -s 08-multi-agent/applied-labs/r17-t041 -p "test_*.py" -v
```
