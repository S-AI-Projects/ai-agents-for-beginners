#!/usr/bin/env python3
"""Unit tests for Bounded Agent Loop — Offline Service Adapter (R17-T015)."""

import unittest

from example import (
    ActionRecord,
    AdapterBoundedAgent,
    AgentLoopResult,
    AgentServiceAdapter,
    LocalDeterministicAdapter,
)


class MockRecordingAdapter(AgentServiceAdapter):
    """Spy adapter to assert exact call counts and parameters."""

    def __init__(self) -> None:
        self.calls = []

    def execute_inspect(self, step: int) -> str:
        self.calls.append(("inspect", step))
        return f"spy_inspect_{step}"

    def execute_answer(self, step: int) -> str:
        self.calls.append(("answer", step))
        return f"spy_answer_{step}"

    def execute_stop(self, step: int) -> str:
        self.calls.append(("stop", step))
        return f"spy_stop_{step}"


class TestAdapterBoundedAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = LocalDeterministicAdapter()
        self.agent = AdapterBoundedAgent(adapter=self.adapter, step_budget=3)

    def test_canonical_plan_terminates_normally(self) -> None:
        plan = ["inspect", "answer", "stop"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "terminated_normally")
        self.assertEqual(result.total_steps, 3)
        actions = [r.action for r in result.trace]
        self.assertEqual(actions, ["inspect", "answer", "stop"])

    def test_endless_plan_halts_at_budget(self) -> None:
        plan = ["inspect", "inspect", "inspect", "inspect"]
        result = self.agent.run(plan)
        self.assertEqual(result.status, "budget_exceeded")
        self.assertEqual(result.total_steps, 3)
        self.assertEqual(len(result.trace), 3)

    def test_no_tool_called_after_stop(self) -> None:
        spy = MockRecordingAdapter()
        agent = AdapterBoundedAgent(adapter=spy, step_budget=3)
        plan = ["inspect", "stop", "answer"]
        result = agent.run(plan)
        self.assertEqual(result.status, "terminated_normally")
        self.assertEqual(result.total_steps, 2)
        # Verify spy records: only inspect and stop were called; answer was never invoked
        invoked_actions = [call[0] for call in spy.calls]
        self.assertEqual(invoked_actions, ["inspect", "stop"])
        self.assertNotIn("answer", invoked_actions)

    def test_deliberate_wrong_status_fails(self) -> None:
        """Deliberate check that abnormal plan does not report terminated_normally."""
        plan = ["inspect", "inspect", "inspect"]
        result = self.agent.run(plan)
        self.assertNotEqual(result.status, "terminated_normally")
        self.assertEqual(result.status, "budget_exceeded")


if __name__ == "__main__":
    unittest.main()
