#!/usr/bin/env python3
"""Bounded Agent Loop — Evaluation Experiment (R17-T019).

Demonstrates core agent loop bounding and empirical evaluation:
- Local scripted agent loop enforcing a step budget.
- Actions [inspect, answer, stop] terminate normally.
- Endless plans halt at step budget with 'budget_exceeded'.
- Invariant: no tools are called after 'stop'.
- Evaluation Experiment:
  Compares 3 controlled configurations (Step Budget = 2, 3, 5) evaluating
  completion rate, step overhead, and containment efficiency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class ActionTraceItem:
    step: int
    action: str
    status: str


@dataclass
class EvaluationRun:
    status: str  # "terminated_normally", "budget_exceeded", "error"
    executed_steps: int
    budget: int
    trace: List[ActionTraceItem] = field(default_factory=list)


class ExperimentAgent:
    """Scripted agent with configurable step budget for evaluation experiments."""

    def __init__(self, step_budget: int = 3) -> None:
        self.step_budget = step_budget
        self._actions: Dict[str, str] = {
            "inspect": "inspected",
            "answer": "answered",
            "stop": "stopped",
        }

    def execute_plan(self, actions: List[str]) -> EvaluationRun:
        trace: List[ActionTraceItem] = []
        stopped = False

        for step_idx, act in enumerate(actions, start=1):
            if step_idx > self.step_budget:
                return EvaluationRun(
                    status="budget_exceeded",
                    executed_steps=len(trace),
                    budget=self.step_budget,
                    trace=trace,
                )

            if act == "stop":
                trace.append(ActionTraceItem(step=step_idx, action="stop", status="stopped"))
                stopped = True
                break
            elif act in self._actions:
                trace.append(ActionTraceItem(step=step_idx, action=act, status="completed"))
            else:
                trace.append(ActionTraceItem(step=step_idx, action=act, status="error"))
                return EvaluationRun(
                    status="error",
                    executed_steps=len(trace),
                    budget=self.step_budget,
                    trace=trace,
                )

        if stopped or len(trace) < self.step_budget:
            return EvaluationRun(
                status="terminated_normally",
                executed_steps=len(trace),
                budget=self.step_budget,
                trace=trace,
            )

        return EvaluationRun(
            status="budget_exceeded",
            executed_steps=len(trace),
            budget=self.step_budget,
            trace=trace,
        )


@dataclass(frozen=True)
class ExperimentSummary:
    budget: int
    canonical_completion: bool
    endless_halt_step: int
    tradeoff_notes: str


def run_budget_experiment() -> Dict[int, ExperimentSummary]:
    """Evaluates 3 controlled configurations (budget 2, 3, 5) against canonical & endless workloads."""
    canonical_workload = ["inspect", "answer", "stop"]
    endless_workload = ["inspect"] * 10

    results: Dict[int, ExperimentSummary] = {}
    configs = [
        (2, "Conservative: Fast containment (halts at 2), but prematurely truncates 3-step canonical tasks"),
        (3, "Optimal: Exactly fits 3-step canonical task with normal completion, bounds runaway loops at 3"),
        (5, "Permissive: Permits longer valid workloads, but permits runaway loops to waste 5 steps before halting"),
    ]

    for budget, notes in configs:
        agent = ExperimentAgent(step_budget=budget)
        res_canonical = agent.execute_plan(canonical_workload)
        res_endless = agent.execute_plan(endless_workload)

        results[budget] = ExperimentSummary(
            budget=budget,
            canonical_completion=(res_canonical.status == "terminated_normally"),
            endless_halt_step=res_endless.executed_steps,
            tradeoff_notes=notes,
        )

    return results


def main() -> None:
    agent = ExperimentAgent(step_budget=3)
    res_normal = agent.execute_plan(["inspect", "answer", "stop"])
    print("Canonical 3-step plan ->", res_normal.status, f"({res_normal.executed_steps} steps)")

    res_endless = agent.execute_plan(["inspect"] * 8)
    print("Endless plan ->", res_endless.status, f"({res_endless.executed_steps} steps)")

    print("\n=== Controlled Evaluation Experiment (Budgets: 2, 3, 5) ===")
    summaries = run_budget_experiment()
    for budget, summ in sorted(summaries.items()):
        print(f"Budget {budget}: Canonical Completed={summ.canonical_completion} | Loop Halted at Step={summ.endless_halt_step}")
        print(f"  Trade-off: {summ.tradeoff_notes}")


if __name__ == "__main__":
    main()
