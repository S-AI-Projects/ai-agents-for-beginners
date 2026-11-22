"""Automated Unit Tests for Browser Action Validation (R17-T045)

Lesson Alignment:
15-browser-use (Computer Use Agents: Safety Guardrails, Scope & Step Budgets)

Contract Checks:
1. Navigation to allowed origin 'example.invalid' passes.
2. Other origins are rejected before execution with OriginValidationError.
3. A 4th step fails under a 3-step budget with StepBudgetExceededError.
4. Refactored components (OriginGuard, StepBudgetGuard) function independently and composably.
5. Before/after equivalence: Monolithic and Decomposed validators produce identical outcomes across all test fixtures.
"""

import unittest
try:
    from example import (
        BrowserAction,
        MonolithicBrowserActionValidator,
        OriginGuard,
        StepBudgetGuard,
        DecomposedBrowserActionValidator,
        OriginValidationError,
        StepBudgetExceededError,
        compare_validators,
        normalize_origin,
    )
except ImportError:
    from .example import (
        BrowserAction,
        MonolithicBrowserActionValidator,
        OriginGuard,
        StepBudgetGuard,
        DecomposedBrowserActionValidator,
        OriginValidationError,
        StepBudgetExceededError,
        compare_validators,
        normalize_origin,
    )


