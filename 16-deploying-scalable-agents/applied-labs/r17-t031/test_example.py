import json
import unittest

from example import TRACE, aggregate


class AggregateTraceTests(unittest.TestCase):
    def setUp(self):
        self.summary = aggregate(TRACE)

    def test_request_a_has_two_tool_calls_and_12ms(self):
        self.assertEqual(
            self.summary["A"],
            {"duration_ms": 12, "tool_calls": 2, "status": "success"},
        )

    def test_request_b_fails(self):
        self.assertEqual(self.summary["B"]["status"], "failure")
        self.assertEqual(self.summary["B"]["duration_ms"], 7)

    def test_missing_end_is_incomplete_not_zero(self):
        self.assertIsNone(self.summary["C"]["duration_ms"])
        self.assertEqual(self.summary["C"]["status"], "incomplete")
        self.assertEqual(self.summary["C"]["tool_calls"], 1)

    def test_prompt_text_is_never_reported(self):
        report = json.dumps(self.summary)
        for record in TRACE:
            if "prompt" in record:
                self.assertNotIn(record["prompt"], report)

    def test_end_without_start_is_incomplete(self):
        summary = aggregate([{"request_id": "X", "event": "end", "ts_ms": 5, "ok": True}])
        self.assertEqual(summary["X"]["status"], "incomplete")
        self.assertIsNone(summary["X"]["duration_ms"])


if __name__ == "__main__":
    unittest.main()
