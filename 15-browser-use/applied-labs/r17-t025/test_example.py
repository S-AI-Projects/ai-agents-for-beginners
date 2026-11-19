"""Unit tests for Browser-Action Guard — Offline Service Adapter.

Lesson 15: Building Computer Use Agents (CUA)
Task: R17-T025
Automated check: python3 -m unittest discover -s 15-browser-use/applied-labs/r17-t025 -p "test_*.py" -v
"""

import unittest

from example import (
    ActionType,
    BrowserAction,
    BrowserGuardError,
    BrowserServiceAdapter,
    DisallowedOriginError,
    GuardedBrowserService,
    OfflineLocalBrowserAdapter,
    REAL_SERVICE_UNSUPPORTED_BEHAVIORS,
    StepBudgetExceededError,
    extract_origin,
)


class TestHappyPath(unittest.TestCase):
    """Test valid browser actions routed through the offline adapter within budget."""

    def setUp(self) -> None:
        self.adapter = OfflineLocalBrowserAdapter()
        self.service = GuardedBrowserService(
            adapter=self.adapter,
            allowed_origins=["example.invalid"],
            step_budget=3,
        )

    def test_navigation_to_allowed_origin_passes(self) -> None:
        """Navigation to approved origin passes and updates adapter state."""
        action = BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/home")
        result = self.service.execute(action)

        self.assertTrue(result.success)
        self.assertEqual(result.step_number, 1)
        self.assertEqual(self.service.step_count, 1)
        self.assertEqual(self.adapter.current_url, "https://example.invalid/home")
        self.assertEqual(len(self.adapter.execution_history), 1)

    def test_sequential_actions_update_history(self) -> None:
        """Sequential navigate, click, and extract actions execute through adapter."""
        r1 = self.service.execute(BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/catalog"))
        r2 = self.service.execute(BrowserAction(ActionType.CLICK, selector="#item-42"))
        r3 = self.service.execute(BrowserAction(ActionType.EXTRACT, selector=".price"))

        self.assertEqual(r1.step_number, 1)
        self.assertEqual(r2.step_number, 2)
        self.assertEqual(r3.step_number, 3)
        self.assertEqual(self.service.step_count, 3)
        self.assertEqual(len(self.adapter.execution_history), 3)


class TestOriginPolicyRejection(unittest.TestCase):
    """Test origin containment guardrails rejecting external origins prior to adapter dispatch."""

    def setUp(self) -> None:
        self.adapter = OfflineLocalBrowserAdapter()
        self.service = GuardedBrowserService(
            adapter=self.adapter,
            allowed_origins=["example.invalid"],
            step_budget=3,
        )

    def test_disallowed_origin_rejected_before_execution(self) -> None:
        """Navigation to unauthorized origin fails without mutating adapter state."""
        rogue_url = "https://malicious.invalid/steal"
        action = BrowserAction(ActionType.NAVIGATE, url=rogue_url)

        with self.assertRaises(DisallowedOriginError) as ctx:
            self.service.execute(action)

        self.assertEqual(ctx.exception.origin, "malicious.invalid")
        self.assertEqual(ctx.exception.url, rogue_url)
        self.assertIn("example.invalid", ctx.exception.allowed_origins)

        # Invariant: Adapter state must NOT change
        self.assertEqual(self.service.step_count, 0)
        self.assertIsNone(self.adapter.current_url)
        self.assertEqual(len(self.adapter.execution_history), 0)


class TestStepBudgetEnforcement(unittest.TestCase):
    """Test step budget enforcement blocking runaway action loops."""

    def setUp(self) -> None:
        self.adapter = OfflineLocalBrowserAdapter()
        self.service = GuardedBrowserService(
            adapter=self.adapter,
            allowed_origins=["example.invalid"],
            step_budget=3,
        )

    def test_fourth_step_fails_under_three_step_budget(self) -> None:
        """A fourth action must raise StepBudgetExceededError under a 3-step limit."""
        self.service.execute(BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/1"))
        self.service.execute(BrowserAction(ActionType.CLICK, selector="#next"))
        self.service.execute(BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/2"))

        fourth_action = BrowserAction(ActionType.EXTRACT, selector=".content")
        with self.assertRaises(StepBudgetExceededError) as ctx:
            self.service.execute(fourth_action)

        self.assertEqual(ctx.exception.attempted_step, 4)
        self.assertEqual(ctx.exception.budget, 3)
        self.assertEqual(ctx.exception.action.action_type, ActionType.EXTRACT)

        # Invariant: Step count latches at budget; adapter history remains at 3
        self.assertEqual(self.service.step_count, 3)
        self.assertEqual(len(self.adapter.execution_history), 3)


class TestAdapterInterfaceAndCatalog(unittest.TestCase):
    """Test polymorphic adapter decoupling and verification of unsupported behaviors."""

    def test_adapter_is_subclass_of_abstract_interface(self) -> None:
        """OfflineLocalBrowserAdapter must conform to BrowserServiceAdapter interface."""
        adapter = OfflineLocalBrowserAdapter()
        self.assertIsInstance(adapter, BrowserServiceAdapter)

    def test_unsupported_behaviors_catalog_is_explicit(self) -> None:
        """Catalog must explicitly document the real-service gaps not established by the mock."""
        self.assertGreaterEqual(len(REAL_SERVICE_UNSUPPORTED_BEHAVIORS), 5)
        combined = " ".join(REAL_SERVICE_UNSUPPORTED_BEHAVIORS).lower()
        self.assertIn("network", combined)
        self.assertIn("javascript", combined)
        self.assertIn("cdp", combined)

    def test_custom_mock_adapter_interoperability(self) -> None:
        """GuardedBrowserService accepts any custom adapter conforming to the callable interface."""
        calls = []

        class SpyAdapter(BrowserServiceAdapter):
            def navigate(self, url: str, step: int):
                calls.append(("nav", url))
                return None
            def click(self, sel: str, step: int):
                calls.append(("clk", sel))
                return None
            def extract(self, sel, step: int):
                return None
            @property
            def current_url(self):
                return None
            @property
            def execution_history(self):
                return []

        spy = SpyAdapter()
        svc = GuardedBrowserService(adapter=spy, allowed_origins=["example.invalid"], step_budget=2)
        svc.execute(BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/"))
        svc.execute(BrowserAction(ActionType.CLICK, selector="#btn"))
        self.assertEqual(calls, [("nav", "https://example.invalid/"), ("clk", "#btn")])


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary and edge cases."""

    def test_zero_budget_fails_first_step(self) -> None:
        """step_budget=0 must reject the very first action."""
        adapter = OfflineLocalBrowserAdapter()
        svc = GuardedBrowserService(adapter=adapter, allowed_origins=["example.invalid"], step_budget=0)
        with self.assertRaises(StepBudgetExceededError):
            svc.execute(BrowserAction(ActionType.NAVIGATE, url="https://example.invalid/"))

    def test_empty_url_raises_value_error(self) -> None:
        """Empty navigation URL raises ValueError."""
        adapter = OfflineLocalBrowserAdapter()
        svc = GuardedBrowserService(adapter=adapter, allowed_origins=["example.invalid"])
        with self.assertRaises(ValueError):
            svc.execute(BrowserAction(ActionType.NAVIGATE, url=""))


if __name__ == "__main__":
    unittest.main()
