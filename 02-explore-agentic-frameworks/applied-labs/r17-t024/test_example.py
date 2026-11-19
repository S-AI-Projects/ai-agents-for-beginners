"""Unit tests for Agent-Component Routing — Invariant and State Trace.

Lesson 02: Explore AI Agent Frameworks
Task: R17-T024
Automated check: python3 -m unittest discover -s 02-explore-agentic-frameworks/applied-labs/r17-t024 -p "test_*.py" -v
"""

import unittest

from example import (
    AgentComponentRouter,
    HandlerName,
    IntentType,
    IntermediateState,
    RouterExecutionResult,
    StateTraceInvariantError,
    StepPhase,
)


class TestRoutingRules(unittest.TestCase):
    """Test deterministic routing rules for clear, single-intent queries."""

    def setUp(self) -> None:
        self.router = AgentComponentRouter()

    def test_help_routes_to_support(self) -> None:
        """'help' intent maps to 'support' handler."""
        result = self.router.route_and_execute("I need help with my account password")
        self.assertEqual(result.handler_name, HandlerName.SUPPORT)
        self.assertEqual(result.decision.chosen_intent, IntentType.HELP)
        self.assertEqual(result.decision.chosen_rule_id, "RULE_HELP_PRIORITY")
        self.assertFalse(result.decision.is_ambiguous)
        self.assertIn("[SupportHandler]", result.handler_response)

    def test_calculate_routes_to_calculator(self) -> None:
        """'calculate' intent maps to 'calculator' handler."""
        result = self.router.route_and_execute("Please calculate the compound interest for 5 years")
        self.assertEqual(result.handler_name, HandlerName.CALCULATOR)
        self.assertEqual(result.decision.chosen_intent, IntentType.CALCULATE)
        self.assertEqual(result.decision.chosen_rule_id, "RULE_CALCULATE_PRIORITY")
        self.assertFalse(result.decision.is_ambiguous)
        self.assertIn("[CalculatorHandler]", result.handler_response)

    def test_unknown_routes_to_fallback(self) -> None:
        """Unrecognized queries map to 'fallback' handler."""
        result = self.router.route_and_execute("Tell me a bedtime story about dragons")
        self.assertEqual(result.handler_name, HandlerName.FALLBACK)
        self.assertEqual(result.decision.chosen_intent, IntentType.UNKNOWN)
        self.assertEqual(result.decision.chosen_rule_id, "RULE_FALLBACK_DEFAULT")
        self.assertFalse(result.decision.is_ambiguous)
        self.assertIn("[FallbackHandler]", result.handler_response)


class TestAmbiguousIntentPriority(unittest.TestCase):
    """Test priority resolution when queries match multiple intent categories."""

    def setUp(self) -> None:
        self.router = AgentComponentRouter()

    def test_ambiguous_query_prioritizes_help_over_calculate(self) -> None:
        """When query matches both 'help' and 'calculate', help takes precedence."""
        query = "Can you help me calculate our departmental travel budget?"
        result = self.router.route_and_execute(query)

        # Invariant: Intent is flagged ambiguous
        self.assertTrue(result.decision.is_ambiguous)
        self.assertIn(IntentType.HELP, result.decision.detected_intents)
        self.assertIn(IntentType.CALCULATE, result.decision.detected_intents)

        # Invariant: Priority 1 (HELP) wins
        self.assertEqual(result.handler_name, HandlerName.SUPPORT)
        self.assertEqual(result.decision.chosen_rule_id, "RULE_HELP_PRIORITY")
        self.assertIn("Ambiguous intent detected", result.decision.rationale)


class TestIntermediateStateTracing(unittest.TestCase):
    """Test capture and sequential fidelity of intermediate execution states."""

    def setUp(self) -> None:
        self.router = AgentComponentRouter()

    def test_trace_contains_all_phases_in_sequence(self) -> None:
        """State trace must contain exactly 5 ordered phases."""
        result = self.router.route_and_execute("Help me reset my token")
        trace = result.state_trace

        self.assertEqual(len(trace), 5)
        self.assertEqual([s.phase for s in trace], [
            StepPhase.RECEIVED,
            StepPhase.ANALYZED,
            StepPhase.ROUTED,
            StepPhase.DISPATCHED,
            StepPhase.COMPLETED,
        ])
        for idx, state in enumerate(trace, start=1):
            self.assertEqual(state.step_number, idx)

    def test_intermediate_payloads_accurate(self) -> None:
        """Each intermediate step must accurately snapshot the local component state."""
        result = self.router.route_and_execute("calculate 10 + 20")
        trace = result.state_trace

        self.assertEqual(trace[0].state_payload["raw_input"], "calculate 10 + 20")
        self.assertEqual(trace[1].state_payload["detected_intents"], ["calculate"])
        self.assertEqual(trace[2].state_payload["target_handler"], "calculator")
        self.assertEqual(trace[3].state_payload["dispatched_to"], "calculator")
        self.assertEqual(trace[4].state_payload["handler_name"], "calculator")


class TestStateTraceInvariants(unittest.TestCase):
    """Test invariant verification linking intermediate states directly to final output."""

    def setUp(self) -> None:
        self.router = AgentComponentRouter()

    def test_valid_execution_satisfies_all_invariants(self) -> None:
        """Normal execution must pass invariant verification without error."""
        result = self.router.route_and_execute("assist with invoice calculation")
        # Invariant verification runs automatically; explicit call should also succeed
        self.router.verify_state_trace_invariants(result)

    def test_tampered_trace_raises_invariant_error(self) -> None:
        """Artificially tampering with intermediate state triggers StateTraceInvariantError."""
        result = self.router.route_and_execute("help me")
        tampered_states = list(result.state_trace)

        # Tamper step 3 (ROUTED) to claim target was 'calculator' while output was 'support'
        tampered_payload = dict(tampered_states[2].state_payload)
        tampered_payload["target_handler"] = "calculator"
        tampered_states[2] = IntermediateState(
            step_number=3,
            phase=StepPhase.ROUTED,
            state_payload=tampered_payload,
            timestamp=tampered_states[2].timestamp,
        )

        tampered_result = RouterExecutionResult(
            request_id=result.request_id,
            raw_input=result.raw_input,
            handler_name=result.handler_name,
            handler_response=result.handler_response,
            decision=result.decision,
            state_trace=tampered_states,
        )

        with self.assertRaises(StateTraceInvariantError) as ctx:
            AgentComponentRouter.verify_state_trace_invariants(tampered_result)
        self.assertIn("Handler parity invariant broken", str(ctx.exception))


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary and edge cases."""

    def setUp(self) -> None:
        self.router = AgentComponentRouter()

    def test_empty_string_routes_to_fallback(self) -> None:
        """Empty input routes safely to fallback."""
        result = self.router.route_and_execute("")
        self.assertEqual(result.handler_name, HandlerName.FALLBACK)
        self.assertEqual(result.decision.chosen_intent, IntentType.UNKNOWN)

    def test_case_insensitivity_and_punctuation(self) -> None:
        """Punctuation and mixed case do not alter intent recognition."""
        result = self.router.route_and_execute("   hElP!   ")
        self.assertEqual(result.handler_name, HandlerName.SUPPORT)


if __name__ == "__main__":
    unittest.main()
