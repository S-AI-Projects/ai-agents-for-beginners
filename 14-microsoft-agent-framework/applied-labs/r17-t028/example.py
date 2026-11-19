#!/usr/bin/env python3
"""Bounded Agent Loop — Failure and Recovery Example (R17-T028).

Demonstrates a bounded agent loop execution fixture with step limits, termination
semantics, traceable action logging, and explicit error recovery on invalid/missing
data, modeling the core execution lifecycle concepts of Microsoft Agent Framework.

Educational simulation: Uses pure Python 3 standard library with zero external
dependencies or cloud service requirements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ActionType(str, Enum):
    """Supported agent actions in the bounded loop."""
    INSPECT = "inspect"
    ANSWER = "answer"
    STOP = "stop"


class LoopStatus(str, Enum):
    """Termination status of the agent loop."""
    COMPLETED = "completed"
    BUDGET_EXCEEDED = "budget_exceeded"
    FAILED = "failed"
    READY = "ready"


class ExecutionHaltedError(Exception):
    """Raised when an action is dispatched after the agent has stopped."""


class MissingDataError(Exception):
    """Raised or recorded when requested data is invalid or missing."""


@dataclass
class ActionTraceRecord:
    """Trace record capturing the execution telemetry for a single step."""
    step_number: int
    action: str
    payload: Dict[str, Any]
    status: str  # "success", "error", "stopped"
    result: Optional[Any] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    explanation: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace record to serializable dictionary."""
        return {
            "step_number": self.step_number,
            "action": self.action,
            "payload": self.payload,
            "status": self.status,
            "result": self.result,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentLoopResult:
    """Outcome and recorded trace of a bounded agent loop execution."""
    status: LoopStatus
    steps_executed: int
    max_steps: int
    trace: List[ActionTraceRecord]
    final_answer: Optional[str] = None
    is_stopped: bool = False
    error_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to serializable dictionary."""
        return {
            "status": self.status.value,
            "steps_executed": self.steps_executed,
            "max_steps": self.max_steps,
            "trace": [t.to_dict() for t in self.trace],
            "final_answer": self.final_answer,
            "is_stopped": self.is_stopped,
            "error_summary": self.error_summary,
        }


class BoundedAgentFixture:
    """Scripted agent execution fixture with bounded step limits and tracing.

    Key invariants:
    1. Maximum step budget (default: 3 steps). If exceeded, stops with `budget_exceeded`.
    2. Supported actions: [inspect, answer, stop].
    3. Normal termination: executing inspect, answer, and stop completes with `completed`.
    4. Stop guarantee: once 'stop' is executed, no subsequent tool calls may run.
    5. Missing/invalid data handling: records explicit diagnostic telemetry and error explanation.
    6. Recovery: subsequent valid steps or invocations proceed normally.
    """

    def __init__(
        self,
        max_steps: int = 3,
        data_store: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.max_steps: int = max_steps
        self.data_store: Dict[str, Any] = data_store if data_store is not None else {
            "doc_101": {
                "title": "Agent Orchestration Guidelines",
                "content": "Workflows should define explicit step budgets and exit conditions.",
            },
            "doc_102": {
                "title": "Telemetry and Observability",
                "content": "Capture OpenTelemetry spans for every agent transition and tool call.",
            },
        }
        self.current_step: int = 0
        self.is_stopped: bool = False
        self.trace: List[ActionTraceRecord] = []
        self.final_answer: Optional[str] = None

    def reset(self) -> None:
        """Reset internal state between runs."""
        self.current_step = 0
        self.is_stopped = False
        self.trace = []
        self.final_answer = None

    def execute_step(self, action: str, payload: Optional[Dict[str, Any]] = None) -> ActionTraceRecord:
        """Execute a single step within the agent loop.

        Raises:
            ExecutionHaltedError: If an action is attempted after the agent has stopped.
        """
        if self.is_stopped:
            raise ExecutionHaltedError(
                f"Action '{action}' rejected: Agent has already stopped. No tools may be called after stop."
            )

        if self.current_step >= self.max_steps:
            raise RuntimeError(
                f"Step budget exceeded ({self.current_step}/{self.max_steps}). Cannot execute further steps."
            )

        self.current_step += 1
        step_number = self.current_step
        safe_payload = payload if payload is not None else {}

        # Validate action
        valid_actions = {a.value for a in ActionType}
        if action not in valid_actions:
            record = ActionTraceRecord(
                step_number=step_number,
                action=action,
                payload=safe_payload,
                status="error",
                error_code="UNSUPPORTED_ACTION",
                error_message=f"Action '{action}' is not supported. Supported actions: {sorted(valid_actions)}",
                explanation="The agent planned an unrecognised action token not registered in the toolset.",
            )
            self.trace.append(record)
            return record

        if action == ActionType.STOP.value:
            self.is_stopped = True
            record = ActionTraceRecord(
                step_number=step_number,
                action=action,
                payload=safe_payload,
                status="stopped",
                result="Agent requested graceful termination.",
                explanation="Terminal action reached; loop marked stopped.",
            )
            self.trace.append(record)
            return record

        if action == ActionType.INSPECT.value:
            target = safe_payload.get("target")
            if target is None or str(target).strip() == "":
                record = ActionTraceRecord(
                    step_number=step_number,
                    action=action,
                    payload=safe_payload,
                    status="error",
                    error_code="MISSING_DATA",
                    error_message="Missing required field 'target' in inspect payload.",
                    explanation=(
                        "Inspect action requires a valid, non-empty 'target' identifier. "
                        "Remediation: Pass a valid document identifier (e.g., 'doc_101')."
                    ),
                )
                self.trace.append(record)
                return record

            target_key = str(target).strip()
            if target_key not in self.data_store:
                record = ActionTraceRecord(
                    step_number=step_number,
                    action=action,
                    payload=safe_payload,
                    status="error",
                    error_code="MISSING_DATA",
                    error_message=f"Record '{target_key}' not found in data store.",
                    explanation=(
                        f"Target '{target_key}' does not exist in local knowledge fixture. "
                        f"Available keys: {list(self.data_store.keys())}. "
                        "Remediation: Inspect a known key or query directory index."
                    ),
                )
                self.trace.append(record)
                return record

            # Successful inspection
            doc_data = self.data_store[target_key]
            record = ActionTraceRecord(
                step_number=step_number,
                action=action,
                payload=safe_payload,
                status="success",
                result=doc_data,
                explanation=f"Successfully retrieved document data for key '{target_key}'.",
            )
            self.trace.append(record)
            return record

        if action == ActionType.ANSWER.value:
            text = safe_payload.get("text")
            if text is None or str(text).strip() == "":
                record = ActionTraceRecord(
                    step_number=step_number,
                    action=action,
                    payload=safe_payload,
                    status="error",
                    error_code="INVALID_PAYLOAD",
                    error_message="Answer text cannot be missing or empty.",
                    explanation="Answer action requires a non-empty 'text' payload to complete synthesis.",
                )
                self.trace.append(record)
                return record

            self.final_answer = str(text).strip()
            record = ActionTraceRecord(
                step_number=step_number,
                action=action,
                payload=safe_payload,
                status="success",
                result=self.final_answer,
                explanation="Synthesised final response payload stored in agent state.",
            )
            self.trace.append(record)
            return record

        # Fallback safeguard
        record = ActionTraceRecord(
            step_number=step_number,
            action=action,
            payload=safe_payload,
            status="error",
            error_code="INTERNAL_ERROR",
            error_message="Unhandled action flow.",
        )
        self.trace.append(record)
        return record

    def run_plan(
        self,
        plan: List[Union[Dict[str, Any], tuple[str, Dict[str, Any]], str]],
    ) -> AgentLoopResult:
        """Execute a scripted sequence of planned actions within the bounded loop.

        Guarantees:
        - At most `max_steps` are executed.
        - Execution stops immediately if `is_stopped` becomes True.
        - Subsequent actions after a `stop` action are NEVER dispatched.
        """
        self.reset()

        for item in plan:
            # Check loop termination conditions before dispatching
            if self.is_stopped:
                break

            if self.current_step >= self.max_steps:
                break

            # Parse action and payload from various input representations
            if isinstance(item, str):
                action = item
                payload = {}
            elif isinstance(item, tuple):
                action = item[0]
                payload = item[1] if len(item) > 1 else {}
            elif isinstance(item, dict):
                action = item.get("action", "")
                payload = item.get("payload", {})
            else:
                action = str(item)
                payload = {}

            self.execute_step(action, payload)

        # Determine overall loop status
        if self.is_stopped:
            status = LoopStatus.COMPLETED
            error_summary = None
        elif self.current_step >= self.max_steps:
            status = LoopStatus.BUDGET_EXCEEDED
            error_summary = f"Execution terminated: reached maximum step budget of {self.max_steps}."
        else:
            # Plan ended without explicit stop
            status = LoopStatus.COMPLETED
            error_summary = None

        return AgentLoopResult(
            status=status,
            steps_executed=self.current_step,
            max_steps=self.max_steps,
            trace=list(self.trace),
            final_answer=self.final_answer,
            is_stopped=self.is_stopped,
            error_summary=error_summary,
        )


def run_concept_demo() -> Dict[str, Any]:
    """Execute standard demonstrations: normal flow, endless plan, invalid data, and recovery."""
    fixture = BoundedAgentFixture(max_steps=3)

    # 1. Normal plan: [inspect, answer, stop]
    normal_plan = [
        ("inspect", {"target": "doc_101"}),
        ("answer", {"text": "Guidelines indicate step budgets are essential."}),
        ("stop", {}),
    ]
    normal_res = fixture.run_plan(normal_plan)

    # 2. Endless plan: 5 inspect actions
    endless_plan = [
        ("inspect", {"target": "doc_101"}),
        ("inspect", {"target": "doc_101"}),
        ("inspect", {"target": "doc_101"}),
        ("inspect", {"target": "doc_101"}),
        ("inspect", {"target": "doc_101"}),
    ]
    endless_res = fixture.run_plan(endless_plan)

    # 3. Actions after stop: [inspect, stop, answer] -> answer must not be called
    stop_early_plan = [
        ("inspect", {"target": "doc_101"}),
        ("stop", {}),
        ("answer", {"text": "This should never be recorded."}),
    ]
    stop_early_res = fixture.run_plan(stop_early_plan)

    # 4. Failure scenario: Missing/invalid data
    invalid_data_plan = [
        ("inspect", {"target": "missing_doc_999"}),
        ("stop", {}),
    ]
    invalid_res = fixture.run_plan(invalid_data_plan)

    # 5. Recovery scenario: Step 1 fails on missing data, Step 2 recovers on valid data, Step 3 stops
    recovery_plan = [
        ("inspect", {"target": "nonexistent_ref"}),  # Step 1: fails with MISSING_DATA
        ("inspect", {"target": "doc_102"}),          # Step 2: recovered with valid target
        ("stop", {}),                                 # Step 3: graceful stop
    ]
    recovery_res = fixture.run_plan(recovery_plan)

    return {
        "normal": normal_res.to_dict(),
        "endless": endless_res.to_dict(),
        "stop_early": stop_early_res.to_dict(),
        "invalid_data": invalid_res.to_dict(),
        "recovery": recovery_res.to_dict(),
    }


if __name__ == "__main__":
    demo_results = run_concept_demo()
    print("=== Bounded Agent Loop Demo Results ===")
    for scenario_name, data in demo_results.items():
        print(f"\n[{scenario_name.upper()}] Status: {data['status']}, Steps: {data['steps_executed']}/{data['max_steps']}")
        for t in data["trace"]:
            print(f"  Step {t['step_number']} ({t['action']}) -> {t['status']}: {t.get('result') or t.get('error_message')}")
