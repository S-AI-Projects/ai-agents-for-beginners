"""Automated Unit Tests for Dependency-Plan Validation & Ordering (R17-T041)

Lesson Alignment:
08-multi-agent (Multi-agent design patterns)

Contract Checks:
1. Canonical scenario: A has no dependencies, B depends on A, C on B -> order A, B, C.
2. Cycle detection: A -> B -> A is rejected with CycleDetectedError.
3. Missing dependency: Unknown dependency is detected and reported by task ID with MissingDependencyError.
4. Boundary cases: Empty plan, single task, independent parallel tasks, diamond dependencies.
5. Applied scenario checks from APPLIED_QUESTIONS.
"""

import unittest
try:
    from example import (
        CANONICAL_PLAN,
        validate_and_order_plan,
        simulate_agent_execution,
        MissingDependencyError,
        CycleDetectedError,
        APPLIED_QUESTIONS,
    )
except ImportError:
    from .example import (
        CANONICAL_PLAN,
        validate_and_order_plan,
        simulate_agent_execution,
        MissingDependencyError,
        CycleDetectedError,
        APPLIED_QUESTIONS,
    )


class TestDependencyPlanValidation(unittest.TestCase):
    """Unit test suite for multi-agent dependency plan validation and execution."""

    def test_canonical_ordering(self):
        """A has no dependencies, B depends on A, C on B: order must be ['A', 'B', 'C']."""
        result = validate_and_order_plan(CANONICAL_PLAN)
        self.assertEqual(result, ["A", "B", "C"])

    def test_empty_plan_boundary(self):
        """Boundary case: empty plan returns empty order without error."""
        result = validate_and_order_plan({})
        self.assertEqual(result, [])

    def test_single_task_boundary(self):
        """Boundary case: single task with no dependencies returns [task]."""
        result = validate_and_order_plan({"A": []})
        self.assertEqual(result, ["A"])

    def test_independent_tasks_deterministic_order(self):
        """Multiple tasks with no dependencies execute in deterministic alphabetical order."""
        plan = {"C": [], "A": [], "B": []}
        result = validate_and_order_plan(plan)
        self.assertEqual(result, ["A", "B", "C"])

    def test_diamond_dependency_graph(self):
        """A has no deps; B and C depend on A; D depends on B and C."""
        plan = {
            "A": [],
            "B": ["A"],
            "C": ["A"],
            "D": ["B", "C"],
        }
        result = validate_and_order_plan(plan)
        self.assertEqual(result, ["A", "B", "C", "D"])
        # Invariants: A must precede B and C; B and C must precede D
        self.assertLess(result.index("A"), result.index("B"))
        self.assertLess(result.index("A"), result.index("C"))
        self.assertLess(result.index("B"), result.index("D"))
        self.assertLess(result.index("C"), result.index("D"))

    def test_missing_dependency_reported_by_task_id(self):
        """Unknown dependency is reported explicitly by task ID."""
        plan = {"task_init": [], "task_process": ["NON_EXISTENT_DEP"]}
        with self.assertRaises(MissingDependencyError) as ctx:
            validate_and_order_plan(plan)

        self.assertEqual(ctx.exception.task_id, "task_process")
        self.assertEqual(ctx.exception.missing_dep_id, "NON_EXISTENT_DEP")
        self.assertIn("NON_EXISTENT_DEP", str(ctx.exception))
        self.assertIn("task_process", str(ctx.exception))

    def test_cycle_direct_a_b_a_rejected(self):
        """A depends on B, B depends on A: rejected with CycleDetectedError."""
        plan = {"A": ["B"], "B": ["A"]}
        with self.assertRaises(CycleDetectedError) as ctx:
            validate_and_order_plan(plan)
        self.assertTrue(len(ctx.exception.cycle_path) >= 2)

    def test_cycle_self_dependency_rejected(self):
        """A task depending directly on itself (A -> A) is rejected with CycleDetectedError."""
        plan = {"A": ["A"]}
        with self.assertRaises(CycleDetectedError):
            validate_and_order_plan(plan)

    def test_cycle_indirect_triangle_rejected(self):
        """Indirect circular dependency A -> B -> C -> A is rejected."""
        plan = {
            "A": ["C"],
            "B": ["A"],
            "C": ["B"],
        }
        with self.assertRaises(CycleDetectedError):
            validate_and_order_plan(plan)

    def test_simulated_execution_trace(self):
        """Simulated execution proceeds in validated topological order."""
        plan = {"A": [], "B": ["A"], "C": ["B"]}
        trace = simulate_agent_execution(plan)
        ordered_ids = [entry["task_id"] for entry in trace]
        self.assertEqual(ordered_ids, ["A", "B", "C"])
        self.assertTrue(all(entry["status"] == "COMPLETED" for entry in trace))

    def test_applied_questions_all_pass(self):
        """Executable checks for applied lesson questions all evaluate to True."""
        for q_id, q_data in APPLIED_QUESTIONS.items():
            with self.subTest(question=q_id):
                self.assertTrue(q_data["check"](), f"Check failed for {q_id}")


if __name__ == "__main__":
    unittest.main()
