# Applied Lab: Comparative Topological Sorting — Kahn's Algorithm vs DFS Post-Order (R17-T042)

## Overview & Lesson Alignment

In **Lesson 08: Multi-agent design patterns**, complex workflows are decomposed into specialized subtasks assigned to collaborating agents (e.g., flight, hotel, and car rental booking agents, or fraud, payment, and compliance agents). In any multi-agent architecture:
1. **Dependency Graphs**: Subtasks depend on outputs from upstream tasks (e.g., payment requires fraud approval and invoice generation).
2. **Missing Dependencies**: If an agent requests data from an undefined or unknown task, the workflow cannot be scheduled.
3. **Deadlocks & Cycles**: Circular dependencies (e.g., Agent A awaiting Agent B while Agent B awaits Agent A) lead to unrecoverable system deadlocks.
4. **Execution Scheduling**: Tasks must execute in a valid topological order so prerequisites are satisfied before consumers start.

This applied lab compares two classical graph algorithms for multi-agent plan validation and topological ordering:
- **Kahn's Algorithm**: In-degree queue / BFS level-by-level scheduling.
- **DFS Post-Order Traversal with Reverse**: Depth-first recursion / branch-first scheduling.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a zero-dependency educational module implemented exclusively with the Python 3 standard library (`dataclasses`, `typing`, `unittest`). The tasks, agents, and dependencies are synthetic teaching fixtures designed to illustrate DAG validation and algorithm trade-offs. No external APIs, cloud services, GPUs, or trained model downloads are required.

---

## Core Contract & Behavioral Guarantees

Both algorithms implement identical core validation contracts:

1. **Topological Order Invariant**:
   For every task $T$ with dependencies $D$, every prerequisite $d \in D$ appears before $T$ in the execution schedule:
   $$\text{index}(d) < \text{index}(T) \quad \forall d \in \text{dependencies}(T)$$
2. **Missing Dependency Reporting**:
   If task $T$ references an unknown dependency ID $X \notin \text{plan}$, validation halts immediately raising `MissingDependencyError(task_id=T, missing_dep_id=X)`.
3. **Cycle Rejection**:
   If tasks form a circular dependency (direct $A \leftrightarrow B$, self $A \to A$, or multi-hop loops), validation halts immediately raising `CycleDetectedError(cycle_path=...)`.
4. **Deterministic Tie-Breaking**:
   When multiple tasks are ready to execute concurrently, alphabetical tie-breaking ensures 100% reproducible execution schedules.

---

## Algorithm Comparison: Kahn's vs DFS Post-Order

| Dimension | Kahn's Algorithm (BFS In-Degree Queue) | DFS Post-Order Traversal with Reverse |
| :--- | :--- | :--- |
| **Traversal Strategy** | Breadth-First Search (BFS) / Level-by-level | Depth-First Search (DFS) / Branch-first |
| **Prerequisite Tracking** | Explicit in-degree count per task | Implicit call-stack and visited state tracking |
| **Ready Tasks** | All zero in-degree tasks immediately available in queue | Discovered via deep recursion down prerequisite trees |
| **Multi-Agent Parallelism** | **Ideal for multi-agent dispatch**: Naturally exposes batches of parallelizable tasks at each stage | Naturally discovers sequential dependency chains (useful for single-threaded or handoff flows) |
| **Cycle Detection** | Count of ordered tasks $< |V|$ at completion | Detected immediately during traversal via back-edge (`state == 1`) |
| **Time Complexity** | $O(|V| + |E|)$ | $O(|V| + |E|)$ |
| **Space Complexity** | $O(|V| + |E|)$ for in-degrees and queue | $O(|V| + |E|)$ for call stack and visited sets |

---

## Comparative Results Across Test Fixtures

| Fixture Scenario | Input Graph | Kahn's Output | DFS Reverse Output | Equivalence Status |
| :--- | :--- | :--- | :--- | :--- |
| **Canonical Linear** | `{"A": [], "B": ["A"], "C": ["B"]}` | `["A", "B", "C"]` | `["A", "B", "C"]` | **Identical & Valid** |
| **Empty Plan** | `{}` | `[]` | `[]` | **Identical & Valid** |
| **Single Task** | `{"A": []}` | `["A"]` | `["A"]` | **Identical & Valid** |
| **Independent Tasks** | `{"B": [], "A": []}` | `["A", "B"]` | `["A", "B"]` | **Identical & Valid** (Alphabetical tie-break) |
| **Diamond DAG** | `{"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}` | `["A", "B", "C", "D"]` | `["A", "B", "C", "D"]` | **Identical & Valid** |
| **Multi-Branch Pipeline** | `START -> DATA_A, DATA_B -> PROCESS_A, PROCESS_B -> JOIN -> REPORT` | `['START', 'DATA_A', 'DATA_B', 'PROCESS_A', 'PROCESS_B', 'JOIN', 'REPORT']` (Level-order) | `['START', 'DATA_A', 'PROCESS_A', 'DATA_B', 'PROCESS_B', 'JOIN', 'REPORT']` (Branch-order) | **Both Valid Topological Sorts** (BFS vs DFS exploration order) |
| **Direct Cycle** | `{"A": ["B"], "B": ["A"]}` | `CycleDetectedError` | `CycleDetectedError` | **Identical Rejection** |
| **Self Cycle** | `{"A": ["A"]}` | `CycleDetectedError` | `CycleDetectedError` | **Identical Rejection** |
| **Indirect Triangle** | `{"A": ["C"], "B": ["A"], "C": ["B"]}` | `CycleDetectedError` | `CycleDetectedError` | **Identical Rejection** |
| **Missing Dependency** | `{"Task1": ["NON_EXISTENT"]}` | `MissingDependencyError` | `MissingDependencyError` | **Identical Diagnosis** (surfaces missing ID) |

---

## Quick Invocation & Testing

```bash
# Run comparative algorithm demonstration
python3 08-multi-agent/applied-labs/r17-t042/example.py

# Run automated unit test suite
python3 -m unittest discover -s 08-multi-agent/applied-labs/r17-t042 -p "test_*.py" -v
```
