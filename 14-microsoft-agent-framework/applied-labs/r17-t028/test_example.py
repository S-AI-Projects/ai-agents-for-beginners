#!/usr/bin/env python3
"""Unit tests for Bounded Agent Loop Fixture (Task R17-T028).

Verifies loop bounds, termination invariants, action tracing, stop guards, and
error explanation and recovery mechanics.
"""

import unittest
from typing import Dict, Any

from example import (
    ActionTraceRecord,
    ActionType,
    AgentLoopResult,
    BoundedAgentFixture,
    ExecutionHaltedError,
    LoopStatus,
)


class TestBoundedAgentLoopHappyPath(unittest.TestCase):
    """Happy path validation for normal sequential execution."""

    def setUp(self) -> None:
        self.fixture = BoundedAgentFixture(max_steps=3)

    def test_normal_lifecycle_terminates_normally(self) -> None:
        """Actions [inspect, answer, stop] must terminate normally with completed status."""
        plan = [
            ("inspect", {"target": "doc_101"}),
            ("answer", {"text": "Step limits are required for production safety."}),
            ("stop", {}),
        ]
        result = self.fixture.run_plan(plan)

        self.assertEqual(result.status, LoopStatus.COMPLETED)
        self.assertEqual(result.steps_executed, 3)
        self.assertTrue(result.is_stopped)
        self.assertEqual(result.final_answer, "Step limits are required for production safety.")
        self.assertIsNone(result.error_summary)

        # Validate sequential trace order
        self.assertEqual(len(result.trace), 3)
        self.assertEqual(result.trace[0].action, "inspect")
        self.assertEqual(result.trace[0].status, "success")
        self.assertIn("Agent Orchestration Guidelines", str(result.trace[0].result))

        self.assertEqual(result.trace[1].action, "answer")
        self.assertEqual(result.trace[1].status, "success")

        self.assertEqual(result.trace[2].action, "stop")
        self.assertEqual(result.trace[2].status, "stopped")

    def test_trace_contains_all_required_metadata(self) -> None:
        """Trace records must include step numbers, timestamps, status, and payload."""
        plan = [("inspect", {"target": "doc_102"}), ("stop", {})]
        result = self.fixture.run_plan(plan)

        record = result.trace[0]
        self.assertIsInstance(record, ActionTraceRecord)
        self.assertEqual(record.step_number, 1)
        self.assertEqual(record.action, "inspect")
        self.assertEqual(record.status, "success")
        self.assertIsNotNone(record.timestamp)
        self.assertIn("Telemetry and Observability", record.result["title"])


class TestBoundedAgentLoopGuardsAndRejection(unittest.TestCase):
    """Guard enforcement: stop guarantee and disallowed actions."""

    def setUp(self) -> None:
        self.fixture = BoundedAgentFixture(max_steps=3)

    def test_no_tool_called_after_stop(self) -> None:
        """In a plan containing actions after stop, subsequent actions are never called."""
        plan = [
            ("inspect", {"target": "doc_101"}),
            ("stop", {}),
            ("answer", {"text": "This action must never execute."}),
            ("inspect", {"target": "doc_102"}),
        ]
        result = self.fixture.run_plan(plan)

        self.assertEqual(result.status, LoopStatus.COMPLETED)
        self.assertEqual(result.steps_executed, 2)
        self.assertTrue(result.is_stopped)
        self.assertIsNone(result.final_answer)

        # Actions after 'stop' must not appear in trace
        recorded_actions = [t.action for t in result.trace]
        self.assertEqual(recorded_actions, ["inspect", "stop"])
        self.assertNotIn("answer", recorded_actions)

    def test_direct_execute_step_after_stop_raises_error(self) -> None:
        """Direct invocation of execute_step on a stopped fixture raises ExecutionHaltedError."""
        self.fixture.execute_step("stop", {})
        self.assertTrue(self.fixture.is_stopped)

        with self.assertRaises(ExecutionHaltedError) as ctx:
            self.fixture.execute_step("inspect", {"target": "doc_101"})

        self.assertIn("Agent has already stopped", str(ctx.exception))

    def test_unsupported_action_recorded_as_error(self) -> None:
        """Dispatching an unsupported action token records an explicit error in trace."""
        self.fixture.execute_step("delete_database", {})
        self.assertEqual(len(self.fixture.trace), 1)
        record = self.fixture.trace[0]
        self.assertEqual(record.status, "error")
        self.assertEqual(record.error_code, "UNSUPPORTED_ACTION")


