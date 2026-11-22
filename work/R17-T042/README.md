# Verification Evidence: R17-T042 (GitHub Issue #43)

## Overview

- **Task Identifier**: R17-T042
- **Issue**: GitHub Issue #43
- **Branch**: `NirmalAdhau/e26b07f2790/R17-T042`
- **Lesson**: `08-multi-agent`
- **Topic**: Comparative Topological Sorting — Kahn's Algorithm vs DFS Post-Order with Reverse

---

## Contract Compliance Matrix

| Requirement | Contract Specification | Implementation Status | Evidence / Verification Test |
| :--- | :--- | :--- | :--- |
| **Topological Sort (Kahn)** | In-degree BFS queue ordering with deterministic alphabetical tie-breaking | PASS | `test_canonical_ordering_kahn_and_dfs` |
| **Topological Sort (DFS)** | DFS post-order traversal with reverse and deterministic tie-breaking | PASS | `test_canonical_ordering_kahn_and_dfs` |
| **Direct Cycle Rejection** | $A \leftrightarrow B$ circular dependency raises `CycleDetectedError` in both | PASS | `test_cycle_direct_a_b_a_rejected` |
| **Self-Dependency Rejection** | $A \to A$ self-loop raises `CycleDetectedError` in both | PASS | `test_cycle_self_dependency_rejected` |
| **Indirect Cycle Rejection** | Multi-hop $A \to B \to C \to A$ raises `CycleDetectedError` in both | PASS | `test_cycle_indirect_triangle_rejected` |
| **Missing Dependency Diagnosis** | Unknown dependency raises `MissingDependencyError` surfacing missing ID in both | PASS | `test_missing_dependency_reported_by_task_id` |
| **Boundary: Empty Plan** | `{}` returns `[]` in both without error | PASS | `test_empty_plan_boundary` |
| **Boundary: Single Task** | `{"A": []}` returns `["A"]` in both | PASS | `test_single_task_boundary` |
| **Boundary: Parallel Tasks** | Independent tasks break ties alphabetically (`{"B": [], "A": []}` $\to$ `["A", "B"]`) | PASS | `test_independent_tasks_deterministic_order` |
| **Boundary: Diamond DAG** | Diamond graph ($A \to B, C \to D$) orders prerequisites before sink in both | PASS | `test_diamond_dag_equivalence` |
| **Multi-Branch Pipeline** | Demonstrates BFS level-order (Kahn) vs DFS branch-order with strict topological validity | PASS | `test_multi_branch_pipeline_equivalence` |
| **Execution Simulation** | Step-by-step trace simulation supports both scheduling methods | PASS | `test_unified_wrapper_and_execution_simulation` |

---

## Test Execution Verification

Command:
```bash
python3 -m unittest discover -s 08-multi-agent/applied-labs/r17-t042 -p "test_*.py" -v
```

Execution Output:
```text
test_canonical_ordering_kahn_and_dfs (test_example.TestComparativeTopologicalSorting.test_canonical_ordering_kahn_and_dfs)
Canonical plan A -> B -> C orders deterministically as ['A', 'B', 'C'] in both. ... ok
test_comparative_helper_matches_errors (test_example.TestComparativeTopologicalSorting.test_comparative_helper_matches_errors)
compare_algorithms helper detects matching errors on invalid fixtures. ... ok
test_cycle_direct_a_b_a_rejected (test_example.TestComparativeTopologicalSorting.test_cycle_direct_a_b_a_rejected)
Direct cycle A -> B -> A raises CycleDetectedError in both algorithms. ... ok
test_cycle_indirect_triangle_rejected (test_example.TestComparativeTopologicalSorting.test_cycle_indirect_triangle_rejected)
Indirect cycle A -> B -> C -> A raises CycleDetectedError in both algorithms. ... ok
test_cycle_self_dependency_rejected (test_example.TestComparativeTopologicalSorting.test_cycle_self_dependency_rejected)
Self-dependency A -> A raises CycleDetectedError in both algorithms. ... ok
test_diamond_dag_equivalence (test_example.TestComparativeTopologicalSorting.test_diamond_dag_equivalence)
Diamond DAG produces valid topological ordering with prerequisites preceding sink in both. ... ok
test_empty_plan_boundary (test_example.TestComparativeTopologicalSorting.test_empty_plan_boundary)
Empty plan {} returns empty list [] in both algorithms. ... ok
test_independent_tasks_deterministic_order (test_example.TestComparativeTopologicalSorting.test_independent_tasks_deterministic_order)
Independent tasks {'B': [], 'A': []} order alphabetically as ['A', 'B'] in both. ... ok
test_missing_dependency_reported_by_task_id (test_example.TestComparativeTopologicalSorting.test_missing_dependency_reported_by_task_id)
Unknown dependency raises MissingDependencyError with matching task ID in both. ... ok
test_multi_branch_pipeline_equivalence (test_example.TestComparativeTopologicalSorting.test_multi_branch_pipeline_equivalence)
Multi-branch pipeline produces valid topological orders in both algorithms. ... ok
test_single_task_boundary (test_example.TestComparativeTopologicalSorting.test_single_task_boundary)
Single task {'A': []} returns ['A'] in both algorithms. ... ok
test_unified_wrapper_and_execution_simulation (test_example.TestComparativeTopologicalSorting.test_unified_wrapper_and_execution_simulation)
validate_and_order_plan wrapper and execution simulation work for both methods. ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
```

---

## Example Script Execution Output

Command:
```bash
python3 08-multi-agent/applied-labs/r17-t042/example.py
```

Execution Output:
```text
=== Multi-Agent Comparative Topological Sorting (R17-T042) ===

--- Canonical Linear Plan ---
  Plan: {'A': [], 'B': ['A'], 'C': ['B']}
  Kahn's Order : ['A', 'B', 'C'] (Valid: True)
  DFS Order    : ['A', 'B', 'C'] (Valid: True)
  Identical    : True

--- Diamond DAG ---
  Plan: {'A': [], 'B': ['A'], 'C': ['A'], 'D': ['B', 'C']}
  Kahn's Order : ['A', 'B', 'C', 'D'] (Valid: True)
  DFS Order    : ['A', 'B', 'C', 'D'] (Valid: True)
  Identical    : True

--- Independent Parallel Tasks ---
  Plan: {'B': [], 'A': []}
  Kahn's Order : ['A', 'B'] (Valid: True)
  DFS Order    : ['A', 'B'] (Valid: True)
  Identical    : True

--- Multi-Branch Pipeline ---
  Plan: {'START': [], 'DATA_A': ['START'], 'DATA_B': ['START'], 'PROCESS_A': ['DATA_A'], 'PROCESS_B': ['DATA_B'], 'JOIN': ['PROCESS_A', 'PROCESS_B'], 'REPORT': ['JOIN']}
  Kahn's Order : ['START', 'DATA_A', 'DATA_B', 'PROCESS_A', 'PROCESS_B', 'JOIN', 'REPORT'] (Valid: True)
  DFS Order    : ['START', 'DATA_A', 'PROCESS_A', 'DATA_B', 'PROCESS_B', 'JOIN', 'REPORT'] (Valid: True)
  Identical    : False

--- Error Handling Comparison ---
1. Cycle Detection (A <-> B):
   Errors matched between Kahn and DFS: True
2. Missing Dependency (Task1 -> NON_EXISTENT):
   Errors matched between Kahn and DFS: True

All comparative demonstrations executed successfully.
```
