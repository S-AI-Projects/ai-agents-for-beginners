#!/usr/bin/env python3
"""Unit tests for Trace Aggregation — Refactor the Teaching Example (R17-T016)."""

import unittest

from example import (
    AggregatedTraceSummary,
    RefactoredTraceAggregator,
    TraceEvent,
    baseline_aggregate_traces,
    get_canonical_fixture,
)


class TestTraceAggregationRefactoring(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = get_canonical_fixture()
        self.refactored = RefactoredTraceAggregator()

    def test_canonical_request_a_metrics(self) -> None:
        # Request A has two tool calls and duration 12ms
        summaries = self.refactored.aggregate(self.fixture)
        summary_a = summaries["req_A"]
        self.assertEqual(summary_a.status, "success")
        self.assertEqual(summary_a.duration_ms, 12)
        self.assertEqual(summary_a.tool_call_count, 2)
        self.assertEqual(summary_a.tools_invoked, ["search_kb", "calculate_fare"])

    def test_canonical_request_b_fails(self) -> None:
        # Request B fails
        summaries = self.refactored.aggregate(self.fixture)
        summary_b = summaries["req_B"]
        self.assertEqual(summary_b.status, "failed")
        self.assertEqual(summary_b.duration_ms, 10)
        self.assertEqual(summary_b.tool_call_count, 1)

    def test_canonical_missing_end_event_marked_incomplete(self) -> None:
        # Missing end events are marked incomplete rather than assigned duration zero
        summaries = self.refactored.aggregate(self.fixture)
        summary_c = summaries["req_C"]
        self.assertEqual(summary_c.status, "incomplete")
        self.assertIsNone(summary_c.duration_ms)
        self.assertNotEqual(summary_c.duration_ms, 0)
        self.assertEqual(summary_c.tool_call_count, 1)

    def test_privacy_preservation_no_prompts_leaked(self) -> None:
        summaries = self.refactored.aggregate(self.fixture)
        for req_id, summ in summaries.items():
            self.assertFalse(hasattr(summ, "prompt_payload"))
            self.assertNotIn("Secret", str(summ))
            self.assertNotIn("Private", str(summ))

    def test_refactoring_equivalence(self) -> None:
        """Verify before/after equivalence between baseline and refactored implementation."""
        baseline_res = baseline_aggregate_traces(self.fixture)
        refactored_res = self.refactored.aggregate(self.fixture)

        self.assertEqual(set(baseline_res.keys()), set(refactored_res.keys()))
        for req_id in baseline_res:
            b = baseline_res[req_id]
            r = refactored_res[req_id]
            self.assertEqual(b.request_id, r.request_id)
            self.assertEqual(b.duration_ms, r.duration_ms)
            self.assertEqual(b.tool_call_count, r.tool_call_count)
            self.assertEqual(b.status, r.status)
            self.assertEqual(b.tools_invoked, r.tools_invoked)


if __name__ == "__main__":
    unittest.main()
