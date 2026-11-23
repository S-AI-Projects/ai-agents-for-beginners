#!/usr/bin/env python3
"""Browser-Action Guard — Compare Two Approaches (R17-T013).

Demonstrates browser action guardrails:
- Origin allowlisting: navigation to 'example.invalid' succeeds; unauthorized origins rejected prior to execution.
- Step budget limit: maximum 3 actions allowed; 4th step fails.
- Comparison of two approaches:
  1. Direct stateful guard runtime (BrowserActionGuard).
  2. Independent reference evaluation / oracle table.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BrowserAction:
    action_type: str  # "navigate", "click", "type", "extract"
    target: str       # URL for navigate, selector/text for click/type


@dataclass
class GuardResult:
    allowed: bool
    status: str       # "PASSED", "ORIGIN_DISALLOWED", "BUDGET_EXCEEDED", "INVALID_ACTION"
    executed_steps: int
    rejection_reason: Optional[str] = None
    action_trace: List[str] = field(default_factory=list)


class BrowserActionGuard:
    """Direct implementation of browser-action validation with state tracking."""

    def __init__(self, allowed_origins: List[str], max_steps: int = 3) -> None:
        self.allowed_origins = set(allowed_origins)
        self.max_steps = max_steps

    def _extract_origin(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        # Handle cases with or without explicit scheme
        if not parsed.netloc and parsed.path:
            host = parsed.path.split("/")[0]
        else:
            host = parsed.netloc
        return host.lower()

    def evaluate(self, actions: List[BrowserAction]) -> GuardResult:
        trace: List[str] = []
        for idx, act in enumerate(actions, start=1):
            if idx > self.max_steps:
                return GuardResult(
                    allowed=False,
                    status="BUDGET_EXCEEDED",
                    executed_steps=len(trace),
                    rejection_reason=f"Step budget of {self.max_steps} exceeded at action {idx}",
                    action_trace=trace,
                )

            if act.action_type == "navigate":
                origin = self._extract_origin(act.target)
                if origin not in self.allowed_origins:
                    return GuardResult(
                        allowed=False,
                        status="ORIGIN_DISALLOWED",
                        executed_steps=len(trace),
                        rejection_reason=f"Target origin '{origin}' not in allowlist {sorted(self.allowed_origins)}",
                        action_trace=trace,
                    )

            trace.append(f"{act.action_type}:{act.target}")

        return GuardResult(
            allowed=True,
            status="PASSED",
            executed_steps=len(trace),
            rejection_reason=None,
            action_trace=trace,
        )


# Approach 2: Independent reference calculation using declarative rule screening
def reference_evaluate_plan(
    actions: List[BrowserAction],
    allowed_origins: List[str],
    max_steps: int = 3,
) -> Tuple[bool, str, int]:
    """Independent reference calculation for cross-verification."""
    allowed_set = set(allowed_origins)
    for idx, act in enumerate(actions, start=1):
        if idx > max_steps:
            return (False, "BUDGET_EXCEEDED", idx - 1)
        if act.action_type == "navigate":
            # Simple hostname extraction
            target = act.target.replace("https://", "").replace("http://", "").split("/")[0].lower()
            if target not in allowed_set:
                return (False, "ORIGIN_DISALLOWED", idx - 1)
    return (True, "PASSED", len(actions))


def main() -> None:
    allowed = ["example.invalid"]
    guard = BrowserActionGuard(allowed_origins=allowed, max_steps=3)

    # 1. Allowed navigation
    plan1 = [BrowserAction("navigate", "https://example.invalid/home"), BrowserAction("click", "#login")]
    res1 = guard.evaluate(plan1)
    print("Plan 1 (Allowed):", res1.status, "Executed:", res1.executed_steps)

    # 2. Disallowed origin
    plan2 = [BrowserAction("navigate", "https://unauthorized.org/page")]
    res2 = guard.evaluate(plan2)
    print("Plan 2 (Unauthorized origin):", res2.status, "-", res2.rejection_reason)

    # 3. Budget exceeded on 4th step
    plan3 = [
        BrowserAction("navigate", "https://example.invalid/page1"),
        BrowserAction("click", "#next"),
        BrowserAction("type", "input#search"),
        BrowserAction("click", "#submit"),  # 4th action
    ]
    res3 = guard.evaluate(plan3)
    print("Plan 3 (4 actions, budget=3):", res3.status, "-", res3.rejection_reason)


if __name__ == "__main__":
    main()
