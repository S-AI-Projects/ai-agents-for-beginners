#!/usr/bin/env python3
"""Unit tests for Model-Manifest Selection — Invariant and State Trace (R17-T014)."""

import unittest

from example import (
    ManifestSelectorWithTrace,
    ModelEntry,
    TEACHING_MANIFEST,
)


class TestManifestSelectorWithTrace(unittest.TestCase):
    def setUp(self) -> None:
        self.selector = ManifestSelectorWithTrace(TEACHING_MANIFEST)

    def test_canonical_selection_admits_only_fixture_a(self) -> None:
        # Fixture A needs RAM 4 / context 2048, B RAM 8 / context 4096; budget RAM 6 and requested context 1024
        result = self.selector.select(ram_budget_gb=6, requested_context_tokens=1024)
        self.assertIn("fixture_a", result.admitted_models)
        self.assertNotIn("fixture_b", result.admitted_models)
        self.assertNotIn("fixture_c", result.admitted_models)
        # Fixture B excluded because of RAM
        self.assertIn("fixture_b", result.all_rejections)
        self.assertIn("EXCEEDS_RAM_BUDGET", result.all_rejections["fixture_b"])
        # Fixture C excluded because of context (512 < 1024)
        self.assertIn("fixture_c", result.all_rejections)
        self.assertIn("INSUFFICIENT_CONTEXT", result.all_rejections["fixture_c"])

    def test_state_trace_invariants(self) -> None:
        """Verify the formal invariants linking intermediate stage traces to the final output."""
        result = self.selector.select(ram_budget_gb=6, requested_context_tokens=1024)
        self.assertEqual(len(result.stage_traces), 2)

        stage1 = result.stage_traces[0]
        stage2 = result.stage_traces[1]

        # Invariant 1: Stage 1 input contains all manifest entries
        self.assertEqual(stage1.input_candidate_ids, ["fixture_a", "fixture_b", "fixture_c"])

        # Invariant 2: Stage 1 partition invariant (inputs == admitted + rejected)
        self.assertEqual(set(stage1.input_candidate_ids), set(stage1.admitted_candidate_ids) | set(stage1.rejections.keys()))
        self.assertEqual(set(stage1.admitted_candidate_ids) & set(stage1.rejections.keys()), set())

        # Invariant 3: Stage 2 input strictly equals Stage 1 admitted candidates
        self.assertEqual(stage2.input_candidate_ids, stage1.admitted_candidate_ids)

        # Invariant 4: Final admitted models strictly equals Stage 2 admitted candidates
        self.assertEqual(result.admitted_models, stage2.admitted_candidate_ids)

        # Invariant 5: Candidates rejected at Stage 1 never appear in Stage 2 traces
        for rejected_in_stage1 in stage1.rejections.keys():
            self.assertNotIn(rejected_in_stage1, stage2.input_candidate_ids)
            self.assertNotIn(rejected_in_stage1, stage2.admitted_candidate_ids)

    def test_high_ram_and_context_boundary(self) -> None:
        # Budget 16 GB and context 4096 admits Fixture B only (Fixture A has 2048 < 4096, C has 512 < 4096)
        result = self.selector.select(ram_budget_gb=16, requested_context_tokens=4096)
        self.assertEqual(result.admitted_models, ["fixture_b"])

    def test_zero_budget_admits_none(self) -> None:
        result = self.selector.select(ram_budget_gb=1, requested_context_tokens=1024)
        self.assertEqual(result.admitted_models, [])
        self.assertEqual(len(result.all_rejections), 3)


if __name__ == "__main__":
    unittest.main()