class TestBrowserActionValidation(unittest.TestCase):
    """Test suite verifying origin filtering, step budgets, and refactored guard equivalence."""

    def setUp(self):
        self.allowed_origins = {"example.invalid"}
        self.max_steps = 3
        self.monolithic_validator = MonolithicBrowserActionValidator(
            allowed_origins=self.allowed_origins, max_steps=self.max_steps
        )
        self.decomposed_validator = DecomposedBrowserActionValidator(
            origin_guard=OriginGuard(allowed_origins=self.allowed_origins),
            budget_guard=StepBudgetGuard(max_steps=self.max_steps),
        )

    def test_navigation_to_allowed_origin_passes(self):
        """Navigation to allowed 'example.invalid' passes under both validators."""
        actions = [
            BrowserAction("navigate", "https://example.invalid"),
            BrowserAction("click", "#search"),
            BrowserAction("extract", ".results"),
        ]

        self.assertTrue(self.monolithic_validator.validate(actions))
        self.assertTrue(self.decomposed_validator.validate(actions))

    def test_navigation_to_disallowed_origin_rejected(self):
        """Navigation to disallowed origin raises OriginValidationError before execution in both."""
        disallowed_urls = [
            "https://malicious-site.com",
            "http://phishing.invalid",
            "https://attacker.org/steal",
        ]

        for url in disallowed_urls:
            with self.subTest(url=url):
                actions = [BrowserAction("navigate", url)]

                # Monolithic test
                with self.assertRaises(OriginValidationError) as ctx_mono:
                    self.monolithic_validator.validate(actions)
                self.assertIn("example.invalid", str(ctx_mono.exception.allowed_origins))

                # Decomposed test
                with self.assertRaises(OriginValidationError) as ctx_decomp:
                    self.decomposed_validator.validate(actions)
                self.assertEqual(ctx_mono.exception.origin, ctx_decomp.exception.origin)

    def test_fourth_step_fails_under_three_step_budget(self):
        """A 4th step fails under a 3-step budget with StepBudgetExceededError in both."""
        actions_4_steps = [
            BrowserAction("navigate", "https://example.invalid"),
            BrowserAction("click", "#btn1"),
            BrowserAction("input", "#text-field", value="query"),
            BrowserAction("click", "#submit"),
        ]

        # Monolithic check
        with self.assertRaises(StepBudgetExceededError) as ctx_mono:
            self.monolithic_validator.validate(actions_4_steps)
        self.assertEqual(ctx_mono.exception.actual_steps, 4)
        self.assertEqual(ctx_mono.exception.budget_limit, 3)

        # Decomposed check
        with self.assertRaises(StepBudgetExceededError) as ctx_decomp:
            self.decomposed_validator.validate(actions_4_steps)
        self.assertEqual(ctx_decomp.exception.actual_steps, 4)
        self.assertEqual(ctx_decomp.exception.budget_limit, 3)

    def test_step_budget_boundaries(self):
        """Tests 0, 1, 2, and 3 steps under a 3-step budget (all must pass)."""
        # 0 steps (empty)
        self.assertTrue(self.monolithic_validator.validate([]))
        self.assertTrue(self.decomposed_validator.validate([]))

        # 1 step
        act_1 = [BrowserAction("navigate", "https://example.invalid")]
        self.assertTrue(self.monolithic_validator.validate(act_1))
        self.assertTrue(self.decomposed_validator.validate(act_1))

        # 2 steps
        act_2 = [
            BrowserAction("navigate", "https://example.invalid"),
            BrowserAction("click", "#proceed"),
        ]
        self.assertTrue(self.monolithic_validator.validate(act_2))
        self.assertTrue(self.decomposed_validator.validate(act_2))

        # Exactly 3 steps
        act_3 = [
            BrowserAction("navigate", "https://example.invalid"),
            BrowserAction("click", "#proceed"),
            BrowserAction("extract", "#content"),
        ]
        self.assertTrue(self.monolithic_validator.validate(act_3))
        self.assertTrue(self.decomposed_validator.validate(act_3))

    def test_origin_guard_standalone(self):
        """OriginGuard works as an independent modular guard."""
        guard = OriginGuard(allowed_origins={"example.invalid", "service.internal"})

        self.assertTrue(guard.check_url("https://example.invalid/path?param=1"))
        self.assertTrue(guard.check_url("http://service.internal:8080/api"))

        with self.assertRaises(OriginValidationError):
            guard.check_url("https://external-leak.com")

    def test_step_budget_guard_standalone(self):
        """StepBudgetGuard works as an independent modular guard."""
        budget_guard = StepBudgetGuard(max_steps=2)

        self.assertTrue(budget_guard.validate([1, 2]))
        with self.assertRaises(StepBudgetExceededError):
            budget_guard.validate([1, 2, 3])

    def test_before_after_refactoring_equivalence_matrix(self):
        """Extensive fixture suite verifies complete equivalence between monolithic and decomposed validators."""
        fixtures = [
            # Fixture A: Valid standard navigation
            [BrowserAction("navigate", "https://example.invalid/home")],
            # Fixture B: Valid 3 steps
            [
                BrowserAction("navigate", "https://example.invalid"),
                BrowserAction("scroll", "window", value="down"),
                BrowserAction("click", "#footer-link"),
            ],
            # Fixture C: 4 steps budget exceeded
            [
                BrowserAction("navigate", "https://example.invalid"),
                BrowserAction("click", "#a"),
                BrowserAction("click", "#b"),
                BrowserAction("click", "#c"),
            ],
            # Fixture D: Disallowed domain
            [
                BrowserAction("navigate", "https://unauthorized-domain.com"),
            ],
            # Fixture E: Empty list
            [],
            # Fixture F: Dictionary format actions
            [
                {"action_type": "navigate", "target": "https://example.invalid"},
                {"action_type": "click", "target": "#button"},
            ],
        ]

        for idx, fixture in enumerate(fixtures):
            with self.subTest(fixture_idx=idx):
                comparison = compare_validators(
                    actions=fixture,
                    allowed_origins=self.allowed_origins,
                    max_steps=self.max_steps,
                )
                self.assertTrue(
                    comparison["equivalent"],
                    f"Equivalence failed for fixture {idx}: {comparison}",
                )

    def test_normalize_origin_helper(self):
        """normalize_origin accurately extracts hostnames across multiple URL variations."""
        self.assertEqual(normalize_origin("example.invalid"), "example.invalid")
        self.assertEqual(normalize_origin("https://example.invalid"), "example.invalid")
        self.assertEqual(normalize_origin("http://example.invalid:8080/path"), "example.invalid")
        self.assertEqual(normalize_origin("HTTPS://EXAMPLE.INVALID/TEST"), "example.invalid")


if __name__ == "__main__":
    unittest.main()

