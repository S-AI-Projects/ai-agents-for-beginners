#!/usr/bin/env python3
"""Unit tests for Bounded Agent Loop — Boundary-Case Lesson Extension (R17-T012)."""

import unittest

from example import BoundedAgent, AgentRunResult


class TestBoundedAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = BoundedAgent(step_budget=3)

    def test_canonical_actions_terminate_normally(self) -> None:
        plan = ["inspect", "answer", "stop"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "terminated_normally")
        self.assertEqual(result.total_steps, 3)
        actions = [record.action for record in result.trace]
        self.assertEqual(actions, ["inspect", "answer", "stop"])

    def test_endless_plan_stops_at_budget(self) -> None:
        plan = ["inspect", "inspect", "inspect", "inspect", "inspect"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "budget_exceeded")
        self.assertEqual(result.total_steps, 3)
        self.assertEqual(len(result.trace), 3)

    def test_no_tool_called_after_stop(self) -> None:
        plan = ["inspect", "stop", "answer"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "terminated_normally")
        self.assertEqual(result.total_steps, 2)
        actions = [record.action for record in result.trace]
        self.assertEqual(actions, ["inspect", "stop"])
        self.assertNotIn("answer", actions)

    def test_minimal_plan_immediate_stop(self) -> None:
        plan = ["stop"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "terminated_normally")
        self.assertEqual(result.total_steps, 1)

    def test_two_step_plan_without_stop(self) -> None:
        plan = ["inspect", "answer"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "terminated_normally")
        self.assertEqual(result.total_steps, 2)

    def test_three_step_plan_without_stop_exceeds_budget(self) -> None:
        plan = ["inspect", "inspect", "answer"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "budget_exceeded")
        self.assertEqual(result.total_steps, 3)

    def test_unknown_action_handled_safely(self) -> None:
        plan = ["inspect", "unknown_tool", "stop"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.trace[-1].status, "error")


if __name__ == "__main__":
    unittest.main()
