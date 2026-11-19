import unittest

from example import QUESTIONS, rejects, route


class RouteTests(unittest.TestCase):
    def test_thresholds_answer(self):
        self.assertEqual(route(0.8, 2), "answer")
        self.assertEqual(route(1.0, 5), "answer")

    def test_just_below_confidence_needs_review(self):
        self.assertEqual(route(0.79, 2), "review")

    def test_single_evidence_item_needs_review(self):
        self.assertEqual(route(0.95, 1), "review")

    def test_out_of_range_confidence_is_rejected(self):
        for value in (-0.01, 1.01, float("nan")):
            with self.subTest(value):
                self.assertTrue(rejects(value, 2))

    def test_negative_evidence_is_rejected(self):
        self.assertTrue(rejects(0.9, -1))


class QuestionTests(unittest.TestCase):
    def test_there_are_three_questions(self):
        self.assertEqual(len(QUESTIONS), 3)

    def test_every_answer_has_a_passing_check(self):
        for number, question in enumerate(QUESTIONS, start=1):
            with self.subTest(f"Q{number}"):
                self.assertTrue(question["check"]())
                self.assertTrue(question["rationale"])


if __name__ == "__main__":
    unittest.main()
