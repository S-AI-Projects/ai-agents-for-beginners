#!/usr/bin/env python3
"""Unit tests for Trace Aggregation — Failure and Recovery Example (R17-T018)."""

import unittest

from example import RequestSummary, ResilientTraceAggregator, TraceEvent


class TestResilientTraceAggregation(unittest.TestCase):
    def setUp(self) -> None:
        self.aggregator = ResilientTraceAggregator()

    def test_canonical_request_a_metrics(self) -> None:
        events = [
            TraceEvent("req_A", "request_start", timestamp_ms=100),
            TraceEvent("req_A", "tool_call", timestamp_ms=104, tool_name="tool_1"),
            TraceEvent("req_A", "tool_call", timestamp_ms=108, tool_name="tool_2"),
            TraceEvent("req_A", "request_end", timestamp_ms=112),
        ]
        summaries, _ = self.aggregator.process_event_stream(events)
        summary_a = summaries["req_A"]
        self.assertEqual(summary_a.status, "success")
        self.assertEqual(summary_a.duration_ms, 12)
        self.assertEqual(summary_a.tool_call_count, 2)

    def test_canonical_request_b_fails(self) -> None:
        events = [
            TraceEvent("req_B", "request_start", timestamp_ms=150),
            TraceEvent("req_B", "request_failed", timestamp_ms=165, error_message="Internal model error"),
        ]
        summaries, _ = self.aggregator.process_event_stream(events)
        summary_b = summaries["req_B"]
        self.assertEqual(summary_b.status, "failed")
        self.assertEqual(summary_b.duration_ms, 15)

    def test_missing_end_events_marked_incomplete(self) -> None:
        events = [
            TraceEvent("req_incomplete", "request_start", timestamp_ms=200),
            TraceEvent("req_incomplete", "tool_call", timestamp_ms=210, tool_name="ping"),
        ]
        summaries, _ = self.aggregator.process_event_stream(events)
        summary = summaries["req_incomplete"]
        self.assertEqual(summary.status, "incomplete")
        self.assertIsNone(summary.duration_ms)
        self.assertNotEqual(summary.duration_ms, 0)

    def test_corrupt_data_failure_and_subsequent_recovery(self) -> None:
        """Exercise documented invalid data case, explain error, and demonstrate recovery on next valid input."""
        events = [
            # 1. Invalid input: missing correlation ID
            TraceEvent(None, "request_start", timestamp_ms=10),
            # 2. Invalid input: negative timestamp
            TraceEvent("req_corrupt", "request_start", timestamp_ms=-99),
            # 3. Subsequent valid input: system recovers cleanly
            TraceEvent("req_recovery", "request_start", timestamp_ms=300),
            TraceEvent("req_recovery", "tool_call", timestamp_ms=305, tool_name="verify"),
            TraceEvent("req_recovery", "request_end", timestamp_ms=315),
        ]
        summaries, anomalies = self.aggregator.process_event_stream(events)

        # Confirm anomaly was logged
        self.assertTrue(len(anomalies) >= 2)
        self.assertTrue(any("missing or non-string request_id" in a for a in anomalies))
        self.assertTrue(any("invalid timestamp" in a for a in anomalies))

        # Confirm corrupt request recorded status
        self.assertEqual(summaries["req_corrupt"].status, "corrupt_data")

        # Confirm immediate recovery on subsequent valid request
        self.assertIn("req_recovery", summaries)
        self.assertEqual(summaries["req_recovery"].status, "success")
        self.assertEqual(summaries["req_recovery"].duration_ms, 15)
        self.assertEqual(summaries["req_recovery"].tool_call_count, 1)


if __name__ == "__main__":
    unittest.main()
