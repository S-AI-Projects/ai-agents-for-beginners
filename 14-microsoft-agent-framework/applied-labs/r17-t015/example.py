#!/usr/bin/env python3
"""Bounded Agent Loop — Offline Service Adapter (R17-T015).

Demonstrates decoupling agent loop logic from external services:
- Defines an explicit callable adapter interface (AgentServiceAdapter).
- Provides a deterministic offline implementation (LocalDeterministicAdapter).
- Bounds execution to at most 3 steps; halts endless plans with 'budget_exceeded'.
- Enforces post-stop invariants (no calls executed after 'stop').
- Explicitly documents real-service behaviors that an offline mock does not establish.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AgentServiceAdapter(ABC):
    """Callable interface abstracting model/tool interactions."""

    @abstractmethod
    def execute_inspect(self, step: int) -> str:
        """Inspect environment or external resource."""
        raise NotImplementedError

    @abstractmethod
    def execute_answer(self, step: int) -> str:
        """Synthesize and format response."""
        raise NotImplementedError

    @abstractmethod
    def execute_stop(self, step: int) -> str:
        """Signal workflow completion."""
        raise NotImplementedError


class LocalDeterministicAdapter(AgentServiceAdapter):
    """Deterministic local adapter for testing without external services.
    
    Limitations:
    - Does not simulate variable network latencies, HTTP 429 rate limits, or TCP drops.
    - Does not validate cloud Entra ID token refresh workflows.
    - Does not test nondeterministic model output distributions or schema drift.
    """

    def execute_inspect(self, step: int) -> str:
        return f"Deterministic inspection at step {step}"

    def execute_answer(self, step: int) -> str:
        return f"Deterministic answer synthesized at step {step}"

    def execute_stop(self, step: int) -> str:
        return "Deterministic stop acknowledged"


@dataclass(frozen=True)
class ActionRecord:
    step_number: int
    action: str
    output: str


@dataclass
class AgentLoopResult:
    status: str  # "terminated_normally" or "budget_exceeded"
    total_steps: int
    trace: List[ActionRecord] = field(default_factory=list)
    final_output: Optional[str] = None


class AdapterBoundedAgent:
    """Agent loop interacting exclusively through an AgentServiceAdapter."""

    MAX_STEPS: int = 3

    def __init__(self, adapter: Optional[AgentServiceAdapter] = None, step_budget: int = MAX_STEPS) -> None:
        self.adapter = adapter if adapter is not None else LocalDeterministicAdapter()
        self.step_budget = step_budget

    def run(self, planned_actions: List[str]) -> AgentLoopResult:
        trace: List[ActionRecord] = []
        stopped = False
        final_output: Optional[str] = None

        for idx, action in enumerate(planned_actions, start=1):
            if idx > self.step_budget:
                return AgentLoopResult(
                    status="budget_exceeded",
                    total_steps=len(trace),
                    trace=trace,
                    final_output=final_output,
                )

            if action == "stop":
                out = self.adapter.execute_stop(idx)
                trace.append(ActionRecord(step_number=idx, action="stop", output=out))
                stopped = True
                final_output = out
                break
            elif action == "inspect":
                out = self.adapter.execute_inspect(idx)
                trace.append(ActionRecord(step_number=idx, action="inspect", output=out))
            elif action == "answer":
                out = self.adapter.execute_answer(idx)
                trace.append(ActionRecord(step_number=idx, action="answer", output=out))
                final_output = out
            else:
                out = f"Unsupported action: {action}"
                trace.append(ActionRecord(step_number=idx, action=action, output=out))
                return AgentLoopResult(
                    status="error",
                    total_steps=len(trace),
                    trace=trace,
                    final_output=out,
                )

        if stopped or len(trace) < self.step_budget:
            return AgentLoopResult(
                status="terminated_normally",
                total_steps=len(trace),
                trace=trace,
                final_output=final_output or "Execution finished",
            )

        return AgentLoopResult(
            status="budget_exceeded",
            total_steps=len(trace),
            trace=trace,
            final_output=final_output,
        )


def main() -> None:
    agent = AdapterBoundedAgent()
    # 1. Normal run
    res1 = agent.run(["inspect", "answer", "stop"])
    print("Normal run status:", res1.status, f"({res1.total_steps} steps)")
    for rec in res1.trace:
        print(f"  Step {rec.step_number}: {rec.action} -> {rec.output}")

    # 2. Endless plan
    res2 = agent.run(["inspect"] * 5)
    print("Endless run status:", res2.status, f"({res2.total_steps} steps)")

    # 3. Post-stop dropped action
    res3 = agent.run(["inspect", "stop", "answer"])
    print("Post-stop plan executed actions:", [rec.action for rec in res3.trace])


if __name__ == "__main__":
    main()
