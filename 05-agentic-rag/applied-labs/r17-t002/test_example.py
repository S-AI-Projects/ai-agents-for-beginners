import unittest
try:
    from .example import LexicalRetriever
except (ImportError, ValueError):
    from example import LexicalRetriever

class TestLexicalRetriever(unittest.TestCase):
    def setUp(self):
        self.retriever = LexicalRetriever()

    def test_ranking_red_apple(self):
        res = self.retriever.retrieve("red apple")
        self.assertEqual([r["doc_id"] for r in res], ["A", "B"])

    def test_ocean_no_match(self):
        self.assertEqual(self.retriever.retrieve("ocean"), [])

    def test_boundary_empty_query(self):
        self.assertEqual(self.retriever.retrieve(""), [])
