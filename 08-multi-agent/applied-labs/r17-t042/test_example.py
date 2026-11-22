"""Automated Unit Tests for Comparative Topological Sorting (R17-T042)

Lesson Alignment:
08-multi-agent (Multi-agent design patterns)

Contract Checks:
1. Canonical scenario: A has no dependencies, B depends on A, C on B -> order A, B, C.
2. Comparative parity: Kahn's algorithm and DFS post-order with reverse yield equivalent valid topological orderings.
3. Cycle detection: Direct (A -> B -> A), self (A -> A), and indirect cycles are rejected with CycleDetectedError in both.
4. Missing dependency: Unknown dependency is detected and reported by task ID with MissingDependencyError in both.
5. Boundary cases: Empty plan, single task, independent parallel tasks, diamond DAG, and multi-branch pipelines.
"""

import unittest
try:
    from example import (
        CANONICAL_PLAN,
        DIAMOND_PLAN,
        INDEPENDENT_PLAN,
        MULTI_BRANCH_PLAN,
        validate_and_order_kahn,
        validate_and_order_dfs,
        validate_and_order_plan,
        is_valid_topological_order,
        compare_algorithms,
        simulate_agent_execution,
        MissingDependencyError,
        CycleDetectedError,
    )
except ImportError:
    from .example import (
        CANONICAL_PLAN,
        DIAMOND_PLAN,
        INDEPENDENT_PLAN,
        MULTI_BRANCH_PLAN,
        validate_and_order_kahn,
        validate_and_order_dfs,
        validate_and_order_plan,
        is_valid_topological_order,
        compare_algorithms,
        simulate_agent_execution,
        MissingDependencyError,
        CycleDetectedError,
    )


