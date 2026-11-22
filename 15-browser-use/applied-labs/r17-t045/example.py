"""Applied Lab: Browser Action Validation with Origin and Step Guards (R17-T045)

Lesson Alignment:
15-browser-use (Computer Use Agents: Safety Guardrails, Scope & Step Budgets)

Contract & Goals:
- Validate proposed browser-action sequences against allowed origins and max step budgets.
- Navigation to allowed `example.invalid` passes.
- Navigation to disallowed origins is rejected before execution with OriginValidationError.
- A 4th step fails under a 3-step budget with StepBudgetExceededError.
- Refactor teaching example: decompose validation into dedicated `OriginGuard` and `StepBudgetGuard` components.
- Demonstrate before/after equivalence on test fixtures.
- Zero external dependencies: pure Python 3 standard library.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse


class BrowserActionValidationError(Exception):
    """Base exception for browser action safety and budget validation failures."""
    pass


class OriginValidationError(BrowserActionValidationError):
    """Raised when an action attempts navigation to an unapproved origin/domain."""

    def __init__(self, url: str, origin: str, allowed_origins: Set[str]):
        self.url = url
        self.origin = origin
        self.allowed_origins = allowed_origins
        super().__init__(
            f"Navigation rejected: origin '{origin}' extracted from '{url}' "
            f"is not in the allowed origins set: {sorted(list(allowed_origins))}."
        )


class StepBudgetExceededError(BrowserActionValidationError):
    """Raised when proposed action sequence exceeds maximum allowed step budget."""

    def __init__(self, actual_steps: int, budget_limit: int):
        self.actual_steps = actual_steps
        self.budget_limit = budget_limit
        super().__init__(
            f"Step budget exceeded: action sequence contains {actual_steps} steps, "
            f"which exceeds the maximum budget limit of {budget_limit} steps."
        )


@dataclass(frozen=True)
class BrowserAction:
    """Represents a discrete browser action planned by an agent."""
    action_type: str  # e.g., 'navigate', 'click', 'input', 'scroll', 'extract'
    target: str       # URL for navigate, CSS/XPath selector or query for interaction
    value: Optional[str] = None
    step_id: Optional[int] = None

    def __repr__(self) -> str:
        if self.value:
            return f"BrowserAction({self.action_type}: {self.target!r}, value={self.value!r})"
        return f"BrowserAction({self.action_type}: {self.target!r})"


def normalize_origin(url_or_domain: str) -> str:
    """Extracts lowercase normalized host/domain from a URL or raw domain string."""
    candidate = url_or_domain.strip().lower()
    if not candidate.startswith(("http://", "https://")):
        candidate = "https://" + candidate
    parsed = urlparse(candidate)
    return parsed.hostname or url_or_domain.strip().lower()


# ============================================================================
# BEFORE REFACTORING: Monolithic Validator
# ============================================================================

class MonolithicBrowserActionValidator:
    """Monolithic validator combining origin checking and step budgeting in a single class."""

    def __init__(self, allowed_origins: Set[str], max_steps: int = 3):
        self.allowed_origins: Set[str] = {normalize_origin(o) for o in allowed_origins}
        self.max_steps: int = max_steps

    def validate(self, actions: List[Union[BrowserAction, Dict[str, Any]]]) -> bool:
        """Validates all actions against origin policy and step budget simultaneously."""
        # 1. Step budget check
        step_count = len(actions)
        if step_count > self.max_steps:
            raise StepBudgetExceededError(actual_steps=step_count, budget_limit=self.max_steps)

        # 2. Origin check for navigate actions
        for act in actions:
            action_type, target = self._extract_action(act)
            if action_type.lower() == "navigate":
                origin = normalize_origin(target)
                if origin not in self.allowed_origins:
                    raise OriginValidationError(
                        url=target,
                        origin=origin,
                        allowed_origins=self.allowed_origins,
                    )
        return True

    def _extract_action(self, act: Union[BrowserAction, Dict[str, Any]]) -> Tuple[str, str]:
        if isinstance(act, BrowserAction):
            return act.action_type, act.target
        elif isinstance(act, dict):
            return act.get("action_type", act.get("action", "")), act.get("target", act.get("url", ""))
        raise ValueError(f"Unsupported action format: {type(act)}")


# ============================================================================
# AFTER REFACTORING: Dedicated Decomposed Components
# ============================================================================

class OriginGuard:
    """Dedicated single-responsibility guard validating navigation URL origins."""

    def __init__(self, allowed_origins: Set[str]):
        self.allowed_origins: Set[str] = {normalize_origin(o) for o in allowed_origins}

    def check_url(self, url: str) -> bool:
        """Checks if a URL belongs to the allowed origins. Raises OriginValidationError if not."""
        origin = normalize_origin(url)
        if origin not in self.allowed_origins:
            raise OriginValidationError(url=url, origin=origin, allowed_origins=self.allowed_origins)
        return True

    def validate(self, actions: List[Union[BrowserAction, Dict[str, Any]]]) -> bool:
        """Validates that all navigation actions target an approved origin."""
        for act in actions:
            action_type, target = self._extract(act)
            if action_type.lower() == "navigate":
                self.check_url(target)
        return True

    def _extract(self, act: Union[BrowserAction, Dict[str, Any]]) -> Tuple[str, str]:
        if isinstance(act, BrowserAction):
            return act.action_type, act.target
        elif isinstance(act, dict):
            return act.get("action_type", act.get("action", "")), act.get("target", act.get("url", ""))
        raise ValueError(f"Unsupported action format: {type(act)}")


class StepBudgetGuard:
    """Dedicated single-responsibility guard enforcing maximum step budget policies."""

    def __init__(self, max_steps: int = 3):
        if max_steps < 0:
            raise ValueError(f"max_steps must be non-negative, got {max_steps}")
        self.max_steps: int = max_steps

    def validate(self, actions: List[Any]) -> bool:
        """Validates that action count does not exceed max_steps."""
        step_count = len(actions)
        if step_count > self.max_steps:
            raise StepBudgetExceededError(actual_steps=step_count, budget_limit=self.max_steps)
        return True


class DecomposedBrowserActionValidator:
    """Composite validator coordinating dedicated OriginGuard and StepBudgetGuard components."""

    def __init__(self, origin_guard: OriginGuard, budget_guard: StepBudgetGuard):
        self.origin_guard: OriginGuard = origin_guard
        self.budget_guard: StepBudgetGuard = budget_guard

    @property
    def allowed_origins(self) -> Set[str]:
        return self.origin_guard.allowed_origins

    @property
    def max_steps(self) -> int:
        return self.budget_guard.max_steps

    def validate(self, actions: List[Union[BrowserAction, Dict[str, Any]]]) -> bool:
        """Runs budget and origin guards in deterministic order."""
        # 1. Enforce step budget first
        self.budget_guard.validate(actions)
        # 2. Enforce origin guard
        self.origin_guard.validate(actions)
        return True


def compare_validators(
    actions: List[Union[BrowserAction, Dict[str, Any]]],
    allowed_origins: Set[str],
    max_steps: int = 3,
) -> Dict[str, Any]:
    """Compares validation outcomes between monolithic (before) and decomposed (after) validators."""
    monolithic = MonolithicBrowserActionValidator(allowed_origins=allowed_origins, max_steps=max_steps)
    decomposed = DecomposedBrowserActionValidator(
        origin_guard=OriginGuard(allowed_origins=allowed_origins),
        budget_guard=StepBudgetGuard(max_steps=max_steps),
    )

    mono_result: Dict[str, Any] = {"passed": False, "error_type": None, "error_message": None}
    decomp_result: Dict[str, Any] = {"passed": False, "error_type": None, "error_message": None}

    try:
        monolithic.validate(actions)
        mono_result["passed"] = True
    except Exception as err:
        mono_result["error_type"] = type(err).__name__
        mono_result["error_message"] = str(err)

    try:
        decomposed.validate(actions)
        decomp_result["passed"] = True
    except Exception as err:
        decomp_result["error_type"] = type(err).__name__
        decomp_result["error_message"] = str(err)

    equivalent = (
        mono_result["passed"] == decomp_result["passed"]
        and mono_result["error_type"] == decomp_result["error_type"]
    )

    return {
        "equivalent": equivalent,
        "monolithic": mono_result,
        "decomposed": decomp_result,
    }


def main():
    print("=== Browser Action Validation with Origin and Step Guards (R17-T045) ===\n")

    allowed = {"example.invalid"}
    budget = 3

    print(f"Policy Configuration: Allowed Origins = {allowed}, Step Budget = {budget}\n")

    # Fixture 1: Valid 3-step sequence navigating to example.invalid
    f1 = [
        BrowserAction("navigate", "https://example.invalid/search"),
        BrowserAction("click", "#search-button"),
        BrowserAction("extract", ".results"),
    ]
    comp1 = compare_validators(f1, allowed, budget)
    print("1. Canonical Valid Sequence (3 steps to example.invalid):")
    print(f"   Monolithic Result : Passed={comp1['monolithic']['passed']}")
    print(f"   Decomposed Result : Passed={comp1['decomposed']['passed']}")
    print(f"   Equivalent        : {comp1['equivalent']}\n")

    # Fixture 2: Step budget exceeded (4th step fails under 3-step budget)
    f2 = [
        BrowserAction("navigate", "https://example.invalid"),
        BrowserAction("click", "#btn1"),
        BrowserAction("click", "#btn2"),
        BrowserAction("click", "#btn3"),
    ]
    comp2 = compare_validators(f2, allowed, budget)
    print("2. Step Budget Exceeded Sequence (4 steps under budget of 3):")
    print(f"   Monolithic Error  : {comp2['monolithic']['error_type']}")
    print(f"   Decomposed Error  : {comp2['decomposed']['error_type']}")
    print(f"   Equivalent        : {comp2['equivalent']}\n")

    # Fixture 3: Disallowed origin navigation rejected before execution
    f3 = [
        BrowserAction("navigate", "https://untrusted-site.com/login"),
        BrowserAction("click", "#submit"),
    ]
    comp3 = compare_validators(f3, allowed, budget)
    print("3. Disallowed Origin Navigation (https://untrusted-site.com):")
    print(f"   Monolithic Error  : {comp3['monolithic']['error_type']}")
    print(f"   Decomposed Error  : {comp3['decomposed']['error_type']}")
    print(f"   Equivalent        : {comp3['equivalent']}\n")

    print("All comparative demonstration fixtures executed successfully.")


if __name__ == "__main__":
    main()

