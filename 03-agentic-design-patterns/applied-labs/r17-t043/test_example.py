"""Automated Unit Tests for Routing Agent with Offline Adapter (R17-T043)

Lesson Alignment:
03-agentic-design-patterns (Routing & Classification Pattern)

Contract Checks:
1. Route incoming requests to named handlers:
   - 'help' -> 'support'
   - 'calculate' -> 'calculator'
   - 'unknown' -> 'fallback'
2. Handle ambiguous intents following documented priority (support > calculator > fallback).
3. Record an auditable structured decision log with query, detected intents, reason, and confidence.
4. Offline service adapter:
   - Adheres to ClassifierAdapterProtocol.
   - Deterministic local mock adapter operates without network/API dependencies.
5. Explicit documentation of unsimulated real-service behaviors.
"""

import unittest
try:
    from example import (
        IntentRouter,
        DeterministicMockClassifierAdapter,
        ClassifierAdapterProtocol,
        ClassificationResult,
        HandlerResponse,
        UNSIMULATED_REAL_SERVICE_BEHAVIORS,
    )
except ImportError:
    from .example import (
        IntentRouter,
        DeterministicMockClassifierAdapter,
        ClassifierAdapterProtocol,
        ClassificationResult,
        HandlerResponse,
        UNSIMULATED_REAL_SERVICE_BEHAVIORS,
    )


class TestIntentRouter(unittest.TestCase):
    """Test suite verifying router dispatch, ambiguity priority, decision logs, and adapters."""

    def setUp(self):
        self.router = IntentRouter()

    def test_route_help_to_support_handler(self):
        """Requests with help/support intents route to 'support' handler."""
        queries = [
            "Help me reset my account password",
            "I need technical support with my device",
            "Can an agent assist me please?",
        ]
        for q in queries:
            with self.subTest(query=q):
                resp = self.router.route(q)
                self.assertEqual(resp.handler_name, "support")
                self.assertIn("SupportAgent", resp.message)

    def test_route_calculate_to_calculator_handler(self):
        """Requests with calculate/arithmetic intents route to 'calculator' handler."""
        queries = [
            "Please calculate 12 * 8",
            "Compute the sum of numbers",
            "What is 100 / 4?",
        ]
        for q in queries:
            with self.subTest(query=q):
                resp = self.router.route(q)
                self.assertEqual(resp.handler_name, "calculator")
                self.assertIn("CalculatorAgent", resp.message)

    def test_route_unknown_to_fallback_handler(self):
        """Unrecognized requests route to 'fallback' handler."""
        queries = [
            "Sing me a lullaby about stars",
            "What is the weather in Seattle?",
            "xyzabc random tokens 12345",
        ]
        for q in queries:
            with self.subTest(query=q):
                resp = self.router.route(q)
                self.assertEqual(resp.handler_name, "fallback")
                self.assertIn("FallbackAgent", resp.message)

    def test_ambiguous_intent_resolved_by_priority(self):
        """Ambiguous request containing both help and calculate resolves to 'support' by priority."""
        ambiguous_query = "Help me calculate my monthly subscription bill"
        resp = self.router.route(ambiguous_query)

        # Documented priority: support > calculator > fallback
        self.assertEqual(resp.handler_name, "support")

        # Verify decision log reflects ambiguity resolution
        latest_record = self.router.decision_log[-1]
        self.assertTrue(latest_record.priority_applied)
        self.assertIn("support", latest_record.detected_intents)
        self.assertIn("calculator", latest_record.detected_intents)
        self.assertIn("documented priority", latest_record.decision_reason)

    def test_auditable_decision_log_records_all_fields(self):
        """Every routing decision is captured in an auditable structured log."""
        query = "Can you help me configure MFA?"
        self.router.route(query)

        records = self.router.decision_log
        self.assertGreaterEqual(len(records), 1)
        record = records[-1]

        self.assertIsInstance(record.decision_id, int)
        self.assertTrue(len(record.timestamp_iso) > 0)
        self.assertEqual(record.raw_query, query)
        self.assertIn("support", record.detected_intents)
        self.assertEqual(record.selected_handler, "support")
        self.assertFalse(record.priority_applied)
        self.assertIn("Direct intent match", record.decision_reason)
        self.assertGreater(record.confidence, 0.0)
        self.assertIn("SupportAgent", record.response_summary)

    def test_decision_log_immutability_protection(self):
        """Mutating the exposed decision log list does not affect internal audit state."""
        self.router.route("Help me please")
        initial_len = len(self.router.decision_log)

        exposed_log = self.router.decision_log
        exposed_log.clear()

        self.assertEqual(len(self.router.decision_log), initial_len)

    def test_offline_adapter_protocol_compliance(self):
        """DeterministicMockClassifierAdapter complies with ClassifierAdapterProtocol."""
        adapter = DeterministicMockClassifierAdapter()
        self.assertIsInstance(adapter, ClassifierAdapterProtocol)

        # Test both callable and named method interfaces
        res_callable = adapter("calculate 2 + 2")
        res_method = adapter.classify("calculate 2 + 2")

        self.assertEqual(res_callable.detected_intents, res_method.detected_intents)
        self.assertEqual(res_callable.confidence_scores, res_method.confidence_scores)
        self.assertIn("calculator", res_callable.detected_intents)

    def test_custom_adapter_injection(self):
        """Router supports injecting custom classification adapters."""
        class MockKeywordAdapter:
            def __call__(self, q: str) -> ClassificationResult:
                return self.classify(q)

            def classify(self, q: str) -> ClassificationResult:
                return ClassificationResult(
                    raw_query=q,
                    detected_intents=["calculate"],
                    confidence_scores={"calculate": 0.99},
                    rationale="Forced calculator classification for test.",
                )

        custom_router = IntentRouter(classifier=MockKeywordAdapter())
        resp = custom_router.route("Any random text")
        self.assertEqual(resp.handler_name, "calculator")

    def test_custom_handler_injection(self):
        """Router allows registering custom handler implementations."""
        def custom_support(query: str) -> HandlerResponse:
            return HandlerResponse(
                handler_name="custom_support",
                message=f"CustomSupport: Handled '{query}'",
            )

        custom_router = IntentRouter(custom_handlers={"support": custom_support})
        resp = custom_router.route("Help me")
        self.assertEqual(resp.handler_name, "custom_support")
        self.assertIn("CustomSupport", resp.message)

    def test_unsimulated_real_service_behaviors_documented(self):
        """All required unsimulated real-service behaviors are documented explicitly."""
        expected_keys = {
            "network_latency",
            "token_rate_limits",
            "probabilistic_llm_drift",
            "context_window_and_truncation",
            "authentication_and_authorization",
            "service_availability_and_transient_failures",
        }
        for key in expected_keys:
            self.assertIn(key, UNSIMULATED_REAL_SERVICE_BEHAVIORS)
            self.assertTrue(len(UNSIMULATED_REAL_SERVICE_BEHAVIORS[key]) > 20)


if __name__ == "__main__":
    unittest.main()
