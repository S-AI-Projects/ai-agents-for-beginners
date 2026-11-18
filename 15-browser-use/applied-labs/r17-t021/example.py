"""Browser-Action Guard - Runnable Concept Example.

Lesson 15: Building Computer Use Agents (CUA)
Task: R17-T021

This module provides a deterministic local fixture implementing a safety
middleware (BrowserActionGuard) for browser agents. It enforces:
1. Origin allowlisting: Validates target URLs before navigation executes.
2. Step budget limiting: Halts agent execution when step limit is reached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set
import urllib.parse


class ActionType(str, Enum):
    """Supported browser interaction primitives."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    EXTRACT = "extract"


class BrowserGuardError(Exception):
    """Base exception for all browser guard policy violations."""


class DisallowedOriginError(BrowserGuardError):
    """Raised when an action targets an origin outside the allowlist."""

    def __init__(self, url: str, origin: str, allowed_origins: Set[str]) -> None:
        self.url = url
        self.origin = origin
        self.allowed_origins = allowed_origins
        message = (
            f"Blocked navigation to disallowed origin '{origin}' (URL: '{url}'). "
            f"Allowed origins: {sorted(allowed_origins)}"
        )
        super().__init__(message)


class StepBudgetExceededError(BrowserGuardError):
    """Raised when an action exceeds the maximum allowed step budget."""

    def __init__(self, attempted_step: int, budget: int, action: BrowserAction) -> None:
        self.attempted_step = attempted_step
        self.budget = budget
        self.action = action
        message = (
            f"Cannot execute step {attempted_step}: step budget of {budget} has been exhausted "
            f"while attempting action '{action.action_type.value}'."
        )
        super().__init__(message)


@dataclass(frozen=True)
class BrowserAction:
    """Represents an atomic action proposed by an agent."""
    action_type: ActionType
    url: Optional[str] = None
    selector: Optional[str] = None
    value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    """Represents the outcome of an executed browser action."""
    step_number: int
    action: BrowserAction
    success: bool
    current_url: Optional[str]
    message: str


