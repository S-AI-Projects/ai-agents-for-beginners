#!/usr/bin/env python3
"""Bounded Agent Loop — Boundary-Case Lesson Extension (R17-T012).

Demonstrates step budget enforcement and lifecycle control:
- Hard step limit: maximum 3 steps.
- Termination on 'stop' action with recorded execution trace.
- Actions [inspect, answer, stop] terminate normally.
- Endless plans halt at step 3 with 'budget_exceeded'.
- Guaranteed post-stop immutability: no tool is executed after 'stop'.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class StepRecord:
    step_number: int
    action: str
    status: str
    detail: Optional[str] = None


@dataclass
class AgentRunResult:
    status: str  # "terminated_normally" or "budget_exceeded"
    total_steps: int
    trace: List[StepRecord] = field(default_factory=list)
    final_output: Optional[str] = None


class BoundedAgent:
    """A deterministic scripted agent enforcing a strict step budget."""

    MAX_STEPS: int = 3

    def __init__(self, step_budget: int = MAX_STEPS) -> None:
        self.step_budget = step_budget
        self._action_handlers: Dict[str, Callable[[int], str]] = {
            "inspect": self._handle_inspect,
            "answer": self._handle_answer,
            "stop": self._handle_stop,
        }

    def _handle_inspect(self, step: int) -> str:
        return f"Inspected environment at step {step}"

    def _handle_answer(self, step: int) -> str:
        return f"Synthesized answer at step {step}"

    def _handle_stop(self, step: int) -> str:
        return "Agent signaled stop"

    def run(self, planned_actions: List[str]) -> AgentRunResult:
        """Executes a list of planned actions within the allocated step budget."""
        trace: List[StepRecord] = []
        stopped = False
        final_output = None

        for idx, action in enumerate(planned_actions, start=1):
            if idx > self.step_budget:
                return AgentRunResult(
                    status="budget_exceeded",
                    total_steps=len(trace),
                    trace=trace,
                    final_output=final_output,
                )

            if action == "stop":
                trace.append(StepRecord(step_number=idx, action="stop", status="completed", detail=self._handle_stop(idx)))
                stopped = True
                final_output = "Execution completed normally via stop"
                break
            elif action in self._action_handlers:
                detail = self._action_handlers[action](idx)
                trace.append(StepRecord(step_number=idx, action=action, status="completed", detail=detail))
                if action == "answer":
                    final_output = detail
            else:
                trace.append(StepRecord(step_number=idx, action=action, status="error", detail=f"Unknown action: {action}"))
                return AgentRunResult(
                    status="error",
                    total_steps=len(trace),
                    trace=trace,
                    final_output=f"Failed on unknown action '{action}'",
                )

        if stopped:
            return AgentRunResult(
                status="terminated_normally",
                total_steps=len(trace),
                trace=trace,
                final_output=final_output,
            )

        # If loop finished all actions without explicit stop, or if budget reached
        if len(trace) >= self.step_budget:
            return AgentRunResult(
                status="budget_exceeded",
                total_steps=len(trace),
                trace=trace,
                final_output=final_output,
            )

        return AgentRunResult(
            status="terminated_normally",
            total_steps=len(trace),
            trace=trace,
            final_output=final_output or "Completed all planned actions",
        )


def main() -> None:
    agent = BoundedAgent()

    # 1. Canonical normal termination within budget
    canonical_plan = ["inspect", "answer", "stop"]
    res1 = agent.run(canonical_plan)
    print("Plan ['inspect', 'answer', 'stop'] ->", res1.status, f"({res1.total_steps} steps)")

    # 2. Endless plan halts at max steps with budget_exceeded
    endless_plan = ["inspect", "inspect", "inspect", "inspect", "inspect"]
    res2 = agent.run(endless_plan)
    print("Endless plan ->", res2.status, f"({res2.total_steps} steps)")

    # 3. Post-stop guarantee
    extra_plan = ["inspect", "stop", "answer"]
    res3 = agent.run(extra_plan)
    print("Plan with action after stop -> total executed steps:", res3.total_steps, [s.action for s in res3.trace])


if __name__ == "__main__":
    main()
