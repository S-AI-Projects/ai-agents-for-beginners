#!/usr/bin/env python3
"""Tests for Typed Tool Dispatch — Runnable Concept Example (R17-T011)."""

import json
import unittest

from example import ToolDispatcher, ToolResult


class TestTypedToolDispatch(unittest.TestCase):
    def setUp(self) -> None:
        self.dispatcher = ToolDispatcher()

    def test_add_success(self) -> None:
        call = {"tool": "add", "args": {"a": 2, "b": 3}}
        result = self.dispatcher.dispatch(call)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.result, 5)
        self.assertEqual(result.tool, "add")

    def test_multiply_success(self) -> None:
        call = {"tool": "multiply", "args": {"a": 2, "b": 3}}
        result = self.dispatcher.dispatch(call)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.result, 6)
        self.assertEqual(result.tool, "multiply")

    def test_json_string_input_parsing(self) -> None:
        raw_json = json.dumps({"tool": "add", "args": {"a": 10, "b": 25}})
        result = self.dispatcher.dispatch(raw_json)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.result, 35)

    def test_invalid_json_string(self) -> None:
        result = self.dispatcher.dispatch("not valid json{")
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, "INVALID_JSON")

    def test_unknown_tool_structured_error(self) -> None:
        call = {"tool": "divide", "args": {"a": 10, "b": 2}}
        result = self.dispatcher.dispatch(call)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, "UNKNOWN_TOOL")
        self.assertIn("not in the allowlist", result.message)

    def test_string_argument_a_structured_error(self) -> None:
        call = {"tool": "add", "args": {"a": "2", "b": 3}}
        result = self.dispatcher.dispatch(call)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, "TYPE_ERROR")
        self.assertIn("Argument 'a' must be numeric", result.message)

    def test_string_argument_b_structured_error(self) -> None:
        call = {"tool": "multiply", "args": {"a": 2, "b": "3"}}
        result = self.dispatcher.dispatch(call)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, "TYPE_ERROR")
        self.assertIn("Argument 'b' must be numeric", result.message)

    def test_missing_argument(self) -> None:
        call = {"tool": "add", "args": {"a": 2}}
        result = self.dispatcher.dispatch(call)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, "MISSING_REQUIRED_ARGUMENTS")

    def test_sequence_aborts_on_failed_call(self) -> None:
        calls = [
            {"tool": "add", "args": {"a": 2, "b": 3}},        # Valid -> 5
            {"tool": "subtract", "args": {"a": 5, "b": 1}},   # Invalid tool -> error
            {"tool": "multiply", "args": {"a": 2, "b": 3}},   # Must NOT execute
        ]
        results = self.dispatcher.dispatch_sequence(calls)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, "success")
        self.assertEqual(results[0].result, 5)
        self.assertEqual(results[1].status, "error")
        self.assertEqual(results[1].error_code, "UNKNOWN_TOOL")

    def test_float_arguments_supported(self) -> None:
        call = {"tool": "add", "args": {"a": 2.5, "b": 3.5}}
        result = self.dispatcher.dispatch(call)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.result, 6.0)


if __name__ == "__main__":
    unittest.main()
