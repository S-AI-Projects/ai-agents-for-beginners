"""Applied Lab: Request Router with Failure and Recovery (R17-T047)

Lesson Alignment:
02-explore-agentic-frameworks (Agent Routing, Framework Resilience & Error Recovery)

Contract & Goals:
- Route requests to named handlers:
    * 'help' -> 'support'
    * 'calculate' -> 'calculator'
    * 'unknown' -> 'fallback'
- Handle ambiguous intents following documented priority:
    Priority: 'support' > 'calculator' > 'fallback'
- Failure and recovery:
    * Exercise invalid / empty / malformed inputs (e.g., None, empty string, non-string).
    * Raise an explicit exception (InvalidRequestError).
    * Prove resilience: Subsequent valid requests route successfully without state corruption.
- Structured audit trail:
    * Records all routing events and error occurrences.
- Zero external dependencies: pure Python 3 standard library.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Callable, Dict, List, Optional, Union


class RouterError(Exception):
    """Base exception for routing errors."""
    pass


class InvalidRequestError(RouterError):
    """Raised when an incoming request is None, empty, whitespace-only, or malformed."""

    def __init__(self, message: str, raw_input: Any):
        self.raw_input = raw_input
        super().__init__(f"Invalid request rejected: {message} (received: {raw_input!r})")


@dataclass(frozen=True)
class RoutingResult:
    """Outcome of a successful routing and handler execution."""
    handler_name: str
    message: str
    detected_intents: List[str]
    priority_applied: bool
    status: str = "SUCCESS"
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouterAuditRecord:
    """Audit record capturing every routing invocation, including failures and recoveries."""
    record_id: int
    timestamp_iso: str
    raw_input: Any
    status: str            # 'SUCCESS' or 'ERROR'
    handler_name: Optional[str] = None
    detected_intents: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class FrameworkRouter:
    """Resilient agentic request router with input validation, priority resolution,
    and stateful failure recovery tracking.
    """

    # Documented priority ordering: support > calculator > fallback
    PRIORITY_ORDER: List[str] = ["support", "calculator", "fallback"]

    SUPPORT_KEYWORDS = {
        "help", "support", "assist", "assistance", "trouble", "issue", "problem",
        "human", "agent", "contact", "guide", "login", "password"
    }

    CALCULATOR_KEYWORDS = {
        "calculate", "calc", "calculator", "math", "add", "sum", "subtract",
        "multiply", "divide", "compute", "arithmetic", "equation"
    }

    def __init__(self, custom_handlers: Optional[Dict[str, Callable[[str], RoutingResult]]] = None):
        self.handlers: Dict[str, Callable[[str], RoutingResult]] = {
            "support": self._default_support_handler,
            "calculator": self._default_calculator_handler,
            "fallback": self._default_fallback_handler,
        }
        if custom_handlers:
            self.handlers.update(custom_handlers)

        self._audit_trail: List[RouterAuditRecord] = []
        self._record_counter: int = 1

    @property
    def audit_trail(self) -> List[RouterAuditRecord]:
        """Returns a defensive copy of the router audit trail."""
        return list(self._audit_trail)

    def _validate_input(self, raw_input: Any) -> str:
        """Validates incoming input for type, nullability, and non-emptiness.

        Raises:
            InvalidRequestError: If input is None, non-string, or blank.
        """
        if raw_input is None:
            raise InvalidRequestError("Request cannot be None", raw_input)
        if not isinstance(raw_input, str):
            raise InvalidRequestError(
                f"Request must be a string, got {type(raw_input).__name__}", raw_input
            )
        stripped = raw_input.strip()
        if not stripped:
            raise InvalidRequestError("Request cannot be empty or whitespace-only", raw_input)
        return stripped

    def classify_intents(self, text: str) -> List[str]:
        """Deterministically classifies text into candidate intents."""
        normalized = text.lower()
        words = set(re.findall(r"\b[a-z0-9_]+\b", normalized))
        detected: List[str] = []

        # Check support signals
        if words.intersection(self.SUPPORT_KEYWORDS) or "help" in normalized:
            detected.append("support")

        # Check calculator signals
        has_arithmetic_expr = bool(re.search(r"\d+\s*[\+\-\*\/\^]\s*\d+", normalized))
        if words.intersection(self.CALCULATOR_KEYWORDS) or has_arithmetic_expr:
            detected.append("calculator")

        if not detected:
            detected.append("unknown")

        return detected

    def route(self, raw_input: Any) -> RoutingResult:
        """Validates, classifies, and routes an incoming request to a named handler.

        Maintains router health and records both successful routes and caught errors.
        """
        record_id = self._record_counter
        self._record_counter += 1
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            valid_query = self._validate_input(raw_input)
        except InvalidRequestError as err:
            # Audit the failure event
            self._audit_trail.append(
                RouterAuditRecord(
                    record_id=record_id,
                    timestamp_iso=now_iso,
                    raw_input=raw_input,
                    status="ERROR",
                    error_type=type(err).__name__,
                    error_message=str(err),
                )
            )
            # Re-raise explicit exception to caller
            raise

        detected = self.classify_intents(valid_query)
        priority_applied = False

        if "unknown" in detected or not detected:
            selected_handler = "fallback"
        elif len(detected) == 1:
            selected_handler = detected[0]
        else:
            # Ambiguity: apply documented priority (support > calculator > fallback)
            priority_applied = True
            selected_handler = "support" if "support" in detected else "calculator"

        # Dispatch to handler
        handler_fn = self.handlers.get(selected_handler, self._default_fallback_handler)
        handler_res = handler_fn(valid_query)

        # Ensure routing metadata reflects actual classification and priority decision
        result = RoutingResult(
            handler_name=handler_res.handler_name,
            message=handler_res.message,
            detected_intents=detected,
            priority_applied=priority_applied,
            status=handler_res.status,
            payload=handler_res.payload,
        )

        # Audit successful routing event
        self._audit_trail.append(
            RouterAuditRecord(
                record_id=record_id,
                timestamp_iso=now_iso,
                raw_input=raw_input,
                status="SUCCESS",
                handler_name=selected_handler,
                detected_intents=detected,
            )
        )

        return result

    # Default Handlers
    def _default_support_handler(self, query: str) -> RoutingResult:
        return RoutingResult(
            handler_name="support",
            message=f"SupportAgent: Resolved customer support request for '{query}'.",
            detected_intents=["support"],
            priority_applied=False,
            payload={"domain": "customer_support", "query": query},
        )

    def _default_calculator_handler(self, query: str) -> RoutingResult:
        return RoutingResult(
            handler_name="calculator",
            message=f"CalculatorAgent: Computed result for calculation request '{query}'.",
            detected_intents=["calculator"],
            priority_applied=False,
            payload={"domain": "calculator", "query": query},
        )

    def _default_fallback_handler(self, query: str) -> RoutingResult:
        return RoutingResult(
            handler_name="fallback",
            message=f"FallbackAgent: Handled unrecognized query '{query}' with standard guidance.",
            detected_intents=["unknown"],
            priority_applied=False,
            payload={"domain": "fallback", "query": query},
        )


def demonstrate_failure_and_recovery() -> Dict[str, Any]:
    """Demonstrates failure on invalid input followed by immediate successful recovery."""
    router = FrameworkRouter()
    recovery_evidence: Dict[str, Any] = {
        "invalid_inputs_tested": [],
        "errors_caught": [],
        "subsequent_successful_routes": [],
        "router_operational_after_recovery": False,
    }

    # 1. Invalid input tests
    malformed_cases = [None, "", "   ", 12345, ["invalid", "list"]]

    for invalid in malformed_cases:
        try:
            router.route(invalid)
            assert False, f"Expected InvalidRequestError for input {invalid!r}"
        except InvalidRequestError as err:
            recovery_evidence["invalid_inputs_tested"].append(invalid)
            recovery_evidence["errors_caught"].append(type(err).__name__)

    # 2. Immediate recovery test: route valid request
    recovery_query = "Help me reset my login password"
    resp = router.route(recovery_query)
    assert resp.handler_name == "support"
    recovery_evidence["subsequent_successful_routes"].append({
        "query": recovery_query,
        "handler": resp.handler_name,
        "status": resp.status,
    })

    # 3. Second recovery test: route calculator request
    calc_query = "Calculate 15 * 4"
    resp_calc = router.route(calc_query)
    assert resp_calc.handler_name == "calculator"
    recovery_evidence["subsequent_successful_routes"].append({
        "query": calc_query,
        "handler": resp_calc.handler_name,
        "status": resp_calc.status,
    })

    recovery_evidence["router_operational_after_recovery"] = True
    return recovery_evidence


def main():
    print("=== Request Router with Failure and Recovery (R17-T047) ===\n")

    router = FrameworkRouter()

    # 1. Standard Routing Contract
    print("1. Standard Routing Contract:")
    canonical_cases = [
        ("I need help with login", "support"),
        ("Calculate 42 / 7", "calculator"),
        ("Tell me a random riddle", "fallback"),
        ("Help me calculate my travel budget", "support"),  # Ambiguous: resolved to support by priority
    ]

    for q, expected in canonical_cases:
        res = router.route(q)
        print(f"  Query: \"{q}\"")
        print(f"    -> Handler: {res.handler_name} (Expected: {expected})")
        print(f"    -> Message: {res.message}\n")

    # 2. Failure & Recovery Walkthrough
    print("2. Failure & Recovery Walkthrough:")
    invalid_input = "   "
    print(f"  Attempting invalid input: {invalid_input!r}")
    try:
        router.route(invalid_input)
    except InvalidRequestError as err:
        print(f"  [EXPECTED ERROR CAUGHT] {type(err).__name__}: {err}")

    print("\n  Executing immediate subsequent valid request to prove recovery...")
    recovery_input = "Help me recover my account"
    recovered_res = router.route(recovery_input)
    print(f"  [RECOVERY SUCCESS] Handler: {recovered_res.handler_name} | Message: {recovered_res.message}\n")

    # 3. Audit Trail Inspection
    print("3. Audit Trail Summary:")
    for record in router.audit_trail:
        if record.status == "SUCCESS":
            print(f"  [{record.record_id}] SUCCESS | Handler: {record.handler_name:<10} | Input: {record.raw_input!r}")
        else:
            print(f"  [{record.record_id}] ERROR   | Type: {record.error_type:<18} | Message: {record.error_message}")

    print("\nAll demonstrations executed successfully.")


if __name__ == "__main__":
    main()
