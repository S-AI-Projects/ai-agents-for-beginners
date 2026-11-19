"""Allowlisted Action Policy — Worked Example with Checks.

Lesson 06: Building Trustworthy AI Agents
Task: R17-T027

This module implements a deterministic pre-execution policy guardrail for AI agents:
1. Validates proposed actions against an explicit allowed-tool allowlist (e.g. 'read').
2. Validates per-tool argument schemas (e.g. required 'path' parameter of type str).
3. Guarantees that disallowed tools (e.g. 'delete') and invalid arguments are rejected
   BEFORE execution reaches the underlying executor stub.
4. Includes an explicit worked input-to-output explanation table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Callable, Dict, List, Optional, Set, Type


class PolicyViolationError(Exception):
    """Base exception for all action policy enforcement failures."""


class DisallowedToolError(PolicyViolationError):
    """Raised when an agent attempts to execute an unauthorized tool."""

    def __init__(self, attempted_tool: str, allowed_tools: Set[str]) -> None:
        self.attempted_tool = attempted_tool
        self.allowed_tools = allowed_tools
        super().__init__(
            f"Action policy blocked tool '{attempted_tool}'. "
            f"Allowed tool set: {sorted(allowed_tools)}"
        )


class ArgumentValidationError(PolicyViolationError):
    """Raised when tool arguments fail per-tool schema validation."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"Argument schema validation failed for tool '{tool_name}': {message}")


@dataclass(frozen=True)
class ToolCall:
    """Proposed tool action submitted by an agent."""
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolExecutionResult:
    """Outcome produced by the stub executor upon successful policy passage."""
    success: bool
    tool_name: str
    output: Any
    message: str


@dataclass(frozen=True)
class ToolSchema:
    """Schema specifying parameter rules for an authorized tool."""
    tool_name: str
    required_params: Set[str]
    param_types: Dict[str, Type]


class StubExecutor:
    """Deterministic local stub executor simulating backend tool dispatch."""

    def __init__(self) -> None:
        self.executed_calls: List[ToolCall] = []

    def execute(self, tool_call: ToolCall) -> ToolExecutionResult:
        """Simulate execution of an action that has passed policy evaluation."""
        self.executed_calls.append(tool_call)

        if tool_call.tool_name == "read":
            path = tool_call.arguments.get("path")
            return ToolExecutionResult(
                success=True,
                tool_name="read",
                output=f"Simulated contents of {path}",
                message=f"Successfully read from path: {path}",
            )
        else:
            return ToolExecutionResult(
                success=True,
                tool_name=tool_call.tool_name,
                output="Default stub execution result",
                message=f"Executed {tool_call.tool_name}",
            )


class AllowedActionPolicy:
    """Enforces explicit tool allowlisting and per-tool argument validation."""

    def __init__(self, tool_schemas: Optional[Dict[str, ToolSchema]] = None) -> None:
        # Default allowlist: 'read' tool with required 'path' parameter
        self.schemas: Dict[str, ToolSchema] = tool_schemas or {
            "read": ToolSchema(
                tool_name="read",
                required_params={"path"},
                param_types={"path": str},
            )
        }

    @property
    def allowed_tools(self) -> Set[str]:
        return set(self.schemas.keys())

    def validate(self, tool_call: ToolCall) -> None:
        """Evaluate a proposed tool call against policy rules.

        Raises:
            DisallowedToolError: If tool_name is not in the allowed tool set.
            ArgumentValidationError: If arguments do not satisfy the tool schema.
        """
        # Rule 1: Tool Allowlist Check
        if tool_call.tool_name not in self.schemas:
            raise DisallowedToolError(tool_call.tool_name, self.allowed_tools)

        schema = self.schemas[tool_call.tool_name]
        args = tool_call.arguments

        # Rule 2: Required Arguments Check
        missing = schema.required_params - set(args.keys())
        if missing:
            raise ArgumentValidationError(
                tool_call.tool_name,
                f"Missing required parameter(s): {sorted(missing)}",
            )

        # Rule 3: Parameter Type and Value Check
        for param, expected_type in schema.param_types.items():
            if param in args:
                val = args[param]
                if not isinstance(val, expected_type):
                    raise ArgumentValidationError(
                        tool_call.tool_name,
                        f"Parameter '{param}' expected type {expected_type.__name__}, got {type(val).__name__}",
                    )
                if expected_type is str and not val.strip():
                    raise ArgumentValidationError(
                        tool_call.tool_name,
                        f"Parameter '{param}' cannot be an empty or whitespace string",
                    )


