"""Applied Lab: Dependency-Plan Validation & Topological Ordering (R17-T041)

Lesson Alignment:
08-multi-agent (Multi-agent design patterns)

Contract:
- Validate and topologically order a task plan across multiple agents.
- Detect missing dependencies before execution (reported by unknown task ID).
- Detect and reject cyclic dependencies (e.g., A -> B -> A).
- Handle boundary cases (empty plan, single task, independent tasks, diamond graphs).
- Provide a deterministic, zero-dependency local simulation using standard library Python 3.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
import sys


class PlanValidationError(Exception):
    """Base exception for plan validation errors."""
    pass


class MissingDependencyError(PlanValidationError):
    """Raised when a task declares a dependency on a task ID that does not exist in the plan."""

    def __init__(self, task_id: str, missing_dep_id: str):
        self.task_id = task_id
        self.missing_dep_id = missing_dep_id
        super().__init__(
            f"Task '{task_id}' declares unknown dependency '{missing_dep_id}'. "
            f"Dependency task ID '{missing_dep_id}' was not found in the plan."
        )


class CycleDetectedError(PlanValidationError):
    """Raised when circular dependencies exist among tasks in the plan."""

    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        path_str = " -> ".join(cycle_path)
        super().__init__(
            f"Circular dependency detected in plan: {path_str}. "
            "Execution rejected to prevent infinite deadlocks."
        )


@dataclass(frozen=True)
class TaskDefinition:
    """Represents an agent task within a multi-agent plan."""
    task_id: str
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: str = "general-worker"
    description: str = ""


# Canonical fixtures
CANONICAL_PLAN: Dict[str, List[str]] = {
    "A": [],        # A has no dependencies
    "B": ["A"],     # B depends on A
    "C": ["B"],     # C depends on B
}


def _find_cycle(plan: Dict[str, List[str]]) -> List[str]:
    """Helper to detect and reconstruct a cycle path in a directed dependency graph.
    
    Graph convention: edge u -> v means u depends on v, or v must precede u.
    Here: task -> dependencies. If A depends on B and B depends on A:
    A depends on B, B depends on A.
    """
    # 0 = unvisited, 1 = visiting (in recursion stack), 2 = visited
    state: Dict[str, int] = {k: 0 for k in plan}
    parent: Dict[str, Optional[str]] = {k: None for k in plan}
    cycle_nodes: List[str] = []

    def dfs(node: str, stack: List[str]) -> bool:
        state[node] = 1
        stack.append(node)

        for dep in plan.get(node, []):
            if dep not in plan:
                continue
            if state[dep] == 1:
                # Cycle found!
                cycle_start_idx = stack.index(dep)
                cycle_nodes.extend(stack[cycle_start_idx:])
                cycle_nodes.append(dep)
                return True
            elif state[dep] == 0:
                parent[dep] = node
                if dfs(dep, stack):
                    return True

        stack.pop()
        state[node] = 2
        return False

    for node in sorted(plan.keys()):
        if state[node] == 0:
            if dfs(node, []):
                return cycle_nodes
    return []


def validate_and_order_plan(plan: Dict[str, List[str]]) -> List[str]:
    """Validates the given task plan and returns tasks in valid topological execution order.

    Rules:
    1. Every dependency referenced by a task must exist as a key in `plan`.
       If unknown, raises `MissingDependencyError` identifying the unknown task ID.
    2. Self-dependencies (e.g. A -> A) and circular dependencies (e.g. A -> B -> A)
       must be detected and rejected with `CycleDetectedError`.
    3. Boundary cases:
       - Empty plan `{}` returns `[]`.
       - Single task `{'A': []}` returns `['A']`.
       - Independent tasks (no deps) return deterministically sorted list.
    4. Deterministic tie-breaking: when multiple tasks are ready to run simultaneously,
       they are scheduled in alphabetical order of their task IDs.

    Args:
        plan: Dictionary mapping task_id -> list of dependency task_ids.

    Returns:
        List of task IDs ordered such that every dependency precedes its dependent tasks.

    Raises:
        MissingDependencyError: If a dependency ID is unknown.
        CycleDetectedError: If a cycle is detected.
    """
    if not plan:
        return []

    # 1. Missing dependency validation
    for task_id, deps in plan.items():
        for dep in deps:
            if dep not in plan:
                raise MissingDependencyError(task_id=task_id, missing_dep_id=dep)

    # 2. Check self-cycles immediately
    for task_id, deps in plan.items():
        if task_id in deps:
            raise CycleDetectedError(cycle_path=[task_id, task_id])

    # 3. Topological sort using Kahn's algorithm
    # In dependency planning:
    # If B depends on A, A must finish before B can start.
    # So an edge goes from A -> B (A unlocks B).
    # In-degree of task T = number of unfulfilled dependencies T is waiting on.
    in_degree: Dict[str, int] = {task_id: len(deps) for task_id, deps in plan.items()}
    dependents: Dict[str, List[str]] = {task_id: [] for task_id in plan}

    for task_id, deps in plan.items():
        for dep in deps:
            dependents[dep].append(task_id)

    # Tasks with in_degree == 0 have all dependencies satisfied and can run immediately
    ready_queue: List[str] = sorted([t for t, deg in in_degree.items() if deg == 0])
    ordered_tasks: List[str] = []

    while ready_queue:
        current = ready_queue.pop(0)
        ordered_tasks.append(current)

        for dep_task in sorted(dependents[current]):
            in_degree[dep_task] -= 1
            if in_degree[dep_task] == 0:
                ready_queue.append(dep_task)
                ready_queue.sort()  # Maintain deterministic tie-breaking

    # If ordered_tasks does not include every task, there is a cycle
    if len(ordered_tasks) < len(plan):
        cycle = _find_cycle(plan)
        if not cycle:
            # Fallback if specific cycle path not isolated
            remaining = [t for t in plan if t not in ordered_tasks]
            cycle = remaining + [remaining[0]]
        raise CycleDetectedError(cycle_path=cycle)

    return ordered_tasks


def simulate_agent_execution(plan: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Simulates multi-agent execution following validated topological order.

    Validates dependencies, catches any issues before runtime, and returns
    a sequential execution audit trace.
    """
    order = validate_and_order_plan(plan)
    executed_trace: List[Dict[str, str]] = []

    for task_id in order:
        executed_trace.append({
            "task_id": task_id,
            "status": "COMPLETED",
            "dependencies_satisfied": str(plan.get(task_id, []))
        })

    return executed_trace


