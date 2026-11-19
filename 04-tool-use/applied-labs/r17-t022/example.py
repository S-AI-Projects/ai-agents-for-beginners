"""Deterministic Typed Tool Dispatch - Applied Lab Example.

Lesson 04: Tool Use Design Pattern
Task: R17-T022

This module provides a deterministic local simulation fixture implementing
typed tool dispatching, explicit allowlisting, strict argument validation,
and failure containment invariants for AI agents.

Key Guarantees:
1. Explicit Tool Allowlist: Only approved tools ("add", "multiply") may execute.
2. Strict Numeric Validation: Operands must be numeric (int/float), explicitly
   rejecting booleans (which subclass int in Python) and non-numeric strings.
3. Pre-Execution State Invariance: If validation fails, execution history and
   session state remain completely unmutated.
4. Failure Containment: A failed call locks the dispatcher; subsequent tool
   calls are blocked with ToolExecutionBlockedError.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any, Dict, List, Optional, Sequence, Set, Union
import urllib.parse


class ToolDispatchError(Exception):
    """Base exception for all tool dispatch and execution errors."""


class UnknownToolError(ToolDispatchError):
    """Raised when an agent attempts to invoke a tool outside the allowlist."""

    def __init__(self, tool_name: str, allowed_tools: Set[str]) -> None:
        self.tool_name = tool_name
        self.allowed_tools = allowed_tools
        message = (
            f"Unknown tool '{tool_name}'. "
            f"Allowed tools: {sorted(allowed_tools)}"
        )
        super().__init__(message)


class ToolArgumentError(ToolDispatchError):
    """Raised when input arguments fail schema or type validation."""

    def __init__(
        self,
        tool_name: str,
        param_name: str,
        received_value: Any,
        expected_type: str,
        message: str = "",
    ) -> None:
        self.tool_name = tool_name
        self.param_name = param_name
        self.received_value = received_value
        self.expected_type = expected_type
        if not message:
            message = (
                f"Invalid argument for tool '{tool_name}': parameter '{param_name}' "
                f"must be {expected_type}, got {type(received_value).__name__} ({received_value!r})."
            )
        super().__init__(message)


class ToolExecutionBlockedError(ToolDispatchError):
    """Raised when an execution is attempted on a dispatcher locked by a prior failure."""

    def __init__(self, attempted_tool: str, reason: str) -> None:
        self.attempted_tool = attempted_tool
        self.reason = reason
        message = (
            f"Cannot execute tool '{attempted_tool}': session is blocked due to prior failure "
            f"('{reason}'). A failed call cannot execute another tool."
        )
        super().__init__(message)


@dataclass(frozen=True)
class ToolCall:
    """Represents an incoming tool invocation request."""

    name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


@dataclass(frozen=True)
class ToolResult:
    """Represents the structured outcome of a tool execution."""

    call_id: Optional[str]
    tool_name: str
    success: bool
    result: Optional[Union[int, float]] = None
    error: Optional[str] = None


def add_tool(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Pure arithmetic addition primitive."""
    return a + b


