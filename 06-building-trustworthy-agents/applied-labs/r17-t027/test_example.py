"""Unit tests for Allowlisted Action Policy — Worked Example with Checks.

Lesson 06: Building Trustworthy AI Agents
Task: R17-T027
Automated check: python3 -m unittest discover -s 06-building-trustworthy-agents/applied-labs/r17-t027 -p "test_*.py" -v
"""

import unittest

from example import (
    AllowedActionPolicy,
    ArgumentValidationError,
    DisallowedToolError,
    GuardedActionDispatcher,
    PolicyViolationError,
    StubExecutor,
    ToolCall,
    WORKED_EXPLANATIONS,
)


class TestAllowedToolPasses(unittest.TestCase):
    """Verify that authorized tools with valid schema arguments execute through the stub."""

    def setUp(self) -> None:
        self.policy = AllowedActionPolicy()
        self.executor = StubExecutor()
        self.dispatcher = GuardedActionDispatcher(self.policy, self.executor)

    def test_allowed_read_with_valid_path_passes(self) -> None:
        """Allowed 'read' with valid 'path' executes successfully."""
        call = ToolCall(tool_name="read", arguments={"path": "/var/log/system.log"})
        result = self.dispatcher.dispatch(call)

        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "read")
        self.assertEqual(len(self.executor.executed_calls), 1)
        self.assertEqual(self.executor.executed_calls[0].arguments["path"], "/var/log/system.log")


class TestDisallowedToolRejected(unittest.TestCase):
    """Verify that unallowlisted tools are blocked before reaching the stub executor."""

    def setUp(self) -> None:
        self.policy = AllowedActionPolicy()
        self.executor = StubExecutor()
        self.dispatcher = GuardedActionDispatcher(self.policy, self.executor)

    def test_unknown_delete_tool_is_rejected(self) -> None:
        """Unknown 'delete' tool raises DisallowedToolError without executing."""
        call = ToolCall(tool_name="delete", arguments={"path": "/tmp/test.txt"})

        with self.assertRaises(DisallowedToolError) as ctx:
            self.dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.attempted_tool, "delete")
        self.assertIn("read", ctx.exception.allowed_tools)

        # Invariant: Stub executor must NOT be reached
        self.assertEqual(len(self.executor.executed_calls), 0)
        self.assertEqual(len(self.dispatcher.rejection_log), 1)


class TestMissingRequiredArgumentRejected(unittest.TestCase):
    """Verify that calls missing required parameters fail prior to execution."""

    def setUp(self) -> None:
        self.policy = AllowedActionPolicy()
        self.executor = StubExecutor()
        self.dispatcher = GuardedActionDispatcher(self.policy, self.executor)

    def test_missing_path_argument_is_rejected(self) -> None:
        """Calling 'read' without 'path' raises ArgumentValidationError."""
        call = ToolCall(tool_name="read", arguments={})

        with self.assertRaises(ArgumentValidationError) as ctx:
            self.dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.tool_name, "read")
        self.assertIn("Missing required parameter", ctx.exception.message)

        # Invariant: Stub executor must NOT be reached
        self.assertEqual(len(self.executor.executed_calls), 0)


class TestRegressionOnExactWorkedExamples(unittest.TestCase):
    """Execute the exact worked example catalog as an automated regression test."""

    def setUp(self) -> None:
        self.policy = AllowedActionPolicy()
        self.executor = StubExecutor()
        self.dispatcher = GuardedActionDispatcher(self.policy, self.executor)

    def test_regression_all_worked_cases(self) -> None:
        """All cataloged input-to-output examples must match their stated outcome."""
        for case in WORKED_EXPLANATIONS:
            call = ToolCall(case["input"]["tool_name"], case["input"]["arguments"])
            initial_count = len(self.executor.executed_calls)

            if case["executor_reached"]:
                result = self.dispatcher.dispatch(call)
                self.assertTrue(result.success)
                self.assertEqual(len(self.executor.executed_calls), initial_count + 1)
            else:
                with self.assertRaises(PolicyViolationError):
                    self.dispatcher.dispatch(call)
                # Invariant: Stub executor call count must not increase on rejected actions
                self.assertEqual(len(self.executor.executed_calls), initial_count)


class TestBoundaryConditions(unittest.TestCase):
    """Verify boundary conditions and invalid argument types."""

    def setUp(self) -> None:
        self.policy = AllowedActionPolicy()
        self.executor = StubExecutor()
        self.dispatcher = GuardedActionDispatcher(self.policy, self.executor)

    def test_whitespace_path_rejected(self) -> None:
        """Empty or whitespace-only paths are rejected."""
        call = ToolCall(tool_name="read", arguments={"path": "   "})
        with self.assertRaises(ArgumentValidationError):
            self.dispatcher.dispatch(call)
        self.assertEqual(len(self.executor.executed_calls), 0)

    def test_non_string_path_rejected(self) -> None:
        """Non-string path types (e.g. int) are rejected."""
        call = ToolCall(tool_name="read", arguments={"path": 12345})
        with self.assertRaises(ArgumentValidationError):
            self.dispatcher.dispatch(call)
        self.assertEqual(len(self.executor.executed_calls), 0)


if __name__ == "__main__":
    unittest.main()