# Applied Scenario Questions for Lesson Validation
APPLIED_QUESTIONS = {
    "question_1": {
        "prompt": "Given canonical plan {A: [], B: [A], C: [B]}, what is the topological execution order?",
        "expected_output": ["A", "B", "C"],
        "check": lambda: validate_and_order_plan(CANONICAL_PLAN) == ["A", "B", "C"]
    },
    "question_2": {
        "prompt": "Given plan {A: [B], B: [A]}, what error is raised to reject circular deadlocks?",
        "expected_error": "CycleDetectedError",
        "check": lambda: _check_cycle_rejected({"A": ["B"], "B": ["A"]})
    },
    "question_3": {
        "prompt": "Given plan {B: [UNKNOWN_TASK]}, what error and missing task ID are reported?",
        "expected_error": "MissingDependencyError",
        "expected_missing_id": "UNKNOWN_TASK",
        "check": lambda: _check_missing_dep_reported({"B": ["UNKNOWN_TASK"]}, "UNKNOWN_TASK")
    }
}


def _check_cycle_rejected(plan: Dict[str, List[str]]) -> bool:
    try:
        validate_and_order_plan(plan)
        return False
    except CycleDetectedError:
        return True
    except Exception:
        return False


def _check_missing_dep_reported(plan: Dict[str, List[str]], expected_missing_id: str) -> bool:
    try:
        validate_and_order_plan(plan)
        return False
    except MissingDependencyError as err:
        return err.missing_dep_id == expected_missing_id and expected_missing_id in str(err)
    except Exception:
        return False


def main():
    print("=== Multi-Agent Dependency-Plan Validation & Ordering (R17-T041) ===\n")

    # 1. Canonical Plan
    print("1. Canonical Scenario:")
    print(f"   Plan: {CANONICAL_PLAN}")
    canonical_order = validate_and_order_plan(CANONICAL_PLAN)
    print(f"   Topological Order: {canonical_order}")
    execution_trace = simulate_agent_execution(CANONICAL_PLAN)
    print(f"   Execution Trace: {[e['task_id'] for e in execution_trace]}\n")

    # 2. Boundary Cases
    print("2. Boundary Cases:")
    print(f"   Empty plan {{}} -> {validate_and_order_plan({})}")
    print(f"   Single task {{'A': []}} -> {validate_and_order_plan({'A': []})}")
    print(f"   Independent tasks {{'B': [], 'A': []}} -> {validate_and_order_plan({'B': [], 'A': []})}\n")

    # 3. Missing Dependency Case
    print("3. Missing Dependency Scenario:")
    try:
        invalid_plan = {"B": ["UNKNOWN_X"]}
        print(f"   Validating plan: {invalid_plan}")
        validate_and_order_plan(invalid_plan)
    except MissingDependencyError as err:
        print(f"   Caught Expected Error: {err}\n")

    # 4. Cycle Detection Scenario
    print("4. Circular Dependency Scenario:")
    try:
        cyclic_plan = {"A": ["B"], "B": ["A"]}
        print(f"   Validating plan: {cyclic_plan}")
        validate_and_order_plan(cyclic_plan)
    except CycleDetectedError as err:
        print(f"   Caught Expected Error: {err}\n")

    print("All demonstrations executed successfully.")


if __name__ == "__main__":
    main()
