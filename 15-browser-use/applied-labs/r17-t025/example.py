"""Browser-Action Guard — Offline Service Adapter.

Lesson 15: Building Computer Use Agents (CUA)
Task: R17-T025

This module decouples browser-action guard validation from real browser automation by:
1. Placing the external browser dependency behind an abstract callable interface (BrowserServiceAdapter).
2. Supplying a deterministic local adapter (OfflineLocalBrowserAdapter).
3. Explicitly cataloging real-service behaviors that the mock adapter does not establish.
4. Enforcing origin containment (allowing example.invalid, rejecting other origins before execution)
   and execution step budget (failing on 4th step under a 3-step budget).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set
import urllib.parse


class ActionType(str, Enum):
    """Supported browser action primitives."""
    NAVIGATE = "navigate"
    CLICK = "click"
    EXTRACT = "extract"


class BrowserGuardError(Exception):
    """Base exception for all guardrail policy violations."""


class DisallowedOriginError(BrowserGuardError):
    """Raised when navigation targets an origin outside the allowlist."""

    def __init__(self, url: str, origin: str, allowed_origins: Set[str]) -> None:
        self.url = url
        self.origin = origin
        self.allowed_origins = allowed_origins
        super().__init__(
            f"Blocked navigation to disallowed origin '{origin}' (URL: '{url}'). "
            f"Allowed origins: {sorted(allowed_origins)}"
        )


class StepBudgetExceededError(BrowserGuardError):
    """Raised when action execution exceeds the configured step budget."""

    def __init__(self, attempted_step: int, budget: int, action: BrowserAction) -> None:
        self.attempted_step = attempted_step
        self.budget = budget
        self.action = action
        super().__init__(
            f"Cannot execute step {attempted_step}: step budget of {budget} has been exhausted "
            f"while attempting action '{action.action_type.value}'."
        )


@dataclass(frozen=True)
class BrowserAction:
    """Atomic browser action proposed by agent."""
    action_type: ActionType
    url: Optional[str] = None
    selector: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionResult:
    """Outcome of an executed browser action."""
    step_number: int
    action: BrowserAction
    success: bool
    current_url: Optional[str]
    message: str


# Explicit catalog of behaviors that this deterministic offline adapter does NOT establish
REAL_SERVICE_UNSUPPORTED_BEHAVIORS: List[str] = [
    "Real network socket negotiation, DNS resolution, TLS handshakes, and HTTP/2 multiplexing.",
    "Dynamic DOM tree mutations, JavaScript single-page app (SPA) rendering, and CSS reflows.",
    "Browser process crashes, native memory constraints, and Chrome DevTools Protocol (CDP) IPC transport delays.",
    "Cross-origin security policies (CORS), iframe sandbox boundaries, and web storage isolation.",
    "HTTP cookie lifecycle, cache headers, local storage persistence, and session eviction.",
    "Visual screenshot generation, actual viewport pixel coordinates, and simulated user input event bubbling.",
]


class BrowserServiceAdapter(ABC):
    """Callable abstract interface decoupling browser interaction from specific drivers."""

    @abstractmethod
    def navigate(self, url: str, step_number: int) -> ActionResult:
        """Navigate to target URL."""

    @abstractmethod
    def click(self, selector: str, step_number: int) -> ActionResult:
        """Click element matching selector."""

    @abstractmethod
    def extract(self, selector: Optional[str], step_number: int) -> ActionResult:
        """Extract content from element or page."""

    @property
    @abstractmethod
    def current_url(self) -> Optional[str]:
        """Return the current active URL."""

    @property
    @abstractmethod
    def execution_history(self) -> List[ActionResult]:
        """Return audit history of executed actions."""


class OfflineLocalBrowserAdapter(BrowserServiceAdapter):
    """Deterministic in-memory browser adapter for offline validation."""

    def __init__(self) -> None:
        self._current_url: Optional[str] = None
        self._history: List[ActionResult] = []

    def navigate(self, url: str, step_number: int) -> ActionResult:
        action = BrowserAction(ActionType.NAVIGATE, url=url)
        self._current_url = url
        res = ActionResult(
            step_number=step_number,
            action=action,
            success=True,
            current_url=self._current_url,
            message=f"Offline adapter navigated to {url}",
        )
        self._history.append(res)
        return res

    def click(self, selector: str, step_number: int) -> ActionResult:
        action = BrowserAction(ActionType.CLICK, selector=selector)
        res = ActionResult(
            step_number=step_number,
            action=action,
            success=True,
            current_url=self._current_url,
            message=f"Offline adapter clicked '{selector}'",
        )
        self._history.append(res)
        return res

    def extract(self, selector: Optional[str], step_number: int) -> ActionResult:
        action = BrowserAction(ActionType.EXTRACT, selector=selector)
        res = ActionResult(
            step_number=step_number,
            action=action,
            success=True,
            current_url=self._current_url,
            message=f"Offline adapter extracted from '{selector or 'page'}'",
        )
        self._history.append(res)
        return res

    @property
    def current_url(self) -> Optional[str]:
        return self._current_url

    @property
    def execution_history(self) -> List[ActionResult]:
        return list(self._history)


def extract_origin(url: str) -> str:
    """Extract and normalize lowercase hostname from URL."""
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    normalized = url.strip()
    if "://" not in normalized:
        normalized = f"http://{normalized}"
    parsed = urllib.parse.urlsplit(normalized)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"Unable to extract hostname from '{url}'")
    return hostname.lower()


class GuardedBrowserService:
    """Intermediary enforcing origin boundaries and step budget on top of any BrowserServiceAdapter."""

    def __init__(
        self,
        adapter: BrowserServiceAdapter,
        allowed_origins: Sequence[str],
        step_budget: int = 3,
    ) -> None:
        if step_budget < 0:
            raise ValueError("step_budget must be non-negative")
        self.adapter = adapter
        self.allowed_origins: Set[str] = {
            extract_origin(o) for o in allowed_origins if o.strip()
        }
        if not self.allowed_origins:
            raise ValueError("Must provide at least one valid allowed origin")
        self.step_budget = step_budget
        self.step_count = 0

    def validate_action(self, action: BrowserAction) -> None:
        """Validate action rules before allowing execution on the underlying adapter."""
        # Check budget limit
        if self.step_count >= self.step_budget:
            raise StepBudgetExceededError(
                attempted_step=self.step_count + 1,
                budget=self.step_budget,
                action=action,
            )

        # Check origin limit
        if action.action_type == ActionType.NAVIGATE:
            if not action.url:
                raise ValueError("URL cannot be empty for navigate action")
            origin = extract_origin(action.url)
            if origin not in self.allowed_origins:
                raise DisallowedOriginError(
                    url=action.url, origin=origin, allowed_origins=self.allowed_origins
                )

    def execute(self, action: BrowserAction) -> ActionResult:
        """Validate and dispatch action to adapter, incrementing step count upon success."""
        # Pre-execution validation invariant: invalid actions fail BEFORE touching the adapter
        self.validate_action(action)
        self.step_count += 1

        if action.action_type == ActionType.NAVIGATE:
            return self.adapter.navigate(action.url or "", self.step_count)
        elif action.action_type == ActionType.CLICK:
            return self.adapter.click(action.selector or "", self.step_count)
        elif action.action_type == ActionType.EXTRACT:
            return self.adapter.extract(action.selector, self.step_count)
        else:
            raise NotImplementedError(f"Unsupported action: {action.action_type}")


def run_concept_demo() -> None:
    """Demonstrate the guarded offline adapter workflow."""
    print("=" * 70)
    print("Browser-Action Guard — Offline Service Adapter Demo (Lesson 15)")
    print("=" * 70)

    adapter = OfflineLocalBrowserAdapter()
    service = GuardedBrowserService(
        adapter=adapter,
        allowed_origins=["example.invalid"],
        step_budget=3,
    )

    print(f"Allowed Origin: {service.allowed_origins}")
    print(f"Step Budget:    {service.step_budget}\n")

    steps = [
        BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/home"),
        BrowserAction(ActionType.CLICK, selector="#login-btn"),
        BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/dashboard"),
        BrowserAction(ActionType.EXTRACT, selector="#stats"),
    ]

    for idx, act in enumerate(steps, start=1):
        try:
            print(f"[Attempt {idx}] Action: {act.action_type.value} (target={act.url or act.selector})")
            res = service.execute(act)
            print(f"  -> SUCCESS: Step {res.step_number} completed: {res.message}")
        except BrowserGuardError as err:
            print(f"  -> BLOCKED by guardrail: {err}")

    # Demonstrate origin rejection with a fresh service instance
    print("\n[Origin Policy Demonstration]")
    fresh_service = GuardedBrowserService(
        adapter=OfflineLocalBrowserAdapter(),
        allowed_origins=["example.invalid"],
        step_budget=3,
    )
    try:
        rogue = BrowserAction(ActionType.NAVIGATE, url="https://malicious.invalid/leak")
        print(f"Attempting navigation to: {rogue.url}")
        fresh_service.execute(rogue)
    except DisallowedOriginError as err:
        print(f"  -> BLOCKED BEFORE EXECUTION: {err}")

    print("\n--- Identified Real-Service Behaviors NOT Established by Mock ---")
    for i, b in enumerate(REAL_SERVICE_UNSUPPORTED_BEHAVIORS, start=1):
        print(f"{i}. {b}")


if __name__ == "__main__":
    run_concept_demo()
