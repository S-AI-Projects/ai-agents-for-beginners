"""Unit tests for Deterministic Typed Tool Dispatch.

Lesson 04: Tool Use Design Pattern
Task: R17-T022
Automated check: python3 -m unittest discover -s 04-tool-use/applied-labs/r17-t022 -p "test_*.py" -v
"""

from __future__ import annotations

import unittest

from example import (
    ToolArgumentError,
    ToolCall,
    ToolDispatchError,
    ToolDispatcher,
    ToolExecutionBlockedError,
    ToolResult,
    UnknownToolError,
    add_tool,
    multiply_tool,
)


class TestHappyPath(unittest.TestCase):
    """Verifies standard valid execution paths and expected outputs."""

    def setUp(self) -> None:
        self.dispatcher = ToolDispatcher()

    def test_add_integers_returns_sum(self) -> None:
        """add(2, 3) must return 5 with success=True."""
        call = ToolCall(name="add", arguments={"a": 2, "b": 3}, call_id="add_01")
        res = self.dispatcher.dispatch(call)

        self.assertIsInstance(res, ToolResult)
        self.assertTrue(res.success)
        self.assertEqual(res.result, 5)
        self.assertEqual(res.tool_name, "add")
        self.assertEqual(res.call_id, "add_01")
        self.assertIsNone(res.error)
        self.assertEqual(len(self.dispatcher.execution_history), 1)

    def test_multiply_integers_returns_product(self) -> None:
        """multiply(2, 3) must return 6 with success=True."""
        call = ToolCall(name="multiply", arguments={"a": 2, "b": 3}, call_id="mult_01")
        res = self.dispatcher.dispatch(call)

        self.assertIsInstance(res, ToolResult)
        self.assertTrue(res.success)
        self.assertEqual(res.result, 6)
        self.assertEqual(res.tool_name, "multiply")
        self.assertEqual(res.call_id, "mult_01")
        self.assertIsNone(res.error)
        self.assertEqual(len(self.dispatcher.execution_history), 1)

    def test_floating_point_operations(self) -> None:
        """Tool dispatcher must correctly handle valid floating-point numbers."""
        res_add = self.dispatcher.dispatch(
            ToolCall(name="add", arguments={"a": 1.5, "b": 2.5})
        )
        self.assertEqual(res_add.result, 4.0)

        res_mult = self.dispatcher.dispatch(
            ToolCall(name="multiply", arguments={"a": 2.5, "b": 4.0})
        )
        self.assertEqual(res_mult.result, 10.0)

    def test_valid_json_dispatch(self) -> None:
        """dispatch_json with valid JSON payload executes and records result."""
        raw_json = '{"name": "add", "arguments": {"a": 20, "b": 22}, "call_id": "json_01"}'
        res = self.dispatcher.dispatch_json(raw_json)

        self.assertTrue(res.success)
        self.assertEqual(res.result, 42)
        self.assertEqual(res.call_id, "json_01")

        # Also supports dict payload
        dict_payload = {"name": "multiply", "arguments": {"a": 3, "b": 7}}
        res_dict = self.dispatcher.dispatch_json(dict_payload)
        self.assertTrue(res_dict.success)
        self.assertEqual(res_dict.result, 21)

    def test_valid_sequence_execution(self) -> None:
        """execute_sequence runs all valid calls in order and returns results."""
        calls = [
            ToolCall(name="add", arguments={"a": 1, "b": 2}),
            ToolCall(name="multiply", arguments={"a": 3, "b": 4}),
            ToolCall(name="add", arguments={"a": 10, "b": 20}),
        ]
        results = self.dispatcher.execute_sequence(calls)

        self.assertEqual(len(results), 3)
        self.assertEqual([r.result for r in results], [3, 12, 30])
        self.assertEqual(len(self.dispatcher.execution_history), 3)
        self.assertFalse(self.dispatcher.is_blocked)


