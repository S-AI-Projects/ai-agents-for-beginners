import unittest
try:
    from .example import LexicalRetriever, assess_q1_predict, assess_q2_diagnose, assess_q3_boundary
except (ImportError, ValueError):
    from example import LexicalRetriever, assess_q1_predict, assess_q2_diagnose, assess_q3_boundary

class TestScenarios(unittest.TestCase):
    def setUp(self):
        self.r = LexicalRetriever()

    def test_core_contract(self):
        res = self.r.retrieve("red apple")
        self.assertEqual(res[0]["doc_id"], "A")
        self.assertEqual(self.r.retrieve("ocean"), [])

    def test_applied_questions(self):
        self.assertEqual(assess_q1_predict(self.r)[0]["doc_id"], "B")
        self.assertEqual(assess_q2_diagnose(self.r)[0]["doc_id"], "A")
        self.assertEqual(assess_q3_boundary(self.r), [])