def multiply_tool(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Pure arithmetic multiplication primitive."""
    return a * b


class ToolDispatcher:
    """Deterministic local tool dispatcher enforcing allowlisting, validation, and failure containment."""

    DEFAULT_ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(self, allowed_tools: Optional[Set[str]] = None) -> None:
        self.allowed_tools: Set[str] = (
            set(allowed_tools) if allowed_tools is not None else set(self.DEFAULT_ALLOWED_TOOLS)
        )
        self.is_blocked: bool = False
        self.block_reason: Optional[str] = None
        self.execution_history: List[ToolResult] = []

    def _latch_block(self, reason: str) -> None:
        """Lock the session so subsequent calls are prevented from executing."""
        self.is_blocked = True
        self.block_reason = reason

    def validate_call(self, call: ToolCall) -> None:
        """Validate call against session block state, allowlist, and argument schemas.

        Raises:
            ToolExecutionBlockedError: If dispatcher is already locked by a prior failure.
            UnknownToolError: If tool name is not in the allowlist.
            ToolArgumentError: If arguments are missing, extraneous, or non-numeric (including bools).
        """
        # 1. State Invariant Check: Latch blocks any further execution
        if self.is_blocked:
            raise ToolExecutionBlockedError(
                attempted_tool=call.name,
                reason=self.block_reason or "unknown failure",
            )

        # 2. Allowlist Check
        if call.name not in self.allowed_tools:
            self._latch_block(f"Unknown tool '{call.name}'")
            raise UnknownToolError(call.name, self.allowed_tools)

        # 3. Argument Presence and Type Checking for binary arithmetic tools
        args = call.arguments
        if not isinstance(args, dict):
            self._latch_block(f"Arguments for tool '{call.name}' must be a dictionary")
            raise ToolArgumentError(
                tool_name=call.name,
                param_name="arguments",
                received_value=args,
                expected_type="dict",
                message=f"Arguments for tool '{call.name}' must be a dictionary.",
            )

        # Check required parameters: "a" and "b"
        for param in ("a", "b"):
            if param not in args:
                self._latch_block(f"Missing required parameter '{param}' for tool '{call.name}'")
                raise ToolArgumentError(
                    tool_name=call.name,
                    param_name=param,
                    received_value=None,
                    expected_type="int | float",
                    message=f"Missing required parameter '{param}' for tool '{call.name}'.",
                )

            val = args[param]

            # In Python, bool is a subclass of int (isinstance(True, int) is True).
            # Strict numeric contract requires rejecting booleans and non-numeric types.
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                self._latch_block(
                    f"Parameter '{param}' received invalid type {type(val).__name__}"
                )
                raise ToolArgumentError(
                    tool_name=call.name,
                    param_name=param,
                    received_value=val,
                    expected_type="int | float",
                    message=(
                        f"Invalid argument for tool '{call.name}': parameter '{param}' "
                        f"must be numeric (int | float), got {type(val).__name__} ({val!r})."
                    ),
                )

        # Check for unexpected extra arguments
        unexpected = set(args.keys()) - {"a", "b"}
        if unexpected:
            param = sorted(unexpected)[0]
            self._latch_block(f"Unexpected arguments: {sorted(unexpected)}")
            raise ToolArgumentError(
                tool_name=call.name,
                param_name=param,
                received_value=args[param],
                expected_type="none",
                message=f"Unexpected parameters for tool '{call.name}': {sorted(unexpected)}.",
            )

    def dispatch(self, call: ToolCall) -> ToolResult:
        """Dispatch a single ToolCall after validation.

        Preserves pre-execution state invariance: if validation fails, execution_history
        is not modified.
        """
        self.validate_call(call)

        a = call.arguments["a"]
        b = call.arguments["b"]

        if call.name == "add":
            res_val = add_tool(a, b)
        elif call.name == "multiply":
            res_val = multiply_tool(a, b)
        else:
            # Defensive guard; allowlist check in validate_call prevents this branch
            self._latch_block(f"Unimplemented tool '{call.name}'")
            raise UnknownToolError(call.name, self.allowed_tools)

        result_obj = ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            success=True,
            result=res_val,
        )
        self.execution_history.append(result_obj)
        return result_obj

    def dispatch_json(self, raw_json: Union[str, Dict[str, Any]]) -> ToolResult:
        """Parse raw JSON string or dictionary representation into a ToolCall and dispatch."""
        if isinstance(raw_json, str):
            try:
                payload = json.loads(raw_json)
            except json.JSONDecodeError as exc:
                if not self.is_blocked:
                    self._latch_block(f"Malformed JSON: {exc}")
                raise ToolArgumentError(
                    tool_name="",
                    param_name="raw_json",
                    received_value=raw_json,
                    expected_type="valid JSON string",
                    message=f"Failed to decode JSON payload: {exc}",
                ) from exc
        elif isinstance(raw_json, dict):
            payload = raw_json
        else:
            if not self.is_blocked:
                self._latch_block(f"Unsupported payload type {type(raw_json).__name__}")
            raise ToolArgumentError(
                tool_name="",
                param_name="raw_json",
                received_value=raw_json,
                expected_type="str | dict",
                message=f"Payload must be a JSON string or dict, got {type(raw_json).__name__}.",
            )

        if not isinstance(payload, dict):
            if not self.is_blocked:
                self._latch_block("JSON root must be an object/dict")
            raise ToolArgumentError(
                tool_name="",
                param_name="payload",
                received_value=payload,
                expected_type="dict",
                message="Parsed JSON payload must be an object.",
            )

        if "name" not in payload or not isinstance(payload["name"], str):
            if not self.is_blocked:
                self._latch_block("Missing or invalid 'name' in payload")
            raise ToolArgumentError(
                tool_name=str(payload.get("name", "")),
                param_name="name",
                received_value=payload.get("name"),
                expected_type="str",
                message="Tool call payload must contain a string 'name'.",
            )

        if "arguments" not in payload or not isinstance(payload["arguments"], dict):
            if not self.is_blocked:
                self._latch_block("Missing or invalid 'arguments' in payload")
            raise ToolArgumentError(
                tool_name=payload["name"],
                param_name="arguments",
                received_value=payload.get("arguments"),
                expected_type="dict",
                message="Tool call payload must contain a dict 'arguments'.",
            )

        call = ToolCall(
            name=payload["name"],
            arguments=payload["arguments"],
            call_id=payload.get("call_id"),
        )
        return self.dispatch(call)

    def execute_sequence(
        self, calls: Sequence[Union[ToolCall, str, Dict[str, Any]]]
    ) -> List[ToolResult]:
        """Execute a sequence of tool calls sequentially.

        Halts immediately on first failure; subsequent calls in the sequence are not executed.
        """
        results: List[ToolResult] = []
        for call_item in calls:
            if isinstance(call_item, ToolCall):
                res = self.dispatch(call_item)
            elif isinstance(call_item, (str, dict)):
                res = self.dispatch_json(call_item)
            else:
                if not self.is_blocked:
                    self._latch_block(f"Unsupported item type {type(call_item).__name__}")
                raise ToolArgumentError(
                    tool_name="",
                    param_name="call_item",
                    received_value=call_item,
                    expected_type="ToolCall | str | dict",
                )
            results.append(res)
        return results


def run_demo() -> None:
    """Demonstrate typed tool dispatch, validation boundaries, and failure containment."""
    print("=" * 65)
    print("Deterministic Typed Tool Dispatch Demo (Lab R17-T022)")
    print("=" * 65)

    dispatcher = ToolDispatcher()
    print(f"Configured Allowed Tools: {sorted(dispatcher.allowed_tools)}")
    print(f"Initial Session State:    blocked={dispatcher.is_blocked}, history_count={len(dispatcher.execution_history)}\n")

    # 1. Normal Happy Path
    print("1. Executing Happy Path Operations:")
    call1 = ToolCall(name="add", arguments={"a": 2, "b": 3}, call_id="call_001")
    res1 = dispatcher.dispatch(call1)
    print(f"  -> dispatch(add, a=2, b=3) -> result={res1.result} (success={res1.success})")

    call2 = ToolCall(name="multiply", arguments={"a": 2, "b": 3}, call_id="call_002")
    res2 = dispatcher.dispatch(call2)
    print(f"  -> dispatch(multiply, a=2, b=3) -> result={res2.result} (success={res2.success})")
    print(f"  Execution history count: {len(dispatcher.execution_history)}\n")

    # 2. JSON Dispatch Demonstration
    print("2. Executing JSON-Formatted Dispatch:")
    json_call = '{"name": "add", "arguments": {"a": 10.5, "b": 4.5}, "call_id": "call_003"}'
    res3 = dispatcher.dispatch_json(json_call)
    print(f"  -> dispatch_json({json_call}) -> result={res3.result}\n")

    # 3. Boundary & Rejection Demonstration (Pre-execution state invariance)
    print("3. Demonstrating Argument Rejection (String input without coercion):")
    fresh_dispatcher = ToolDispatcher()
    invalid_call = ToolCall(name="add", arguments={"a": "2", "b": 3}, call_id="call_bad_1")
    try:
        fresh_dispatcher.dispatch(invalid_call)
    except ToolArgumentError as exc:
        print(f"  -> REJECTED by ArgumentValidator: {exc}")
        print(f"  Pre-execution state invariant preserved:")
        print(f"     history_count={len(fresh_dispatcher.execution_history)} (unmutated)")
        print(f"     is_blocked={fresh_dispatcher.is_blocked}")
        print(f"     block_reason={fresh_dispatcher.block_reason}\n")

    # 4. Failure Containment Demonstration
    print("4. Demonstrating Failure Containment Latch:")
    print("  Attempting valid call on blocked session:")
    try:
        fresh_dispatcher.dispatch(call1)
    except ToolExecutionBlockedError as exc:
        print(f"  -> BLOCKED by FailureContainmentLatch: {exc}\n")

    # 5. Unknown Tool Rejection
    print("5. Demonstrating Unknown Tool Rejection:")
    fresh_dispatcher2 = ToolDispatcher()
    unknown_call = ToolCall(name="divide", arguments={"a": 10, "b": 2})
    try:
        fresh_dispatcher2.dispatch(unknown_call)
    except UnknownToolError as exc:
        print(f"  -> REJECTED by AllowlistValidator: {exc}\n")

    print("=" * 65)
    print("Demo execution trace completed successfully.")
    print("=" * 65)


if __name__ == "__main__":
    run_demo()
