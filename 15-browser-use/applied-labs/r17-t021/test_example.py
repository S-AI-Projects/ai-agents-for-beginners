"""Unit tests for Browser-Action Guard.

Lesson 15: Building Computer Use Agents (CUA)
Task: R17-T021
Automated check: python3 -m unittest discover -s 15-browser-use/applied-labs/r17-t021 -p "test_*.py"
"""

import unittest

from example import (
    ActionResult,
    ActionType,
    BrowserAction,
    BrowserActionGuard,
    DisallowedOriginError,
    MockBrowserSession,
    StepBudgetExceededError,
    extract_origin,
)


class TestBrowserActionGuard(unittest.TestCase):
    """Test suite verifying safety guardrails for browser agents."""

    def setUp(self) -> None:
        self.allowed_origin = "example.invalid"
        self.guard = BrowserActionGuard(
            allowed_origins=[self.allowed_origin], step_budget=3
        )
        self.browser = MockBrowserSession()

    def test_extract_origin_normalization(self) -> None:
        """Origin extractor should properly parse and normalize hostnames."""
        self.assertEqual(extract_origin("https://example.invalid/path"), "example.invalid")
        self.assertEqual(extract_origin("HTTP://EXAMPLE.INVALID:8080/test"), "example.invalid")
        self.assertEqual(extract_origin("example.invalid"), "example.invalid")
        with self.assertRaises(ValueError):
            extract_origin("")
        with self.assertRaises(ValueError):
            extract_origin("   ")

    def test_navigation_to_allowed_origin_passes(self) -> None:
        """Navigation to approved origin must execute successfully within budget."""
        action = BrowserAction(
            action_type=ActionType.NAVIGATE,
            url="https://example.invalid/home",
        )
        result = self.guard.execute_step(action, self.browser)

        self.assertIsInstance(result, ActionResult)
        self.assertTrue(result.success)
        self.assertEqual(result.step_number, 1)
        self.assertEqual(self.guard.step_count, 1)
        self.assertEqual(self.browser.current_url, "https://example.invalid/home")
        self.assertEqual(len(self.browser.executed_actions), 1)

    def test_disallowed_origin_rejected_before_execution(self) -> None:
        """Navigation to an unapproved origin must be rejected BEFORE execution."""
        rogue_url = "https://untrusted.invalid/login"
        action = BrowserAction(
            action_type=ActionType.NAVIGATE,
            url=rogue_url,
        )

        with self.assertRaises(DisallowedOriginError) as ctx:
            self.guard.execute_step(action, self.browser)

        self.assertEqual(ctx.exception.origin, "untrusted.invalid")
        self.assertEqual(ctx.exception.url, rogue_url)
        self.assertIn("example.invalid", ctx.exception.allowed_origins)

        # Invariant: Browser state must NOT change, step count must NOT increment
        self.assertEqual(self.guard.step_count, 0)
        self.assertIsNone(self.browser.current_url)
        self.assertEqual(len(self.browser.executed_actions), 0)
        self.assertEqual(len(self.browser.history), 0)

    def test_fourth_step_fails_under_three_step_budget(self) -> None:
        """A fourth action must fail under a three-step budget."""
        step1 = BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/page1")
        step2 = BrowserAction(ActionType.CLICK, selector="#button-next")
        step3 = BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/page2")
        step4 = BrowserAction(ActionType.EXTRACT, selector=".content")

        # Steps 1 through 3 should succeed
        res1 = self.guard.execute_step(step1, self.browser)
        self.assertEqual(res1.step_number, 1)
        self.assertEqual(self.guard.step_count, 1)

        res2 = self.guard.execute_step(step2, self.browser)
        self.assertEqual(res2.step_number, 2)
        self.assertEqual(self.guard.step_count, 2)

        res3 = self.guard.execute_step(step3, self.browser)
        self.assertEqual(res3.step_number, 3)
        self.assertEqual(self.guard.step_count, 3)

        # Step 4 must be rejected by the budget guard
        with self.assertRaises(StepBudgetExceededError) as ctx:
            self.guard.execute_step(step4, self.browser)

        self.assertEqual(ctx.exception.attempted_step, 4)
        self.assertEqual(ctx.exception.budget, 3)
        self.assertEqual(ctx.exception.action.action_type, ActionType.EXTRACT)

        # Invariant: Step count must remain at budget limit
        self.assertEqual(self.guard.step_count, 3)
        self.assertEqual(len(self.browser.executed_actions), 3)

    def test_zero_budget_fails_immediately(self) -> None:
        """Boundary test: A guard with step_budget=0 must reject the first action."""
        zero_guard = BrowserActionGuard(
            allowed_origins=["example.invalid"], step_budget=0
        )
        action = BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/")

        with self.assertRaises(StepBudgetExceededError) as ctx:
            zero_guard.execute_step(action, self.browser)

        self.assertEqual(ctx.exception.attempted_step, 1)
        self.assertEqual(ctx.exception.budget, 0)
        self.assertEqual(zero_guard.step_count, 0)
        self.assertIsNone(self.browser.current_url)

    def test_navigate_without_url_raises_error(self) -> None:
        """Navigate action without URL must raise a ValueError."""
        action = BrowserAction(action_type=ActionType.NAVIGATE, url=None)
        with self.assertRaises(ValueError):
            self.guard.execute_step(action, self.browser)


if __name__ == "__main__":
    unittest.main()
