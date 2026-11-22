"""Applied Lab: Comparative Topological Sorting — Kahn's Algorithm vs DFS Post-Order (R17-T042)

Lesson Alignment:
08-multi-agent (Multi-agent design patterns)

Contract & Goals:
- Validate and topologically sort multi-agent task plans.
- Reject cycles (e.g., A -> B -> A, self-dependencies, multi-hop loops) with CycleDetectedError.
- Detect missing / unknown dependencies before scheduling with MissingDependencyError reporting the missing task ID.
- Comparative analysis: Implement Kahn's algorithm (in-degree queue) alongside DFS post-order traversal with reverse.
- Demonstrate equivalence in topological validity, deterministic tie-breaking, and cycle/missing dependency handling.
- Zero external dependencies: pure Python 3 standard library.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Any
import sys


class PlanValidationError(Exception):
    """Base exception for task plan validation errors."""
    pass


class MissingDependencyError(PlanValidationError):
    """Raised when a task declares a dependency on an unknown/unregistered task ID."""

    def __init__(self, task_id: str, missing_dep_id: str):
        self.task_id = task_id
        self.missing_dep_id = missing_dep_id
        super().__init__(
            f"Task '{task_id}' references unknown dependency '{missing_dep_id}'. "
            f"Dependency task ID '{missing_dep_id}' was not found in the plan catalog."
        )


class CycleDetectedError(PlanValidationError):
    """Raised when circular dependencies exist among tasks in the plan."""

    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        path_str = " -> ".join(cycle_path) if cycle_path else "unknown cycle"
        super().__init__(
            f"Circular dependency detected in plan: {path_str}. "
            "Execution rejected to prevent infinite multi-agent deadlock."
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
    "A": [],        # Task A: Independent initial task
    "B": ["A"],     # Task B: Depends on A
    "C": ["B"],     # Task C: Depends on B
}

DIAMOND_PLAN: Dict[str, List[str]] = {
    "A": [],
    "B": ["A"],
    "C": ["A"],
    "D": ["B", "C"],
}

INDEPENDENT_PLAN: Dict[str, List[str]] = {
    "B": [],
    "A": [],
}

MULTI_BRANCH_PLAN: Dict[str, List[str]] = {
    "START": [],
    "DATA_A": ["START"],
    "DATA_B": ["START"],
    "PROCESS_A": ["DATA_A"],
    "PROCESS_B": ["DATA_B"],
    "JOIN": ["PROCESS_A", "PROCESS_B"],
    "REPORT": ["JOIN"],
}


def validate_dependencies(plan: Dict[str, List[str]]) -> None:
    """Verifies that all referenced dependencies exist as registered task keys.

    Raises:
        MissingDependencyError: If any task declares a dependency on a non-existent task.
    """
    for task_id in sorted(plan.keys()):
        for dep in plan[task_id]:
            if dep not in plan:
                raise MissingDependencyError(task_id=task_id, missing_dep_id=dep)


def _reconstruct_cycle(plan: Dict[str, List[str]]) -> List[str]:
    """Helper to detect and reconstruct a cycle path in a directed dependency graph."""
    state: Dict[str, int] = {k: 0 for k in plan}  # 0=unvisited, 1=visiting, 2=visited
    cycle_nodes: List[str] = []

    def dfs(node: str, stack: List[str]) -> bool:
        state[node] = 1
        stack.append(node)
        for dep in sorted(plan.get(node, [])):
            if dep not in plan:
                continue
            if state[dep] == 1:
                start_idx = stack.index(dep)
                cycle_nodes.extend(stack[start_idx:])
                cycle_nodes.append(dep)
                return True
            elif state[dep] == 0:
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


def validate_and_order_kahn(plan: Dict[str, List[str]]) -> List[str]:
    """Topologically sorts tasks using Kahn's algorithm (in-degree BFS queue).

    Approach:
    1. Compute in-degree (number of unfulfilled prerequisites) for each task.
    2. Maintain dependent adjacency list (dep -> list of tasks waiting on dep).
    3. Initialize a ready queue of tasks with in-degree 0, sorted alphabetically
       for deterministic tie-breaking.
    4. Repeatedly pop the lowest alphabetical task, append to sorted order, and
       decrement in-degrees of dependent tasks. Add any newly unblocked tasks to queue.
    5. If sorted order contains fewer tasks than total tasks, a cycle exists.

    Raises:
        MissingDependencyError: If an unknown dependency is referenced.
        CycleDetectedError: If a circular dependency exists.
    """
    if not plan:
        return []

    validate_dependencies(plan)

    # Check immediate self-dependency
    for task_id, deps in plan.items():
        if task_id in deps:
            raise CycleDetectedError(cycle_path=[task_id, task_id])

    in_degree: Dict[str, int] = {task_id: len(deps) for task_id, deps in plan.items()}
    dependents: Dict[str, List[str]] = {task_id: [] for task_id in plan}

    for task_id, deps in plan.items():
        for dep in deps:
            dependents[dep].append(task_id)

    # Ready queue with deterministic alphabetical tie-breaking
    ready_queue: List[str] = sorted([t for t, deg in in_degree.items() if deg == 0])
    ordered_tasks: List[str] = []

    while ready_queue:
        current = ready_queue.pop(0)
        ordered_tasks.append(current)

        for dep_task in sorted(dependents[current]):
            in_degree[dep_task] -= 1
            if in_degree[dep_task] == 0:
                ready_queue.append(dep_task)
                ready_queue.sort()

    if len(ordered_tasks) < len(plan):
        cycle = _reconstruct_cycle(plan)
        if not cycle:
            remaining = [t for t in sorted(plan.keys()) if t not in ordered_tasks]
            cycle = remaining + [remaining[0]]
        raise CycleDetectedError(cycle_path=cycle)

    return ordered_tasks


def validate_and_order_dfs(plan: Dict[str, List[str]]) -> List[str]:
    """Topologically sorts tasks using DFS post-order traversal with reverse.

    Approach:
    1. Invert dependencies into forward execution edges:
       If Task B depends on Task A, edge is A -> B (A unlocks B).
    2. Track node state during traversal: 0=unvisited, 1=visiting, 2=visited.
    3. If an edge leads to a node currently in state 1 (visiting), a back-edge
       (cycle) has been detected; reconstruct the cycle path and raise CycleDetectedError.
    4. Explore neighbors in reverse alphabetical order so that when the post-order list
       is reversed at the end, tasks with equal rank maintain alphabetical order.
    5. Reverse the post-order list to produce the topological execution schedule.

    Raises:
        MissingDependencyError: If an unknown dependency is referenced.
        CycleDetectedError: If a circular dependency exists.
    """
    if not plan:
        return []

    validate_dependencies(plan)

    # Check immediate self-dependency
    for task_id, deps in plan.items():
        if task_id in deps:
            raise CycleDetectedError(cycle_path=[task_id, task_id])

    # Build forward execution graph: prerequisite -> list of dependent tasks
    dependents: Dict[str, List[str]] = {task_id: [] for task_id in plan}
    for task_id, deps in plan.items():
        for dep in deps:
            dependents[dep].append(task_id)

    # State: 0 = unvisited, 1 = visiting (recursion stack), 2 = visited
    state: Dict[str, int] = {k: 0 for k in plan}
    post_order: List[str] = []
    recursion_stack: List[str] = []

    def dfs(node: str) -> None:
        state[node] = 1
        recursion_stack.append(node)

        # Explore neighbors in reverse alphabetical order for deterministic tie-breaking
        for next_task in sorted(dependents[node], reverse=True):
            if state[next_task] == 1:
                # Cycle detected via back-edge
                start_idx = recursion_stack.index(next_task)
                cycle_path = recursion_stack[start_idx:] + [next_task]
                raise CycleDetectedError(cycle_path=cycle_path)
            elif state[next_task] == 0:
                dfs(next_task)

        recursion_stack.pop()
        state[node] = 2
        post_order.append(node)

    # Visit top-level nodes in reverse alphabetical order
    for root_node in sorted(plan.keys(), reverse=True):
        if state[root_node] == 0:
            dfs(root_node)

    # Reverse post-order produces topological order
    return list(reversed(post_order))


def validate_and_order_plan(plan: Dict[str, List[str]], method: str = "kahn") -> List[str]:
    """Unified entry point to validate and order a plan using the chosen algorithm.

    Args:
        plan: Mapping of task_id -> list of dependency task IDs.
        method: 'kahn' for in-degree BFS queue, 'dfs' for DFS post-order reverse.

    Returns:
        Topologically sorted list of task IDs.
    """
    if method == "kahn":
        return validate_and_order_kahn(plan)
    elif method == "dfs":
        return validate_and_order_dfs(plan)
    else:
        raise ValueError(f"Unknown ordering method: '{method}'. Choose 'kahn' or 'dfs'.")


def is_valid_topological_order(plan: Dict[str, List[str]], order: List[str]) -> bool:
    """Verifies that an execution order is a mathematically valid topological sort.

    Invariants checked:
    1. Every task in `plan` appears exactly once in `order`.
    2. For every task, all of its declared dependencies appear BEFORE the task in `order`.
    """
    if len(order) != len(plan):
        return False
    if set(order) != set(plan.keys()):
        return False

    position: Dict[str, int] = {task_id: idx for idx, task_id in enumerate(order)}
    for task_id, deps in plan.items():
        task_pos = position[task_id]
        for dep in deps:
            if position[dep] >= task_pos:
                return False
    return True


def compare_algorithms(plan: Dict[str, List[str]]) -> Dict[str, Any]:
    """Compares Kahn's algorithm and DFS post-order reverse on a given plan fixture.

    Returns:
        Dictionary detailing results from both algorithms, validity, and equivalence.
    """
    result: Dict[str, Any] = {
        "kahn_order": None,
        "dfs_order": None,
        "kahn_valid": False,
        "dfs_valid": False,
        "identical_order": False,
        "error_matched": False,
    }

    kahn_err: Optional[Exception] = None
    dfs_err: Optional[Exception] = None

    try:
        result["kahn_order"] = validate_and_order_kahn(plan)
        result["kahn_valid"] = is_valid_topological_order(plan, result["kahn_order"])
    except Exception as err:
        kahn_err = err

    try:
        result["dfs_order"] = validate_and_order_dfs(plan)
        result["dfs_valid"] = is_valid_topological_order(plan, result["dfs_order"])
    except Exception as err:
        dfs_err = err

    if kahn_err and dfs_err:
        result["error_matched"] = type(kahn_err) is type(dfs_err)
    elif result["kahn_order"] is not None and result["dfs_order"] is not None:
        result["identical_order"] = (result["kahn_order"] == result["dfs_order"])

    return result


def simulate_agent_execution(plan: Dict[str, List[str]], method: str = "kahn") -> List[Dict[str, str]]:
    """Simulates multi-agent task execution following validated topological order."""
    order = validate_and_order_plan(plan, method=method)
    trace: List[Dict[str, str]] = []

    for task_id in order:
        trace.append({
            "task_id": task_id,
            "status": "COMPLETED",
            "method": method,
            "dependencies": str(plan.get(task_id, [])),
        })

    return trace


def main():
    print("=== Multi-Agent Comparative Topological Sorting (R17-T042) ===\n")

    fixtures = [
        ("Canonical Linear Plan", CANONICAL_PLAN),
        ("Diamond DAG", DIAMOND_PLAN),
        ("Independent Parallel Tasks", INDEPENDENT_PLAN),
        ("Multi-Branch Pipeline", MULTI_BRANCH_PLAN),
    ]

    for name, fixture in fixtures:
        print(f"--- {name} ---")
        comparison = compare_algorithms(fixture)
        print(f"  Plan: {fixture}")
        print(f"  Kahn's Order : {comparison['kahn_order']} (Valid: {comparison['kahn_valid']})")
        print(f"  DFS Order    : {comparison['dfs_order']} (Valid: {comparison['dfs_valid']})")
        print(f"  Identical    : {comparison['identical_order']}\n")

    # Error handling demonstrations
    print("--- Error Handling Comparison ---")
    cyclic_plan = {"A": ["B"], "B": ["A"]}
    missing_plan = {"Task1": ["NON_EXISTENT"]}

    print("1. Cycle Detection (A <-> B):")
    comp_cycle = compare_algorithms(cyclic_plan)
    print(f"   Errors matched between Kahn and DFS: {comp_cycle['error_matched']}")

    print("2. Missing Dependency (Task1 -> NON_EXISTENT):")
    comp_missing = compare_algorithms(missing_plan)
    print(f"   Errors matched between Kahn and DFS: {comp_missing['error_matched']}")

    print("\nAll comparative demonstrations executed successfully.")


if __name__ == "__main__":
    main()