class TestBoundedAgentLoopBudgetInvariants(unittest.TestCase):
    """Budget limits and state invariants."""

    def setUp(self) -> None:
        self.fixture = BoundedAgentFixture(max_steps=3)

    def test_endless_plan_stops_at_budget(self) -> None:
        """An endless plan stops at three steps with budget_exceeded."""
        endless_plan = [
            ("inspect", {"target": "doc_101"}),
            ("inspect", {"target": "doc_101"}),
            ("inspect", {"target": "doc_101"}),
            ("inspect", {"target": "doc_101"}),
            ("inspect", {"target": "doc_101"}),
        ]
        result = self.fixture.run_plan(endless_plan)

        self.assertEqual(result.status, LoopStatus.BUDGET_EXCEEDED)
        self.assertEqual(result.steps_executed, 3)
        self.assertEqual(result.max_steps, 3)
        self.assertFalse(result.is_stopped)
        self.assertEqual(len(result.trace), 3)
        self.assertIn("reached maximum step budget", result.error_summary or "")

    def test_reset_clears_state(self) -> None:
        """Reset clears step counter, trace records, and stopped flag."""
        self.fixture.run_plan([("stop", {})])
        self.assertTrue(self.fixture.is_stopped)

        self.fixture.reset()
        self.assertEqual(self.fixture.current_step, 0)
        self.assertFalse(self.fixture.is_stopped)
        self.assertEqual(len(self.fixture.trace), 0)
        self.assertIsNone(self.fixture.final_answer)


class TestFailureAndRecoveryMechanics(unittest.TestCase):
    """Core focus: invalid/missing-data error explanation and recovery."""

    def setUp(self) -> None:
        self.fixture = BoundedAgentFixture(max_steps=3)

    def test_missing_data_explains_error_clearly(self) -> None:
        """Nonexistent target records an explicit MISSING_DATA error with diagnostic explanation."""
        plan = [("inspect", {"target": "unknown_entity_404"})]
        result = self.fixture.run_plan(plan)

        record = result.trace[0]
        self.assertEqual(record.status, "error")
        self.assertEqual(record.error_code, "MISSING_DATA")
        self.assertIn("unknown_entity_404", record.error_message)
        self.assertIsNotNone(record.explanation)
        self.assertIn("Remediation", record.explanation)

    def test_empty_target_payload_explains_error_clearly(self) -> None:
        """Missing or whitespace target field records MISSING_DATA error with guidance."""
        plan = [("inspect", {"target": "   "})]
        result = self.fixture.run_plan(plan)

        record = result.trace[0]
        self.assertEqual(record.status, "error")
        self.assertEqual(record.error_code, "MISSING_DATA")
        self.assertIn("required field 'target'", record.error_message)

    def test_recovery_on_subsequent_valid_input(self) -> None:
        """Demonstrates recovery: step 1 fails on invalid input, step 2 succeeds on valid input, step 3 stops."""
        recovery_plan = [
            ("inspect", {"target": "nonexistent_key"}),  # Fails with missing data
            ("inspect", {"target": "doc_102"}),          # Recovers with valid target
            ("stop", {}),                                 # Terminates cleanly
        ]
        result = self.fixture.run_plan(recovery_plan)

        self.assertEqual(result.status, LoopStatus.COMPLETED)
        self.assertEqual(result.steps_executed, 3)
        self.assertTrue(result.is_stopped)

        # Step 1 was an error with explanation
        self.assertEqual(result.trace[0].status, "error")
        self.assertEqual(result.trace[0].error_code, "MISSING_DATA")
        self.assertIn("nonexistent_key", result.trace[0].error_message)

        # Step 2 recovered successfully
        self.assertEqual(result.trace[1].status, "success")
        self.assertIn("Telemetry and Observability", result.trace[1].result["title"])

        # Step 3 stopped
        self.assertEqual(result.trace[2].status, "stopped")

    def test_multi_turn_invocation_recovery(self) -> None:
        """Demonstrates multi-turn recovery: first invocation fails, second invocation succeeds."""
        # Run 1: Invalid input payload
        fail_plan = [("inspect", {"target": "invalid_doc"}), ("stop", {})]
        res1 = self.fixture.run_plan(fail_plan)
        self.assertEqual(res1.trace[0].status, "error")

        # Run 2: Corrected input parameters
        success_plan = [
            ("inspect", {"target": "doc_101"}),
            ("answer", {"text": "Recovered successfully with valid input."}),
            ("stop", {}),
        ]
        res2 = self.fixture.run_plan(success_plan)
        self.assertEqual(res2.status, LoopStatus.COMPLETED)
        self.assertEqual(res2.trace[0].status, "success")
        self.assertEqual(res2.final_answer, "Recovered successfully with valid input.")


if __name__ == "__main__":
    unittest.main()