class GuardedActionDispatcher:
    """Coordinates policy validation and stub execution, enforcing pre-execution refusal."""

    def __init__(self, policy: AllowedActionPolicy, executor: StubExecutor) -> None:
        self.policy = policy
        self.executor = executor
        self.rejection_log: List[Dict[str, Any]] = []

    def dispatch(self, tool_call: ToolCall) -> ToolExecutionResult:
        """Validate proposed action and execute only if policy passes.

        Guarantees:
        Rejected actions NEVER reach self.executor.execute().
        """
        try:
            # Policy check happens strictly prior to execution
            self.policy.validate(tool_call)
        except PolicyViolationError as err:
            self.rejection_log.append({
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
                "error_type": type(err).__name__,
                "reason": str(err),
            })
            raise

        # Execution reached only upon successful validation
        return self.executor.execute(tool_call)


# Worked input-to-output explanation catalog
WORKED_EXPLANATIONS: List[Dict[str, Any]] = [
    {
        "case_id": "CASE_1_ALLOWED_READ",
        "description": "Allowed 'read' tool with a valid 'path' argument",
        "input": {"tool_name": "read", "arguments": {"path": "/safe/data/metrics.csv"}},
        "policy_evaluation": "Tool 'read' is in allowlist; 'path' is provided, non-empty, and type str.",
        "expected_action": "Dispatched to StubExecutor",
        "expected_result": "Success: Simulated contents of /safe/data/metrics.csv",
        "executor_reached": True,
    },
    {
        "case_id": "CASE_2_DISALLOWED_DELETE",
        "description": "Unauthorized 'delete' tool attempted by agent",
        "input": {"tool_name": "delete", "arguments": {"path": "/safe/data/metrics.csv"}},
        "policy_evaluation": "Tool 'delete' is NOT in allowlist {'read'}. Blocked immediately.",
        "expected_action": "Raises DisallowedToolError; execution aborted.",
        "expected_result": "Blocked before execution; StubExecutor untouched.",
        "executor_reached": False,
    },
    {
        "case_id": "CASE_3_MISSING_REQUIRED_ARGUMENT",
        "description": "Allowed 'read' tool with missing required 'path' parameter",
        "input": {"tool_name": "read", "arguments": {}},
        "policy_evaluation": "Tool 'read' is allowed, but required parameter 'path' is absent.",
        "expected_action": "Raises ArgumentValidationError; execution aborted.",
        "expected_result": "Blocked before execution; StubExecutor untouched.",
        "executor_reached": False,
    },
]


def run_concept_demo() -> None:
    """Demonstrate policy validation across the 3 canonical cases."""
    print("=" * 70)
    print("Allowlisted Action Policy — Worked Example Demo (Lesson 06)")
    print("=" * 70)

    policy = AllowedActionPolicy()
    executor = StubExecutor()
    dispatcher = GuardedActionDispatcher(policy, executor)

    print(f"\nConfigured Policy Allowed Tools: {policy.allowed_tools}\n")

    for case in WORKED_EXPLANATIONS:
        tool_call = ToolCall(case["input"]["tool_name"], case["input"]["arguments"])
        print(f"--- Running: {case['case_id']} ---")
        print(f"Description: {case['description']}")
        print(f"Input:       {json.dumps(case['input'])}")
        initial_executor_count = len(executor.executed_calls)

        try:
            result = dispatcher.dispatch(tool_call)
            print(f"Outcome:     SUCCESS -> {result.message}")
        except PolicyViolationError as err:
            print(f"Outcome:     BLOCKED -> [{type(err).__name__}] {err}")

        executor_delta = len(executor.executed_calls) - initial_executor_count
        print(f"Executor Calls Incremented: {executor_delta} (Reached: {executor_delta > 0})\n")

    print(f"Total Successful Executor Calls: {len(executor.executed_calls)}")
    print(f"Total Blocked Policy Rejections: {len(dispatcher.rejection_log)}")


if __name__ == "__main__":
    run_concept_demo()
