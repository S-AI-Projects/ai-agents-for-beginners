#!/usr/bin/env python3
"""Unit tests for Model-Manifest Selection and Scenario Assessment (Task R17-T030).

Validates canonical manifest selection, exclusion diagnostics, boundary policy decisions,
and the three applied assessment questions.
"""

import unittest
from typing import Dict, Any

from example import (
    APPLIED_QUESTIONS,
    ManifestSelector,
    ModelEntry,
    RejectionCode,
    TEACHING_MANIFEST,
    check_q1_predict_output,
    check_q2_diagnose_failure,
    check_q3_boundary_policy,
)


class TestCanonicalManifestSelection(unittest.TestCase):
    """Verifies the core canonical contract required by Task R17-T030."""

    def setUp(self) -> None:
        self.selector = ManifestSelector()

    def test_canonical_budget_admits_only_fixture_a(self) -> None:
        """Budget RAM6 and requested context1024 admits only Fixture A."""
        result = self.selector.select(ram_budget_gb=6, requested_context_tokens=1024)

        admitted_ids = [m.id for m in result.eligible_models]
        self.assertEqual(admitted_ids, ["fixture_a"])
        self.assertEqual(len(result.eligible_models), 1)

        # Verify Fixture A attributes
        fixture_a = result.eligible_models[0]
        self.assertEqual(fixture_a.required_ram_gb, 4)
        self.assertEqual(fixture_a.max_context_tokens, 2048)
        self.assertTrue(fixture_a.supports_tools)

    def test_excluded_entries_report_actionable_reasons(self) -> None:
        """Excluded models report explicit error codes and actionable remediation."""
        result = self.selector.select(ram_budget_gb=6, requested_context_tokens=1024)

        self.assertIn("fixture_b", result.excluded_models)
        b_reasons = result.excluded_models["fixture_b"]
        self.assertTrue(any(r.code == RejectionCode.EXCEEDS_RAM_BUDGET for r in b_reasons))
        self.assertIn("exceeding budget of 6 GB", b_reasons[0].message)
        self.assertTrue(len(b_reasons[0].remediation) > 0)
        self.assertIn("RAM allocation", b_reasons[0].remediation)


class TestBoundaryPoliciesAndConstraints(unittest.TestCase):
    """Verifies edge cases and boundary comparison policies."""

    def setUp(self) -> None:
        self.selector = ManifestSelector()

    def test_exact_ram_boundary_inclusive(self) -> None:
        """When required RAM equals budget, model is admitted (inclusive policy)."""
        result = self.selector.select(ram_budget_gb=4, requested_context_tokens=1024)
        admitted_ids = [m.id for m in result.eligible_models]
        self.assertIn("fixture_a", admitted_ids)

    def test_exact_context_boundary_inclusive(self) -> None:
        """When requested context equals maximum context, model is admitted."""
        result = self.selector.select(ram_budget_gb=8, requested_context_tokens=2048)
        admitted_ids = [m.id for m in result.eligible_models]
        # Fixture A has exactly 2048 tokens; must be admitted
        self.assertIn("fixture_a", admitted_ids)

    def test_insufficient_ram_budget_rejects_all(self) -> None:
        """RAM budget below smallest tool model (3 GB) excludes Fixture A and B."""
        result = self.selector.select(ram_budget_gb=3, requested_context_tokens=1024)
        admitted_ids = [m.id for m in result.eligible_models]
        self.assertEqual(admitted_ids, [])

    def test_missing_tool_support_rejection(self) -> None:
        """Fixture C lacks tool support and must be excluded when require_tools=True."""
        result = self.selector.select(ram_budget_gb=16, requested_context_tokens=256, require_tools=True)
        admitted_ids = [m.id for m in result.eligible_models]
        self.assertNotIn("fixture_c", admitted_ids)

        c_codes = [r.code for r in result.excluded_models["fixture_c"]]
        self.assertIn(RejectionCode.MISSING_TOOL_SUPPORT, c_codes)


class TestAppliedScenarioAssessment(unittest.TestCase):
    """Verifies the three applied assessment questions and executable checks."""

    def test_question_1_predict_output_check(self) -> None:
        """Question 1: Executable check correctly predicts output for 6GB/1024 tokens."""
        self.assertTrue(check_q1_predict_output())
        q1 = APPLIED_QUESTIONS["question_1_predict_output"]
        self.assertEqual(q1["expected_answer"], ["fixture_a"])
        self.assertIn("Fixture A requires 4 GB RAM", q1["rationale"])

    def test_question_2_diagnose_failure_check(self) -> None:
        """Question 2: Executable check confirms INSUFFICIENT_CONTEXT on 8192 token request."""
        self.assertTrue(check_q2_diagnose_failure())
        q2 = APPLIED_QUESTIONS["question_2_diagnose_failure"]
        self.assertIn("INSUFFICIENT_CONTEXT", q2["expected_answer"])
        self.assertIn("context starvation", q2["rationale"])

    def test_question_3_boundary_policy_check(self) -> None:
        """Question 3: Executable check confirms inclusive boundary policy admitting exact match."""
        self.assertTrue(check_q3_boundary_policy())
        q3 = APPLIED_QUESTIONS["question_3_boundary_policy"]
        self.assertIn("Inclusive policy", q3["expected_answer"])
        self.assertIn("exact-fit allocations", q3["rationale"])


if __name__ == "__main__":
    unittest.main()