class TestRejectionGuardPath(unittest.TestCase):
    """Verifies schema validation and allowlist rejections with diagnostic exceptions."""

    def setUp(self) -> None:
        self.dispatcher = ToolDispatcher()

    def test_unknown_tool_raises_unknown_tool_error(self) -> None:
        """Attempting to invoke an unlisted tool must raise UnknownToolError."""
        call = ToolCall(name="divide", arguments={"a": 10, "b": 2})

        with self.assertRaises(UnknownToolError) as ctx:
            self.dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.tool_name, "divide")
        self.assertIn("add", ctx.exception.allowed_tools)
        self.assertIn("multiply", ctx.exception.allowed_tools)
        self.assertIn("Allowed tools", str(ctx.exception))

    def test_string_argument_raises_tool_argument_error(self) -> None:
        """Passing string '2' instead of numeric 2 must be strictly rejected without coercion."""
        call = ToolCall(name="add", arguments={"a": "2", "b": 3})

        with self.assertRaises(ToolArgumentError) as ctx:
            self.dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.tool_name, "add")
        self.assertEqual(ctx.exception.param_name, "a")
        self.assertEqual(ctx.exception.received_value, "2")
        self.assertEqual(ctx.exception.expected_type, "int | float")
        self.assertIn("must be numeric", str(ctx.exception))

    def test_missing_argument_raises_tool_argument_error(self) -> None:
        """Omitting required argument 'b' must raise ToolArgumentError."""
        call = ToolCall(name="multiply", arguments={"a": 5})

        with self.assertRaises(ToolArgumentError) as ctx:
            self.dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.tool_name, "multiply")
        self.assertEqual(ctx.exception.param_name, "b")
        self.assertIn("Missing required parameter", str(ctx.exception))

    def test_boolean_argument_strictly_rejected(self) -> None:
        """Booleans (subclass of int in Python) must be explicitly rejected with ToolArgumentError."""
        call = ToolCall(name="add", arguments={"a": True, "b": 3})

        with self.assertRaises(ToolArgumentError) as ctx:
            self.dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.tool_name, "add")
        self.assertEqual(ctx.exception.param_name, "a")
        self.assertIs(ctx.exception.received_value, True)
        self.assertIn("bool", str(ctx.exception))

    def test_unexpected_extra_arguments_rejected(self) -> None:
        """Extra unexpected arguments must be rejected."""
        call = ToolCall(name="add", arguments={"a": 2, "b": 3, "c": 4})

        with self.assertRaises(ToolArgumentError) as ctx:
            self.dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.tool_name, "add")
        self.assertEqual(ctx.exception.param_name, "c")
        self.assertIn("Unexpected parameters", str(ctx.exception))

    def test_malformed_json_raises_tool_argument_error(self) -> None:
        """Malformed JSON strings must raise ToolArgumentError."""
        bad_json = '{"name": "add", "arguments": broken_json}'

        with self.assertRaises(ToolArgumentError):
            self.dispatcher.dispatch_json(bad_json)


class TestStateInvariants(unittest.TestCase):
    """Verifies pre-execution failure immutability and post-failure containment."""

    def setUp(self) -> None:
        self.dispatcher = ToolDispatcher()

    def test_session_state_unmutated_upon_rejection(self) -> None:
        """Failed calls must not alter execution history or record successful steps."""
        # Initial state
        self.assertEqual(len(self.dispatcher.execution_history), 0)
        self.assertFalse(self.dispatcher.is_blocked)

        # Attempt invalid call (string argument)
        bad_call = ToolCall(name="add", arguments={"a": "invalid", "b": 5})
        with self.assertRaises(ToolArgumentError):
            self.dispatcher.dispatch(bad_call)

        # Invariant: execution_history must remain empty
        self.assertEqual(len(self.dispatcher.execution_history), 0)
        # Failure containment: dispatcher is now blocked
        self.assertTrue(self.dispatcher.is_blocked)
        self.assertIsNotNone(self.dispatcher.block_reason)

    def test_prior_history_preserved_upon_subsequent_failure(self) -> None:
        """Prior successful executions remain in history; failing call does not append."""
        # Step 1: Valid execution
        res1 = self.dispatcher.dispatch(ToolCall(name="add", arguments={"a": 2, "b": 3}))
        self.assertEqual(len(self.dispatcher.execution_history), 1)
        self.assertEqual(self.dispatcher.execution_history[0].result, 5)

        # Step 2: Attempt unknown tool
        with self.assertRaises(UnknownToolError):
            self.dispatcher.dispatch(ToolCall(name="subtract", arguments={"a": 5, "b": 2}))

        # Invariant: History still contains exactly the 1 prior success, not modified
        self.assertEqual(len(self.dispatcher.execution_history), 1)
        self.assertEqual(self.dispatcher.execution_history[0].result, 5)
        self.assertTrue(self.dispatcher.is_blocked)

    def test_failed_call_blocks_subsequent_executions(self) -> None:
        """Enforces invariant: a failed call cannot execute another tool."""
        # Fail the dispatcher with an invalid call
        with self.assertRaises(ToolArgumentError):
            self.dispatcher.dispatch(ToolCall(name="multiply", arguments={"a": "bad", "b": 2}))

        self.assertTrue(self.dispatcher.is_blocked)

        # Any subsequent call (even a perfectly valid one) must be blocked
        valid_call = ToolCall(name="add", arguments={"a": 2, "b": 3})
        with self.assertRaises(ToolExecutionBlockedError) as ctx:
            self.dispatcher.dispatch(valid_call)

        self.assertEqual(ctx.exception.attempted_tool, "add")
        self.assertIn("session is blocked due to prior failure", str(ctx.exception))
        # History is still 0
        self.assertEqual(len(self.dispatcher.execution_history), 0)

    def test_sequence_halts_at_first_failure(self) -> None:
        """Sequence execution halts at first failure; subsequent tools are not executed."""
        calls = [
            ToolCall(name="add", arguments={"a": 2, "b": 3}),          # Call 1: Valid -> 5
            ToolCall(name="multiply", arguments={"a": "bad", "b": 3}),  # Call 2: Invalid -> Fails
            ToolCall(name="add", arguments={"a": 10, "b": 20}),        # Call 3: Never executed
        ]

        with self.assertRaises(ToolArgumentError):
            self.dispatcher.execute_sequence(calls)

        # Invariant: Exactly 1 call executed in history
        self.assertEqual(len(self.dispatcher.execution_history), 1)
        self.assertEqual(self.dispatcher.execution_history[0].result, 5)
        self.assertTrue(self.dispatcher.is_blocked)

        # Additional call directly via dispatch must also be blocked
        with self.assertRaises(ToolExecutionBlockedError):
            self.dispatcher.dispatch(ToolCall(name="add", arguments={"a": 1, "b": 1}))


