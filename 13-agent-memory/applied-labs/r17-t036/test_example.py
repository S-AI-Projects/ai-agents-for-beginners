import unittest

from example import STREAM, evaluate


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.rows = {row["capacity"]: row for row in evaluate()}

    def test_every_configuration_keeps_the_latest_records_in_order(self):
        for capacity, row in self.rows.items():
            with self.subTest(capacity):
                self.assertTrue(row["correct"])
                self.assertEqual(row["kept"], STREAM[-capacity:])

    def test_recall_of_newest_three_by_capacity(self):
        self.assertEqual(
            {c: row["recall_newest"] for c, row in self.rows.items()},
            {1: 0.33, 3: 1.0, 5: 1.0},
        )

    def test_larger_capacity_stores_more_without_improving_recall_past_window(self):
        self.assertGreater(len(self.rows[5]["kept"]), len(self.rows[3]["kept"]))
        self.assertEqual(self.rows[5]["recall_newest"], self.rows[3]["recall_newest"])

    def test_stream_shorter_than_capacity_keeps_everything(self):
        row = evaluate(capacities=(5,), stream=list("AB"), window=2)[0]
        self.assertEqual(row["kept"], ["A", "B"])
        self.assertTrue(row["correct"])


if __name__ == "__main__":
    unittest.main()
