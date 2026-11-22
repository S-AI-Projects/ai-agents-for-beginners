"""Automated Unit Tests for Request Router with Failure and Recovery (R17-T047)

Lesson Alignment:
02-explore-agentic-frameworks (Agent Routing, Framework Resilience & Error Recovery)

Contract Checks:
1. Route requests:
   - 'help' -> 'support'
   - 'calculate' -> 'calculator'
   - 'unknown' -> 'fallback'
2. Ambiguity resolution adheres to documented priority: support > calculator > fallback.
3. Invalid / empty / malformed inputs raise explicit InvalidRequestError.
4. Failure and recovery proof: router state is not corrupted, and subsequent valid requests succeed immediately.
5. Structured audit trail tracks all invocations, failures, and recoveries.
"""

import unittest
try:
    from example import (
        FrameworkRouter,
        RoutingResult,
        InvalidRequestError,
        demonstrate_failure_and_recovery,
    )
except ImportError:
    from .example import (
        FrameworkRouter,
        RoutingResult,
        InvalidRequestError,
        demonstrate_failure_and_recovery,
    )


class TestFrameworkRouter(unittest.TestCase):
    """Test suite verifying request routing, ambiguity priorities, and failure recovery."""

    def setUp(self):
        self.router = FrameworkRouter()

    def test_route_help_to_support_handler(self):
        """Queries containing help/support intent route to 'support' handler."""
        queries = [
            "I need help recovering my account",
            "Contact technical support please",
            "Can someone assist with login issues?",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.router.route(q)
                self.assertEqual(res.handler_name, "support")
                self.assertIn("SupportAgent", res.message)

    def test_route_calculate_to_calculator_handler(self):
        """Queries containing calculate/arithmetic intent route to 'calculator' handler."""
        queries = [
            "Calculate 12 * 12",
            "Please compute the math equation",
            "What is 100 / 5?",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.router.route(q)
                self.assertEqual(res.handler_name, "calculator")
                self.assertIn("CalculatorAgent", res.message)

    def test_route_unknown_to_fallback_handler(self):
        """Unrecognized queries route to 'fallback' handler."""
        queries = [
            "Sing me an upbeat song",
            "Tell me an obscure trivia fact",
            "random xyz text query 987",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.router.route(q)
                self.assertEqual(res.handler_name, "fallback")
                self.assertIn("FallbackAgent", res.message)

    def test_ambiguous_intent_priority_resolution(self):
        """Queries matching both help and calculate resolve to 'support' by documented priority."""
        ambiguous = "Help me calculate my quarterly tax estimates"
        res = self.router.route(ambiguous)

        self.assertEqual(res.handler_name, "support")
        self.assertTrue(res.priority_applied)
        self.assertIn("support", res.detected_intents)
        self.assertIn("calculator", res.detected_intents)

    def test_invalid_and_empty_inputs_raise_explicit_exception(self):
        """None, empty, whitespace-only, and non-string inputs raise InvalidRequestError."""
        invalid_cases = [
            None,
            "",
            "   ",
            "\t\n",
            12345,
            {"query": "invalid"},
            ["list", "query"],
        ]
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvalidRequestError) as ctx:
                    self.router.route(invalid)
                self.assertEqual(ctx.exception.raw_input, invalid)
                self.assertIn("Invalid request rejected", str(ctx.exception))

    def test_failure_and_subsequent_recovery_proof(self):
        """Proves that a failure on invalid input does not corrupt state and allows subsequent recovery."""
        # 1. Trigger failure
        with self.assertRaises(InvalidRequestError):
            self.router.route("   ")

        # 2. Immediately issue valid request to prove recovery
        recovery_res = self.router.route("Help me reset my password")
        self.assertEqual(recovery_res.handler_name, "support")
        self.assertEqual(recovery_res.status, "SUCCESS")

        # 3. Verify audit trail captured both the error and the recovery
        trail = self.router.audit_trail
        self.assertGreaterEqual(len(trail), 2)
        error_record = trail[-2]
        success_record = trail[-1]

        self.assertEqual(error_record.status, "ERROR")
        self.assertEqual(error_record.error_type, "InvalidRequestError")
        self.assertEqual(success_record.status, "SUCCESS")
        self.assertEqual(success_record.handler_name, "support")

    def test_multiple_consecutive_failures_then_recovery(self):
        """Multiple consecutive errors do not degrade the router's ability to recover."""
        # 3 consecutive failures
        for bad_input in [None, "", 9999]:
            with self.assertRaises(InvalidRequestError):
                self.router.route(bad_input)

        # Successful subsequent routes across both domains
        res1 = self.router.route("Calculate 50 + 50")
        self.assertEqual(res1.handler_name, "calculator")

        res2 = self.router.route("Help with account settings")
        self.assertEqual(res2.handler_name, "support")

    def test_demonstration_helper_executes_cleanly(self):
        """demonstrate_failure_and_recovery executes and confirms recovery evidence."""
        evidence = demonstrate_failure_and_recovery()
        self.assertTrue(evidence["router_operational_after_recovery"])
        self.assertEqual(len(evidence["subsequent_successful_routes"]), 2)
        self.assertGreater(len(evidence["errors_caught"]), 0)


if __name__ == "__main__":
    unittest.main()
