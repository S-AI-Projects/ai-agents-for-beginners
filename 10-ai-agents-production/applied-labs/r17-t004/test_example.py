import unittest
try:
    from .example import TraceAggregator
except (ImportError, ValueError):
    from example import TraceAggregator

class TestTraceAggregator(unittest.TestCase):
    def test_aggregation_and_privacy(self):
        agg = TraceAggregator()
        agg.log_event("A", "start", 0, {"prompt": "private prompt"})
        agg.log_event("A", "tool_call", 5)
        agg.log_event("A", "tool_call", 10)
        agg.log_event("A", "end", 12, {"status": "success"})
        agg.log_event("B", "start", 0)
        agg.log_event("B", "end", 5, {"status": "failure"})
        agg.log_event("C", "start", 0)
        agg.log_event("C", "tool_call", 2)
        summary = agg.aggregate()
        self.assertEqual(summary["A"]["tool_calls"], 2)
        self.assertEqual(summary["A"]["duration_ms"], 12)
        self.assertEqual(summary["B"]["status"], "failure")
        self.assertEqual(summary["C"]["status"], "incomplete")
        self.assertIsNone(summary["C"]["duration_ms"])
        self.assertNotIn("prompt", str(summary))
