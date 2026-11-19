"""Agent-Component Routing — Invariant and State Trace.

Lesson 02: Explore AI Agent Frameworks
Task: R17-T024

This module provides an auditable agent component router with deterministic state tracing.
Routing Rules:
1. 'help' intent routes to 'support' handler.
2. 'calculate' intent routes to 'calculator' handler.
3. 'unknown' intent routes to 'fallback' handler.
4. Ambiguous intents follow documented priority (help > calculate) and log the chosen rule.
5. Intermediate states are recorded at every step and mathematically linked to final output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class StepPhase(str, Enum):
    """Lifecycle phases for intermediate routing execution."""
    RECEIVED = "RECEIVED"
    ANALYZED = "ANALYZED"
    ROUTED = "ROUTED"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"


class IntentType(str, Enum):
    """Supported request intents."""
    HELP = "help"
    CALCULATE = "calculate"
    UNKNOWN = "unknown"


class HandlerName(str, Enum):
    """Named component handlers."""
    SUPPORT = "support"
    CALCULATOR = "calculator"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class RoutingRule:
    """Explicit routing policy rule with priority ordering (lower number = higher priority)."""
    rule_id: str
    intent: IntentType
    target_handler: HandlerName
    priority: int
    description: str


# Documented priority ordering: HELP (1) > CALCULATE (2) > UNKNOWN (99)
ROUTING_POLICIES: List[RoutingRule] = [
    RoutingRule(
        rule_id="RULE_HELP_PRIORITY",
        intent=IntentType.HELP,
        target_handler=HandlerName.SUPPORT,
        priority=1,
        description="Directs assistance or help queries to support handler with top priority.",
    ),
    RoutingRule(
        rule_id="RULE_CALCULATE_PRIORITY",
        intent=IntentType.CALCULATE,
        target_handler=HandlerName.CALCULATOR,
        priority=2,
        description="Directs computational or math queries to calculator handler.",
    ),
    RoutingRule(
        rule_id="RULE_FALLBACK_DEFAULT",
        intent=IntentType.UNKNOWN,
        target_handler=HandlerName.FALLBACK,
        priority=99,
        description="Directs unrecognized or unclassifiable queries to fallback handler.",
    ),
]


@dataclass(frozen=True)
class RoutingDecision:
    """Auditable record documenting how and why a routing decision was made."""
    request_id: str
    raw_input: str
    detected_intents: Tuple[IntentType, ...]
    chosen_rule_id: str
    chosen_intent: IntentType
    target_handler: HandlerName
    is_ambiguous: bool
    rationale: str
    timestamp: str


@dataclass(frozen=True)
class IntermediateState:
    """Immutable state snapshot captured after each lifecycle step."""
    step_number: int
    phase: StepPhase
    state_payload: Dict[str, Any]
    timestamp: str


@dataclass(frozen=True)
class RouterExecutionResult:
    """Final output coupled with the auditable intermediate state trace."""
    request_id: str
    raw_input: str
    handler_name: HandlerName
    handler_response: str
    decision: RoutingDecision
    state_trace: List[IntermediateState]


class StateTraceInvariantError(Exception):
    """Raised when an intermediate state trace violates causal invariants with final output."""


class AgentComponentRouter:
    """Deterministic agent-component router with invariant enforcement and step-by-step state tracing."""

    def __init__(self) -> None:
        self.rules: List[RoutingRule] = sorted(ROUTING_POLICIES, key=lambda r: r.priority)
        self.handlers: Dict[HandlerName, Callable[[str], str]] = {
            HandlerName.SUPPORT: self._handle_support,
            HandlerName.CALCULATOR: self._handle_calculator,
            HandlerName.FALLBACK: self._handle_fallback,
        }

    @staticmethod
    def _handle_support(query: str) -> str:
        return f"[SupportHandler] Processed support inquiry for: '{query}'"

    @staticmethod
    def _handle_calculator(query: str) -> str:
        return f"[CalculatorHandler] Processed computational query for: '{query}'"

    @staticmethod
    def _handle_fallback(query: str) -> str:
        return f"[FallbackHandler] No specialized handler found for: '{query}'. Delegated to general fallback."

    def detect_intents(self, query: str) -> List[IntentType]:
        """Analyze query string to identify all matching intent signals."""
        normalized = query.lower()
        detected: List[IntentType] = []

        help_pattern = re.compile(r"\b(help|support|assist|guide|troubleshoot)\b")
        calc_pattern = re.compile(r"\b(calculate|math|compute|sum|add|multiply|divide|calc)\b")

        if help_pattern.search(normalized):
            detected.append(IntentType.HELP)
        if calc_pattern.search(normalized):
            detected.append(IntentType.CALCULATE)

        if not detected:
            detected.append(IntentType.UNKNOWN)

        return detected

    def resolve_routing(self, request_id: str, query: str, detected: List[IntentType]) -> RoutingDecision:
        """Apply documented priority rules to resolve ambiguous or single intents."""
        is_ambiguous = len(detected) > 1

        # Match against policy in strict priority order
        chosen_rule: Optional[RoutingRule] = None
        for rule in self.rules:
            if rule.intent in detected:
                chosen_rule = rule
                break

        if chosen_rule is None:
            chosen_rule = next(r for r in self.rules if r.intent == IntentType.UNKNOWN)

        rationale = (
            f"Ambiguous intent detected ({[i.value for i in detected]}). Applied highest priority rule: {chosen_rule.rule_id}"
            if is_ambiguous
            else f"Single intent matched: {chosen_rule.intent.value} -> {chosen_rule.target_handler.value}"
        )

        return RoutingDecision(
            request_id=request_id,
            raw_input=query,
            detected_intents=tuple(detected),
            chosen_rule_id=chosen_rule.rule_id,
            chosen_intent=chosen_rule.intent,
            target_handler=chosen_rule.target_handler,
            is_ambiguous=is_ambiguous,
            rationale=rationale,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def route_and_execute(self, query: str, request_id: Optional[str] = None) -> RouterExecutionResult:
        """Route request through the multi-step lifecycle, capturing intermediate states."""
        req_id = request_id or f"req-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        trace: List[IntermediateState] = []
        step_counter = 1

        def append_state(phase: StepPhase, payload: Dict[str, Any]) -> None:
            nonlocal step_counter
            trace.append(
                IntermediateState(
                    step_number=step_counter,
                    phase=phase,
                    state_payload=payload,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
            step_counter += 1

        # Step 1: Request Received
        append_state(StepPhase.RECEIVED, {"request_id": req_id, "raw_input": query})

        # Step 2: Intent Analysis
        detected = self.detect_intents(query)
        append_state(
            StepPhase.ANALYZED,
            {"detected_intents": [i.value for i in detected], "count": len(detected)},
        )

        # Step 3: Decision & Policy Resolution
        decision = self.resolve_routing(req_id, query, detected)
        append_state(
            StepPhase.ROUTED,
            {
                "chosen_rule_id": decision.chosen_rule_id,
                "chosen_intent": decision.chosen_intent.value,
                "target_handler": decision.target_handler.value,
                "is_ambiguous": decision.is_ambiguous,
            },
        )

        # Step 4: Dispatch to Selected Component
        handler = self.handlers[decision.target_handler]
        append_state(
            StepPhase.DISPATCHED,
            {"dispatched_to": decision.target_handler.value},
        )

        # Step 5: Execution Completion
        response = handler(query)
        append_state(
            StepPhase.COMPLETED,
            {
                "handler_name": decision.target_handler.value,
                "response_length": len(response),
            },
        )

        result = RouterExecutionResult(
            request_id=req_id,
            raw_input=query,
            handler_name=decision.target_handler,
            handler_response=response,
            decision=decision,
            state_trace=trace,
        )

        # Invariant Verification: Guarantee state trace matches final output
        self.verify_state_trace_invariants(result)
        return result

    @staticmethod
    def verify_state_trace_invariants(result: RouterExecutionResult) -> None:
        """Formally test invariants connecting intermediate state trace to final output.

        Invariants:
        1. Exact Phase Sequence: Trace must contain all 5 lifecycle phases in exact sequential order.
        2. Routing-to-Dispatch Parity: Target handler decided at ROUTED must match DISPATCHED and COMPLETED.
        3. Handler Output Parity: Final result handler_name must strictly match COMPLETED state.
        4. Priority Invariant: If ambiguous intents include 'help', chosen rule must be RULE_HELP_PRIORITY.
        """
        trace = result.state_trace
        expected_phases = [
            StepPhase.RECEIVED,
            StepPhase.ANALYZED,
            StepPhase.ROUTED,
            StepPhase.DISPATCHED,
            StepPhase.COMPLETED,
        ]

        actual_phases = [s.phase for s in trace]
        if actual_phases != expected_phases:
            raise StateTraceInvariantError(
                f"Phase sequence invariant broken: expected {expected_phases}, got {actual_phases}"
            )

        routed_handler = trace[2].state_payload["target_handler"]
        dispatched_handler = trace[3].state_payload["dispatched_to"]
        completed_handler = trace[4].state_payload["handler_name"]

        if not (routed_handler == dispatched_handler == completed_handler == result.handler_name.value):
            raise StateTraceInvariantError(
                f"Handler parity invariant broken across state trace: "
                f"routed={routed_handler}, dispatched={dispatched_handler}, "
                f"completed={completed_handler}, result={result.handler_name.value}"
            )

        if result.decision.is_ambiguous:
            intents = result.decision.detected_intents
            if IntentType.HELP in intents and result.decision.target_handler != HandlerName.SUPPORT:
                raise StateTraceInvariantError(
                    "Priority policy broken: 'help' was detected but handler was not 'support'"
                )


def run_concept_demo() -> None:
    """Run interactive demonstration of router and state trace."""
    print("=" * 70)
    print("Agent-Component Routing & State Trace Demo (Lesson 02)")
    print("=" * 70)

    router = AgentComponentRouter()

    test_queries = [
        ("I need help with my billing account", "Single Intent -> help"),
        ("Please calculate 45 * 12", "Single Intent -> calculate"),
        ("What is the weather outside today?", "Unrecognized Intent -> unknown"),
        ("Can you help me calculate monthly revenue?", "Ambiguous Intent -> help + calculate"),
    ]

    for query, description in test_queries:
        print(f"\n--- Query: '{query}' ({description}) ---")
        res = router.route_and_execute(query)
        print(f"Chosen Handler: {res.handler_name.value}")
        print(f"Chosen Rule:    {res.decision.chosen_rule_id}")
        print(f"Ambiguous:      {res.decision.is_ambiguous}")
        print(f"Rationale:      {res.decision.rationale}")
        print(f"Response:       {res.handler_response}")
        print("Captured State Trace:")
        for state in res.state_trace:
            print(f"  Step {state.step_number} [{state.phase.value}]: {state.state_payload}")

    print("\nDemonstration completed with all state invariants verified.")


if __name__ == "__main__":
    run_concept_demo()