class TestComparativeTopologicalSorting(unittest.TestCase):
    """Unit test suite verifying Kahn's algorithm and DFS post-order comparative behavior."""

    def test_canonical_ordering_kahn_and_dfs(self):
        """Canonical plan A -> B -> C orders deterministically as ['A', 'B', 'C'] in both."""
        order_kahn = validate_and_order_kahn(CANONICAL_PLAN)
        order_dfs = validate_and_order_dfs(CANONICAL_PLAN)

        self.assertEqual(order_kahn, ["A", "B", "C"])
        self.assertEqual(order_dfs, ["A", "B", "C"])
        self.assertEqual(order_kahn, order_dfs)
        self.assertTrue(is_valid_topological_order(CANONICAL_PLAN, order_kahn))
        self.assertTrue(is_valid_topological_order(CANONICAL_PLAN, order_dfs))

    def test_empty_plan_boundary(self):
        """Empty plan {} returns empty list [] in both algorithms."""
        self.assertEqual(validate_and_order_kahn({}), [])
        self.assertEqual(validate_and_order_dfs({}), [])

    def test_single_task_boundary(self):
        """Single task {'A': []} returns ['A'] in both algorithms."""
        self.assertEqual(validate_and_order_kahn({"A": []}), ["A"])
        self.assertEqual(validate_and_order_dfs({"A": []}), ["A"])

    def test_independent_tasks_deterministic_order(self):
        """Independent tasks {'B': [], 'A': []} order alphabetically as ['A', 'B'] in both."""
        order_kahn = validate_and_order_kahn(INDEPENDENT_PLAN)
        order_dfs = validate_and_order_dfs(INDEPENDENT_PLAN)

        self.assertEqual(order_kahn, ["A", "B"])
        self.assertEqual(order_dfs, ["A", "B"])
        self.assertEqual(order_kahn, order_dfs)

    def test_diamond_dag_equivalence(self):
        """Diamond DAG produces valid topological ordering with prerequisites preceding sink in both."""
        order_kahn = validate_and_order_kahn(DIAMOND_PLAN)
        order_dfs = validate_and_order_dfs(DIAMOND_PLAN)

        self.assertEqual(order_kahn, ["A", "B", "C", "D"])
        self.assertEqual(order_dfs, ["A", "B", "C", "D"])
        self.assertTrue(is_valid_topological_order(DIAMOND_PLAN, order_kahn))
        self.assertTrue(is_valid_topological_order(DIAMOND_PLAN, order_dfs))

        # Invariant checks: A must precede B and C; B and C must precede D
        for order in [order_kahn, order_dfs]:
            self.assertLess(order.index("A"), order.index("B"))
            self.assertLess(order.index("A"), order.index("C"))
            self.assertLess(order.index("B"), order.index("D"))
            self.assertLess(order.index("C"), order.index("D"))

    def test_multi_branch_pipeline_equivalence(self):
        """Multi-branch pipeline produces valid topological orders in both algorithms.
        
        Kahn's yields BFS level-by-level ordering, while DFS yields branch-first ordering.
        Both satisfy all dependency precedence constraints.
        """
        comparison = compare_algorithms(MULTI_BRANCH_PLAN)
        self.assertTrue(comparison["kahn_valid"])
        self.assertTrue(comparison["dfs_valid"])

        # Both must strictly satisfy topological invariants
        for order in [comparison["kahn_order"], comparison["dfs_order"]]:
            self.assertLess(order.index("START"), order.index("DATA_A"))
            self.assertLess(order.index("START"), order.index("DATA_B"))
            self.assertLess(order.index("DATA_A"), order.index("PROCESS_A"))
            self.assertLess(order.index("DATA_B"), order.index("PROCESS_B"))
            self.assertLess(order.index("PROCESS_A"), order.index("JOIN"))
            self.assertLess(order.index("PROCESS_B"), order.index("JOIN"))
            self.assertLess(order.index("JOIN"), order.index("REPORT"))

    def test_missing_dependency_reported_by_task_id(self):
        """Unknown dependency raises MissingDependencyError with matching task ID in both."""
        plan = {"task_init": [], "task_process": ["UNKNOWN_DEP"]}

        for method, fn in [("kahn", validate_and_order_kahn), ("dfs", validate_and_order_dfs)]:
            with self.subTest(method=method):
                with self.assertRaises(MissingDependencyError) as ctx:
                    fn(plan)
                self.assertEqual(ctx.exception.task_id, "task_process")
                self.assertEqual(ctx.exception.missing_dep_id, "UNKNOWN_DEP")
                self.assertIn("UNKNOWN_DEP", str(ctx.exception))
                self.assertIn("task_process", str(ctx.exception))

    def test_cycle_direct_a_b_a_rejected(self):
        """Direct cycle A -> B -> A raises CycleDetectedError in both algorithms."""
        plan = {"A": ["B"], "B": ["A"]}

        for method, fn in [("kahn", validate_and_order_kahn), ("dfs", validate_and_order_dfs)]:
            with self.subTest(method=method):
                with self.assertRaises(CycleDetectedError) as ctx:
                    fn(plan)
                self.assertTrue(len(ctx.exception.cycle_path) >= 2)

    def test_cycle_self_dependency_rejected(self):
        """Self-dependency A -> A raises CycleDetectedError in both algorithms."""
        plan = {"A": ["A"]}

        for method, fn in [("kahn", validate_and_order_kahn), ("dfs", validate_and_order_dfs)]:
            with self.subTest(method=method):
                with self.assertRaises(CycleDetectedError):
                    fn(plan)

    def test_cycle_indirect_triangle_rejected(self):
        """Indirect cycle A -> B -> C -> A raises CycleDetectedError in both algorithms."""
        plan = {"A": ["C"], "B": ["A"], "C": ["B"]}

        for method, fn in [("kahn", validate_and_order_kahn), ("dfs", validate_and_order_dfs)]:
            with self.subTest(method=method):
                with self.assertRaises(CycleDetectedError):
                    fn(plan)

    def test_comparative_helper_matches_errors(self):
        """compare_algorithms helper detects matching errors on invalid fixtures."""
        cyclic_plan = {"A": ["B"], "B": ["A"]}
        missing_plan = {"B": ["NON_EXISTENT"]}

        comp_cycle = compare_algorithms(cyclic_plan)
        self.assertTrue(comp_cycle["error_matched"])
        self.assertFalse(comp_cycle["kahn_valid"])
        self.assertFalse(comp_cycle["dfs_valid"])

        comp_missing = compare_algorithms(missing_plan)
        self.assertTrue(comp_missing["error_matched"])

    def test_unified_wrapper_and_execution_simulation(self):
        """validate_and_order_plan wrapper and execution simulation work for both methods."""
        for method in ["kahn", "dfs"]:
            with self.subTest(method=method):
                order = validate_and_order_plan(CANONICAL_PLAN, method=method)
                self.assertEqual(order, ["A", "B", "C"])

                trace = simulate_agent_execution(CANONICAL_PLAN, method=method)
                self.assertEqual([t["task_id"] for t in trace], ["A", "B", "C"])
                self.assertTrue(all(t["status"] == "COMPLETED" for t in trace))
                self.assertTrue(all(t["method"] == method for t in trace))

        with self.assertRaises(ValueError):
            validate_and_order_plan(CANONICAL_PLAN, method="invalid_method")


if __name__ == "__main__":
    unittest.main()
