#!/usr/bin/env python3
"""Unit tests for Browser-Action Guard — Compare Two Approaches (R17-T013)."""

import unittest

from example import BrowserAction, BrowserActionGuard, reference_evaluate_plan


class TestBrowserActionGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.allowed_origins = ["example.invalid"]
        self.guard = BrowserActionGuard(allowed_origins=self.allowed_origins, max_steps=3)

    def test_allowed_navigation_and_actions(self) -> None:
        actions = [
            BrowserAction("navigate", "https://example.invalid/dashboard"),
            BrowserAction("click", "#submit"),
        ]
        res = self.guard.evaluate(actions)
        self.assertTrue(res.allowed)
        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.executed_steps, 2)

    def test_disallowed_origin_rejected_before_execution(self) -> None:
        actions = [
            BrowserAction("navigate", "https://attacker.com/malicious"),
            BrowserAction("click", "#button"),
        ]
        res = self.guard.evaluate(actions)
        self.assertFalse(res.allowed)
        self.assertEqual(res.status, "ORIGIN_DISALLOWED")
        self.assertEqual(res.executed_steps, 0)
        self.assertIn("not in allowlist", res.rejection_reason)

    def test_fourth_step_fails_under_three_step_budget(self) -> None:
        actions = [
            BrowserAction("navigate", "https://example.invalid/step1"),
            BrowserAction("click", "#step2"),
            BrowserAction("type", "#step3"),
            BrowserAction("click", "#step4"),  # 4th step
        ]
        res = self.guard.evaluate(actions)
        self.assertFalse(res.allowed)
        self.assertEqual(res.status, "BUDGET_EXCEEDED")
        self.assertEqual(res.executed_steps, 3)
        self.assertIn("Step budget of 3 exceeded", res.rejection_reason)

    def test_three_steps_exact_boundary_passes(self) -> None:
        actions = [
            BrowserAction("navigate", "https://example.invalid/step1"),
            BrowserAction("click", "#step2"),
            BrowserAction("click", "#step3"),
        ]
        res = self.guard.evaluate(actions)
        self.assertTrue(res.allowed)
        self.assertEqual(res.status, "PASSED")
        self.assertEqual(res.executed_steps, 3)

    def test_compare_two_approaches_equivalence(self) -> None:
        """Compare direct implementation with independent reference calculation on identical test inputs."""
        test_cases = [
            # Case 1: normal allowed
            [BrowserAction("navigate", "https://example.invalid/home"), BrowserAction("click", "#a")],
            # Case 2: forbidden domain
            [BrowserAction("navigate", "https://evil.org/phish")],
            # Case 3: budget overflow
            [
                BrowserAction("navigate", "https://example.invalid/1"),
                BrowserAction("click", "#2"),
                BrowserAction("type", "#3"),
                BrowserAction("click", "#4"),
            ],
            # Case 4: empty actions
            [],
        ]

        for idx, actions in enumerate(test_cases, start=1):
            with self.subTest(case_num=idx):
                direct_res = self.guard.evaluate(actions)
                ref_allowed, ref_status, ref_steps = reference_evaluate_plan(
                    actions, self.allowed_origins, max_steps=3
                )
                self.assertEqual(direct_res.allowed, ref_allowed)
                self.assertEqual(direct_res.status, ref_status)
                self.assertEqual(direct_res.executed_steps, ref_steps)


if __name__ == "__main__":
    unittest.main()
