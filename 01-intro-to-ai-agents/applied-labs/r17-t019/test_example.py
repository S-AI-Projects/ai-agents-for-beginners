#!/usr/bin/env python3
"""Unit tests for Bounded Agent Loop — Evaluation Experiment (R17-T019)."""

import unittest

from example import ExperimentAgent, run_budget_experiment


class TestBoundedAgentEvaluation(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ExperimentAgent(step_budget=3)

    def test_actions_terminate_normally(self) -> None:
        plan = ["inspect", "answer", "stop"]
        res = self.agent.execute_plan(plan)
        self.assertEqual(res.status, "terminated_normally")
        self.assertEqual(res.executed_steps, 3)
        self.assertEqual([item.action for item in res.trace], ["inspect", "answer", "stop"])

    def test_endless_plan_stops_at_three_steps(self) -> None:
        plan = ["inspect"] * 10
        res = self.agent.execute_plan(plan)
        self.assertEqual(res.status, "budget_exceeded")
        self.assertEqual(res.executed_steps, 3)

    def test_no_tool_called_after_stop(self) -> None:
        plan = ["inspect", "stop", "answer"]
        res = self.agent.execute_plan(plan)
        self.assertEqual(res.status, "terminated_normally")
        self.assertEqual(res.executed_steps, 2)
        actions = [item.action for item in res.trace]
        self.assertEqual(actions, ["inspect", "stop"])
        self.assertNotIn("answer", actions)

    def test_evaluation_experiment_across_three_configurations(self) -> None:
        """Compare 3 controlled configurations (budgets 2, 3, 5) without real-world model claims."""
        summaries = run_budget_experiment()
        self.assertEqual(set(summaries.keys()), {2, 3, 5})

        # Config 1: Budget 2 fails to complete 3-step canonical task
        self.assertFalse(summaries[2].canonical_completion)
        self.assertEqual(summaries[2].endless_halt_step, 2)

        # Config 2: Budget 3 successfully completes 3-step canonical task
        self.assertTrue(summaries[3].canonical_completion)
        self.assertEqual(summaries[3].endless_halt_step, 3)

        # Config 3: Budget 5 completes canonical task but allows endless loop to run to 5
        self.assertTrue(summaries[5].canonical_completion)
        self.assertEqual(summaries[5].endless_halt_step, 5)


if __name__ == "__main__":
    unittest.main()
