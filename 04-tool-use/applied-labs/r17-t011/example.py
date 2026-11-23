#!/usr/bin/env python3
"""Typed Tool Dispatch — Runnable Concept Example (R17-T011).

Demonstrates local typed tool dispatch for agentic workflows:
- Allowlisted tool discovery and dispatch for add(a, b) and multiply(a, b).
- Type validation ensuring numeric inputs.
- Structured response and error envelopes.
- Bounded sequence execution stopping immediately upon failure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass(frozen=True)
class ToolResult:
    status: str
    result: Optional[Union[int, float]] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    tool: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"status": self.status, "tool": self.tool}
        if self.status == "success":
            data["result"] = self.result
        else:
            data["error_code"] = self.error_code
            data["message"] = self.message
        return data


def tool_add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b


def tool_multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a * b


class ToolDispatcher:
    """Dispatches tool calls against an explicit allowlist with argument validation."""

    def __init__(self) -> None:
        self._registry: Dict[str, Callable[[Union[int, float], Union[int, float]], Union[int, float]]] = {
            "add": tool_add,
            "multiply": tool_multiply,
        }

    @property
    def allowlist(self) -> List[str]:
        return sorted(self._registry.keys())

    def dispatch(self, tool_call_json: Union[str, Dict[str, Any]]) -> ToolResult:
        """Parse, validate, and execute a single tool call."""
        if isinstance(tool_call_json, str):
            try:
                payload = json.loads(tool_call_json)
            except json.JSONDecodeError as exc:
                return ToolResult(
                    status="error",
                    error_code="INVALID_JSON",
                    message=f"Failed to parse JSON payload: {exc}",
                )
        else:
            payload = tool_call_json

        tool_name = payload.get("tool")
        if not tool_name or not isinstance(tool_name, str):
            return ToolResult(
                status="error",
                error_code="MISSING_TOOL_NAME",
                message="Payload must contain a string 'tool' field",
                tool=str(tool_name),
            )

        if tool_name not in self._registry:
            return ToolResult(
                status="error",
                error_code="UNKNOWN_TOOL",
                message=f"Tool '{tool_name}' is not in the allowlist {self.allowlist}",
                tool=tool_name,
            )

        args = payload.get("args")
        if not isinstance(args, dict):
            return ToolResult(
                status="error",
                error_code="INVALID_ARGUMENTS",
                message="Tool arguments must be provided as a dictionary",
                tool=tool_name,
            )

        if "a" not in args or "b" not in args:
            return ToolResult(
                status="error",
                error_code="MISSING_REQUIRED_ARGUMENTS",
                message="Arguments 'a' and 'b' are required",
                tool=tool_name,
            )

        a_val = args["a"]
        b_val = args["b"]

        if isinstance(a_val, bool) or not isinstance(a_val, (int, float)):
            return ToolResult(
                status="error",
                error_code="TYPE_ERROR",
                message=f"Argument 'a' must be numeric (int/float), got {type(a_val).__name__}",
                tool=tool_name,
            )

        if isinstance(b_val, bool) or not isinstance(b_val, (int, float)):
            return ToolResult(
                status="error",
                error_code="TYPE_ERROR",
                message=f"Argument 'b' must be numeric (int/float), got {type(b_val).__name__}",
                tool=tool_name,
            )

        handler = self._registry[tool_name]
        res = handler(a_val, b_val)
        return ToolResult(status="success", result=res, tool=tool_name)

    def dispatch_sequence(self, calls: List[Union[str, Dict[str, Any]]]) -> List[ToolResult]:
        """Execute a sequence of tool calls. If any call fails, execution stops immediately."""
        results: List[ToolResult] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if res.status != "success":
                # A failed call cannot execute another tool
                break
        return results


def main() -> None:
    dispatcher = ToolDispatcher()
    print("Available tools:", dispatcher.allowlist)

    call1 = {"tool": "add", "args": {"a": 2, "b": 3}}
    res1 = dispatcher.dispatch(call1)
    print("add(2, 3) ->", res1.to_dict())

    call2 = {"tool": "multiply", "args": {"a": 2, "b": 3}}
    res2 = dispatcher.dispatch(call2)
    print("multiply(2, 3) ->", res2.to_dict())

    call_invalid_tool = {"tool": "subtract", "args": {"a": 5, "b": 2}}
    res_unknown = dispatcher.dispatch(call_invalid_tool)
    print("unknown tool ->", res_unknown.to_dict())

    call_invalid_type = {"tool": "add", "args": {"a": "2", "b": 3}}
    res_type = dispatcher.dispatch(call_invalid_type)
    print("string argument ->", res_type.to_dict())


if __name__ == "__main__":
    main()
