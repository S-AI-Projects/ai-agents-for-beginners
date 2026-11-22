"""Applied Lab: Routing Agent with Offline Service Adapter (R17-T043)

Lesson Alignment:
03-agentic-design-patterns (Routing & Classification Pattern)

Contract & Goals:
- Route incoming requests to named handlers:
    * 'help' -> 'support'
    * 'calculate' -> 'calculator'
    * 'unknown' -> 'fallback'
- Handle ambiguous intents following documented priority:
    Priority: 'support' > 'calculator' > 'fallback'
- Record an auditable, structured decision log for every routing event.
- Offline service adapter:
    * Abstract callable adapter protocol (`ClassifierAdapterProtocol`).
    * Deterministic local mock adapter (`DeterministicMockClassifierAdapter`).
- Document explicitly which real-service behaviors the mock does not simulate
  (e.g., network latency, token limits, probabilistic LLM drift).
- Zero external dependencies: pure Python 3 standard library.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, Callable


# Explicit documentation of real-service behaviors NOT simulated by the local mock adapter
UNSIMULATED_REAL_SERVICE_BEHAVIORS: Dict[str, str] = {
    "network_latency": (
        "The mock executes synchronously in-memory with sub-millisecond execution, "
        "omitting network round-trip delays, TCP handshakes, TLS negotiation, and DNS resolution."
    ),
    "token_rate_limits": (
        "The mock does not enforce API rate limits (TPM - Tokens Per Minute, RPM - Requests Per Minute), "
        "HTTP 429 throttling headers, or backoff retry behaviors."
    ),
    "probabilistic_llm_drift": (
        "The mock utilizes deterministic heuristic pattern matching. Real LLMs with non-zero temperature "
        "exhibit stochastic output variation, prompt injection vulnerabilities, and semantic drift across model checkpoints."
    ),
    "context_window_and_truncation": (
        "The mock does not simulate token context limits (e.g., 8k/32k/128k context windows), "
        "token serialization costs, or payload size truncation errors."
    ),
    "authentication_and_authorization": (
        "The mock operates without Entra ID / API key credential validation, token expiry, "
        "or multi-tenant IAM authorization boundaries."
    ),
    "service_availability_and_transient_failures": (
        "The mock does not simulate partial outages, HTTP 5xx gateway errors, connection drops, "
        "or retry jitter."
    ),
}


@dataclass(frozen=True)
class ClassificationResult:
    """Represents the output from an intent classification adapter."""
    raw_query: str
    detected_intents: List[str]
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""


@runtime_checkable
class ClassifierAdapterProtocol(Protocol):
    """Abstract callable adapter protocol for request intent classification.
    
    Implementations must be callable with a string query, returning a ClassificationResult.
    """
    def __call__(self, query: str) -> ClassificationResult:
        """Callable interface to classify input query."""
        ...

    def classify(self, query: str) -> ClassificationResult:
        """Named method interface to classify input query."""
        ...


class DeterministicMockClassifierAdapter:
    """Deterministic, offline local mock classification adapter.

    Uses deterministic rule matching and keywords to simulate an LLM classifier
    without network, GPU, API key, or probabilistic drift overhead.
    """

    SUPPORT_KEYWORDS = {
        "help", "support", "assist", "assistance", "trouble", "issue", "problem",
        "human", "agent", "contact", "guide", "manual", "customer service"
    }

    CALCULATOR_KEYWORDS = {
        "calculate", "calc", "calculator", "math", "add", "sum", "subtract",
        "multiply", "divide", "compute", "equation", "formula", "arithmetic"
    }

    def __call__(self, query: str) -> ClassificationResult:
        return self.classify(query)

    def classify(self, query: str) -> ClassificationResult:
        normalized = query.lower()
        words = set(re.findall(r"\b[a-z0-9_]+\b", normalized))

        detected: List[str] = []
        scores: Dict[str, float] = {}

        # Support check
        support_matches = words.intersection(self.SUPPORT_KEYWORDS)
        if support_matches or "how do i" in normalized or "help" in normalized:
            detected.append("support")
            scores["support"] = 0.95 if support_matches else 0.80

        # Calculator check
        calc_matches = words.intersection(self.CALCULATOR_KEYWORDS)
        # Check arithmetic symbols
        has_arithmetic_expr = bool(re.search(r"\d+\s*[\+\-\*\/\^]\s*\d+", normalized))
        if calc_matches or has_arithmetic_expr:
            detected.append("calculator")
            scores["calculator"] = 0.95 if calc_matches else 0.85

        if not detected:
            detected.append("unknown")
            scores["unknown"] = 1.0
            rationale = "No recognized keywords or patterns detected; labeled as unknown."
        elif len(detected) > 1:
            rationale = f"Multiple intent signals detected: {detected}."
        else:
            rationale = f"Single intent matched: {detected[0]}."

        return ClassificationResult(
            raw_query=query,
            detected_intents=detected,
            confidence_scores=scores,
            rationale=rationale,
        )


@dataclass(frozen=True)
class HandlerResponse:
    """Output generated by a routed intent handler."""
    handler_name: str
    message: str
    status: str = "SUCCESS"
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionLogRecord:
    """Auditable record documenting a routing decision."""
    decision_id: int
    timestamp_iso: str
    raw_query: str
    detected_intents: List[str]
    selected_handler: str
    priority_applied: bool
    decision_reason: str
    confidence: float
    response_summary: str


class IntentRouter:
    """Agentic Router implementing deterministic classification, priority resolution,
    handler dispatch, and structured decision auditing.
    """

    # Documented priority ordering: support > calculator > fallback
    PRIORITY_ORDER: List[str] = ["support", "calculator", "fallback"]

    def __init__(
        self,
        classifier: Optional[ClassifierAdapterProtocol] = None,
        custom_handlers: Optional[Dict[str, Callable[[str], HandlerResponse]]] = None,
    ):
        self.classifier: ClassifierAdapterProtocol = classifier or DeterministicMockClassifierAdapter()
        self.handlers: Dict[str, Callable[[str], HandlerResponse]] = {
            "support": self._default_support_handler,
            "calculator": self._default_calculator_handler,
            "fallback": self._default_fallback_handler,
        }
        if custom_handlers:
            self.handlers.update(custom_handlers)

        self._decision_log: List[DecisionLogRecord] = []
        self._next_decision_id: int = 1

    @property
    def decision_log(self) -> List[DecisionLogRecord]:
        """Read-only access to audit trail of routing decisions."""
        return list(self._decision_log)

    def route(self, query: str) -> HandlerResponse:
        """Classifies, resolves ambiguities by priority, routes to handler, and logs the decision."""
        classification = self.classifier(query)
        detected = classification.detected_intents

        priority_applied = False
        decision_reason: str

        if "unknown" in detected or not detected:
            selected_handler = "fallback"
            decision_reason = "Unrecognized input intent; routed to fallback handler."
            confidence = classification.confidence_scores.get("unknown", 1.0)

        elif len(detected) == 1:
            target_intent = detected[0]
            if target_intent == "help" or target_intent == "support":
                selected_handler = "support"
                decision_reason = "Direct intent match for support/help."
            elif target_intent == "calculate" or target_intent == "calculator":
                selected_handler = "calculator"
                decision_reason = "Direct intent match for calculate/calculator."
            else:
                selected_handler = "fallback"
                decision_reason = f"Unmapped intent '{target_intent}'; routed to fallback."
            confidence = classification.confidence_scores.get(target_intent, 0.9)

        else:
            # Ambiguous intent: multiple signals detected
            # Resolve using documented priority order: support > calculator > fallback
            priority_applied = True
            resolved = None
            for candidate in self.PRIORITY_ORDER:
                if candidate in detected or (candidate == "support" and "help" in detected) or (candidate == "calculator" and "calculate" in detected):
                    resolved = candidate
                    break

            selected_handler = resolved if resolved else "fallback"
            decision_reason = (
                f"Ambiguous intents {detected} resolved to '{selected_handler}' "
                f"via documented priority order ({' > '.join(self.PRIORITY_ORDER)})."
            )
            confidence = classification.confidence_scores.get(selected_handler, 0.85)

        # Dispatch to handler
        handler_fn = self.handlers.get(selected_handler, self._default_fallback_handler)
        response = handler_fn(query)

        # Audit decision log entry
        log_entry = DecisionLogRecord(
            decision_id=self._next_decision_id,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            raw_query=query,
            detected_intents=detected,
            selected_handler=selected_handler,
            priority_applied=priority_applied,
            decision_reason=decision_reason,
            confidence=confidence,
            response_summary=response.message,
        )
        self._decision_log.append(log_entry)
        self._next_decision_id += 1

        return response

    # Default Named Handlers
    def _default_support_handler(self, query: str) -> HandlerResponse:
        return HandlerResponse(
            handler_name="support",
            message=f"SupportAgent: Connected to customer support for request: '{query}'. How can we assist you?",
            payload={"service": "customer_support", "query": query},
        )

    def _default_calculator_handler(self, query: str) -> HandlerResponse:
        # Simple local computation if pattern matches
        expr_match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", query)
        calc_result = None
        if expr_match:
            try:
                a, op, b = float(expr_match.group(1)), expr_match.group(2), float(expr_match.group(3))
                if op == "+":
                    calc_result = a + b
                elif op == "-":
                    calc_result = a - b
                elif op == "*":
                    calc_result = a * b
                elif op == "/":
                    calc_result = a / b if b != 0 else "Error: Division by zero"
            except Exception:
                calc_result = None

        msg = f"CalculatorAgent: Processed calculation query: '{query}'."
        if calc_result is not None:
            msg += f" Result: {calc_result}"

        return HandlerResponse(
            handler_name="calculator",
            message=msg,
            payload={"service": "calculator", "result": calc_result},
        )

    def _default_fallback_handler(self, query: str) -> HandlerResponse:
        return HandlerResponse(
            handler_name="fallback",
            message=(
                f"FallbackAgent: We could not determine an exact handler for: '{query}'. "
                "Available services: 'support' (help/troubleshooting) and 'calculator' (math/computations)."
            ),
            payload={"service": "fallback", "query": query},
        )


def main():
    print("=== Multi-Agent Routing Agent with Offline Adapter (R17-T043) ===\n")

    router = IntentRouter()

    test_queries = [
        "Help me reset my password",
        "Can you calculate 25 * 4?",
        "Help me calculate my monthly invoice cost please",
        "Tell me a joke about bananas",
    ]

    for q in test_queries:
        print(f"User Query: \"{q}\"")
        resp = router.route(q)
        print(f"  Handler : {resp.handler_name}")
        print(f"  Message : {resp.message}\n")

    print("--- Auditable Decision Log ---")
    for record in router.decision_log:
        print(
            f"[{record.decision_id}] Handler: {record.selected_handler:<10} | "
            f"Priority Applied: {str(record.priority_applied):<5} | "
            f"Reason: {record.decision_reason}"
        )

    print("\n--- Unsimulated Real-Service Behaviors ---")
    for key, desc in UNSIMULATED_REAL_SERVICE_BEHAVIORS.items():
        print(f"• {key}: {desc[:90]}...")


if __name__ == "__main__":
    main()
