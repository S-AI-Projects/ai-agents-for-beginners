"""Automated Unit Tests for Production Trace Aggregation (R17-T046)

Lesson Alignment:
10-ai-agents-production (Observability, Telemetry & Evaluation)

Contract Checks:
1. Aggregate trace events by request ID: duration, tool-call count, status.
2. Request A: 2 tool calls, duration 12ms, status SUCCESS.
3. Request B: fails with status FAILED.
4. Request C: missing end events marked INCOMPLETE with duration None (not 0).
5. Privacy: Prompt contents and raw queries are omitted from aggregated metrics.
6. Worked example regression test.
"""

import unittest
try:
    from example import (
        TraceEvent,
        AggregatedMetrics,
        aggregate_trace_events,
        run_worked_example,
        CANONICAL_TRACE_EVENTS,
    )
except ImportError:
    from .example import (
        TraceEvent,
        AggregatedMetrics,
        aggregate_trace_events,
        run_worked_example,
        CANONICAL_TRACE_EVENTS,
    )


class TestTraceAggregation(unittest.TestCase):
    """Test suite verifying trace aggregation, contract invariants, and privacy safeguards."""

    def test_canonical_request_a(self):
        """Request A has 2 tool calls, duration 12ms, and status SUCCESS."""
        metrics = aggregate_trace_events(CANONICAL_TRACE_EVENTS)
        self.assertIn("A", metrics)
        metric_a = metrics["A"]

        self.assertEqual(metric_a.request_id, "A")
        self.assertEqual(metric_a.tool_call_count, 2)
        self.assertEqual(metric_a.duration_ms, 12.0)
        self.assertEqual(metric_a.status, "SUCCESS")

    def test_canonical_request_b_failed(self):
        """Request B terminates with ERROR and reports status FAILED."""
        metrics = aggregate_trace_events(CANONICAL_TRACE_EVENTS)
        self.assertIn("B", metrics)
        metric_b = metrics["B"]

        self.assertEqual(metric_b.request_id, "B")
        self.assertEqual(metric_b.tool_call_count, 1)
        self.assertEqual(metric_b.status, "FAILED")
        self.assertEqual(metric_b.duration_ms, 18.0)

    def test_canonical_request_c_missing_end_is_incomplete(self):
        """Request C with missing end event is marked INCOMPLETE with duration None (not 0)."""
        metrics = aggregate_trace_events(CANONICAL_TRACE_EVENTS)
        self.assertIn("C", metrics)
        metric_c = metrics["C"]

        self.assertEqual(metric_c.request_id, "C")
        self.assertEqual(metric_c.status, "INCOMPLETE")
        # Explicit contract check: duration is None, NOT 0
        self.assertIsNone(metric_c.duration_ms)
        self.assertNotEqual(metric_c.duration_ms, 0)
        self.assertNotEqual(metric_c.duration_ms, 0.0)

    def test_privacy_safeguard_omits_prompt_contents(self):
        """Prompt contents and raw input payloads are strictly excluded from metrics."""
        metrics = aggregate_trace_events(CANONICAL_TRACE_EVENTS)
        for req_id, m in metrics.items():
            serialized = m.to_dict()
            # Verify no 'prompt' key exists
            self.assertNotIn("prompt", serialized)
            self.assertNotIn("payload", serialized)
            # Verify user query text from canonical fixtures does not appear anywhere
            serialized_str = str(serialized)
            self.assertNotIn("calculate annual budget", serialized_str)
            self.assertNotIn("confidential contract transfer", serialized_str)
            self.assertNotIn("stream real-time sensor telemetry", serialized_str)

    def test_empty_event_stream_returns_empty_dict(self):
        """Empty event stream returns an empty dictionary without errors."""
        self.assertEqual(aggregate_trace_events([]), {})

    def test_zero_tool_calls_request(self):
        """A simple request without tool calls reports tool_call_count == 0."""
        events = [
            {"event_type": "START", "request_id": "simple", "timestamp_ms": 100.0, "payload": {"prompt": "Hi"}},
            {"event_type": "END", "request_id": "simple", "timestamp_ms": 105.0, "payload": {"status": "SUCCESS"}},
        ]
        metrics = aggregate_trace_events(events)
        self.assertIn("simple", metrics)
        self.assertEqual(metrics["simple"].tool_call_count, 0)
        self.assertEqual(metrics["simple"].duration_ms, 5.0)
        self.assertEqual(metrics["simple"].status, "SUCCESS")

    def test_trace_event_dataclass_objects_handling(self):
        """aggregate_trace_events seamlessly accepts TraceEvent dataclass instances."""
        events = [
            TraceEvent(event_type="START", request_id="obj_req", timestamp_ms=500.0, payload={"prompt": "secret"}),
            TraceEvent(event_type="TOOL_CALL", request_id="obj_req", timestamp_ms=510.0, payload={"tool": "search"}),
            TraceEvent(event_type="END", request_id="obj_req", timestamp_ms=525.0, payload={"status": "SUCCESS"}),
        ]
        metrics = aggregate_trace_events(events)
        self.assertIn("obj_req", metrics)
        self.assertEqual(metrics["obj_req"].tool_call_count, 1)
        self.assertEqual(metrics["obj_req"].duration_ms, 25.0)
        self.assertEqual(metrics["obj_req"].status, "SUCCESS")
        self.assertNotIn("secret", str(metrics["obj_req"].to_dict()))

    def test_interleaved_multi_request_stream(self):
        """Events from multiple interleaved concurrent requests are properly partitioned."""
        events = [
            {"event_type": "START", "request_id": "R1", "timestamp_ms": 10.0},
            {"event_type": "START", "request_id": "R2", "timestamp_ms": 15.0},
            {"event_type": "TOOL_CALL", "request_id": "R1", "timestamp_ms": 20.0},
            {"event_type": "TOOL_CALL", "request_id": "R2", "timestamp_ms": 25.0},
            {"event_type": "TOOL_CALL", "request_id": "R1", "timestamp_ms": 30.0},
            {"event_type": "END", "request_id": "R1", "timestamp_ms": 35.0},
            # R2 remains incomplete
        ]
        metrics = aggregate_trace_events(events)
        self.assertEqual(metrics["R1"].tool_call_count, 2)
        self.assertEqual(metrics["R1"].duration_ms, 25.0)
        self.assertEqual(metrics["R1"].status, "SUCCESS")

        self.assertEqual(metrics["R2"].tool_call_count, 1)
        self.assertIsNone(metrics["R2"].duration_ms)
        self.assertEqual(metrics["R2"].status, "INCOMPLETE")

    def test_worked_example_runner(self):
        """run_worked_example() executes successfully and returns all canonical metrics."""
        result = run_worked_example()
        self.assertEqual(set(result.keys()), {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