def extract_origin(url: str) -> str:
    """Extract and normalize the origin (host or hostname:port) from a URL.

    Accepts fully-qualified URLs as well as bare hostnames.
    Returns normalized lowercase hostname.
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    normalized = url.strip()
    if "://" not in normalized:
        # Prepend placeholder scheme to allow urlparse to extract host properly
        normalized = f"http://{normalized}"

    parsed = urllib.parse.urlsplit(normalized)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"Unable to extract hostname from URL: '{url}'")

    return hostname.lower()


class MockBrowserSession:
    """Deterministic local browser stub for safety guardrail verification.

    Maintains session state without requiring real Chrome, Playwright, or network.
    """

    def __init__(self) -> None:
        self.current_url: Optional[str] = None
        self.history: List[str] = []
        self.executed_actions: List[BrowserAction] = []

    def execute(self, action: BrowserAction, step_number: int) -> ActionResult:
        """Simulate execution of an action after it has passed guard validation."""
        self.executed_actions.append(action)

        if action.action_type == ActionType.NAVIGATE:
            if not action.url:
                raise ValueError("URL must be provided for navigate action")
            self.current_url = action.url
            self.history.append(action.url)
            message = f"Navigated to {action.url}"
        elif action.action_type == ActionType.CLICK:
            message = f"Clicked element matching '{action.selector}'"
        elif action.action_type == ActionType.TYPE_TEXT:
            message = f"Typed '{action.value}' into '{action.selector}'"
        elif action.action_type == ActionType.EXTRACT:
            message = f"Extracted content from '{action.selector or 'page'}'"
        else:
            message = f"Executed {action.action_type.value}"

        return ActionResult(
            step_number=step_number,
            action=action,
            success=True,
            current_url=self.current_url,
            message=message,
        )


class BrowserActionGuard:
    """Safety guardrail intercepting and validating proposed browser actions.

    Guarantees:
    1. Origin Policy: Any navigation targeting an origin outside `allowed_origins`
       is rejected BEFORE execution.
    2. Step Budget: If `step_count >= step_budget`, further actions are rejected
       BEFORE execution, terminating infinite loops.
    """

    def __init__(self, allowed_origins: Sequence[str], step_budget: int = 3) -> None:
        if step_budget < 0:
            raise ValueError("step_budget must be non-negative")

        self.allowed_origins: Set[str] = {
            extract_origin(origin) for origin in allowed_origins if origin.strip()
        }
        if not self.allowed_origins:
            raise ValueError("At least one valid allowed origin must be specified")

        self.step_budget: int = step_budget
        self.step_count: int = 0
        self.action_history: List[ActionResult] = []

    def validate_action(self, action: BrowserAction) -> None:
        """Validate proposed action against origin and budget rules.

        Raises:
            StepBudgetExceededError: if current step count reached budget limit.
            DisallowedOriginError: if navigate action targets an unapproved origin.
            ValueError: if required action parameters are missing.
        """
        # 1. Budget gate check (checked strictly prior to execution)
        if self.step_count >= self.step_budget:
            raise StepBudgetExceededError(
                attempted_step=self.step_count + 1,
                budget=self.step_budget,
                action=action,
            )

        # 2. Origin containment check (checked strictly prior to navigation)
        if action.action_type == ActionType.NAVIGATE:
            if not action.url:
                raise ValueError("URL cannot be empty for navigate action")
            origin = extract_origin(action.url)
            if origin not in self.allowed_origins:
                raise DisallowedOriginError(
                    url=action.url,
                    origin=origin,
                    allowed_origins=self.allowed_origins,
                )

    def execute_step(
        self, action: BrowserAction, browser: MockBrowserSession
    ) -> ActionResult:
        """Validate action with guard and execute on mock browser session."""
        # Policy enforcement: rejects invalid actions before execution
        self.validate_action(action)

        # Increment internal step counter
        self.step_count += 1

        # Execute on stub browser
        result = browser.execute(action, self.step_count)
        self.action_history.append(result)
        return result


def run_concept_demo() -> None:
    """Demonstrate the safety guardrail with the standard lesson scenario."""
    print("=" * 60)
    print("Running Browser-Action Guard Demo (Lesson 15 Concept Example)")
    print("=" * 60)

    allowed_origin = "example.invalid"
    guard = BrowserActionGuard(allowed_origins=[allowed_origin], step_budget=3)
    browser = MockBrowserSession()

    print(f"Configured Allowed Origin: {guard.allowed_origins}")
    print(f"Configured Step Budget:    {guard.step_budget}\n")

    # Sequence of proposed actions
    actions = [
        # Step 1: Valid navigation to allowed origin
        BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/search"),
        # Step 2: Valid in-page interaction
        BrowserAction(ActionType.CLICK, selector="#search-button"),
        # Step 3: Valid navigation to allowed origin (hits 3-step limit)
        BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/results?page=2"),
        # Step 4: Exceeds budget (expected to fail)
        BrowserAction(ActionType.EXTRACT, selector=".listing-title"),
    ]

    for idx, act in enumerate(actions, start=1):
        try:
            print(f"[Attempt {idx}] Action: {act.action_type.value} (url={act.url})")
            res = guard.execute_step(act, browser)
            print(f"  -> SUCCESS: Step {res.step_number} completed: {res.message}")
        except StepBudgetExceededError as err:
            print(f"  -> BLOCKED by StepBudgetGuard: {err}")
        except DisallowedOriginError as err:
            print(f"  -> BLOCKED by OriginGuard: {err}")

    # Demonstrate origin rejection
    print("\nDemonstrating Origin Policy Enforcement:")
    rogue_action = BrowserAction(
        ActionType.NAVIGATE, url="https://malicious.invalid/phishing"
    )
    # Reset budget for demonstration
    fresh_guard = BrowserActionGuard(allowed_origins=["example.invalid"], step_budget=3)
    try:
        print(f"Attempting navigation to untrusted URL: {rogue_action.url}")
        fresh_guard.execute_step(rogue_action, browser)
    except DisallowedOriginError as err:
        print(f"  -> BLOCKED BEFORE EXECUTION: {err}")

    print("\nConcept demonstration completed successfully.")


if __name__ == "__main__":
    run_concept_demo()