class TestBoundaryConditions(unittest.TestCase):
    """Verifies edge cases, zero operands, negative values, and precision limits."""

    def setUp(self) -> None:
        self.dispatcher = ToolDispatcher()

    def test_zero_operands(self) -> None:
        """Zeros as operands and products must compute accurately."""
        res_add = self.dispatcher.dispatch(ToolCall(name="add", arguments={"a": 0, "b": 0}))
        self.assertEqual(res_add.result, 0)

        res_mult = self.dispatcher.dispatch(ToolCall(name="multiply", arguments={"a": 0, "b": 5}))
        self.assertEqual(res_mult.result, 0)

    def test_negative_operands(self) -> None:
        """Negative integers and signed products must compute accurately."""
        res_add = self.dispatcher.dispatch(ToolCall(name="add", arguments={"a": -10, "b": 4}))
        self.assertEqual(res_add.result, -6)

        res_mult = self.dispatcher.dispatch(ToolCall(name="multiply", arguments={"a": -3, "b": -7}))
        self.assertEqual(res_mult.result, 21)

    def test_floating_point_precision(self) -> None:
        """Mixed float arithmetic handles signed decimals without truncation."""
        res = self.dispatcher.dispatch(ToolCall(name="add", arguments={"a": -2.5, "b": 3.5}))
        self.assertEqual(res.result, 1.0)

        res_mult = self.dispatcher.dispatch(ToolCall(name="multiply", arguments={"a": -2.5, "b": 2.0}))
        self.assertEqual(res_mult.result, -5.0)

    def test_large_integers(self) -> None:
        """Arbitrary-precision large integers must compute without overflow."""
        large_a = 10**18
        large_b = 10**18
        res_add = self.dispatcher.dispatch(ToolCall(name="add", arguments={"a": large_a, "b": large_b}))
        self.assertEqual(res_add.result, 2 * 10**18)

        res_mult = self.dispatcher.dispatch(ToolCall(name="multiply", arguments={"a": 10**9, "b": 10**9}))
        self.assertEqual(res_mult.result, 10**18)

    def test_empty_allowlist_boundary(self) -> None:
        """Dispatcher configured with empty allowlist rejects all tool calls."""
        empty_dispatcher = ToolDispatcher(allowed_tools=set())
        call = ToolCall(name="add", arguments={"a": 2, "b": 3})

        with self.assertRaises(UnknownToolError) as ctx:
            empty_dispatcher.dispatch(call)

        self.assertEqual(ctx.exception.allowed_tools, set())
        self.assertTrue(empty_dispatcher.is_blocked)


if __name__ == "__main__":
    unittest.main()
