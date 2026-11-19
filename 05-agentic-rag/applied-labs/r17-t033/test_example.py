import unittest

from example import DOCS, retrieve


class RetrieveTests(unittest.TestCase):
    def test_red_apple_ranks_a_before_b(self):
        hits, _ = retrieve("red apple")
        self.assertEqual([doc_id for doc_id, _ in hits], ["A", "B"])

    def test_ocean_returns_no_match(self):
        hits, _ = retrieve("ocean")
        self.assertEqual(hits, [])

    def test_query_is_case_insensitive(self):
        hits, _ = retrieve("RED Apple")
        self.assertEqual([doc_id for doc_id, _ in hits], ["A", "B"])

    def test_ties_break_by_document_id(self):
        hits, _ = retrieve("apple")
        self.assertEqual(hits, [("A", 1), ("B", 1)])

    def test_trace_has_one_state_per_step(self):
        _, trace = retrieve("red apple")
        self.assertEqual([step for step, _ in trace], ["normalize", "score", "rank", "filter"])

    def test_final_output_follows_recorded_state(self):
        for query in ("red apple", "apple", "sky", "ocean", ""):
            with self.subTest(query):
                hits, trace = retrieve(query)
                state = dict(trace)
                self.assertEqual([doc_id for doc_id, _ in hits], state["filter"])
                self.assertEqual(state["filter"], [d for d in state["rank"] if state["score"][d] > 0])
                for doc_id, score in hits:
                    self.assertEqual(score, state["score"][doc_id])
                self.assertEqual(set(state["score"]), set(DOCS))


if __name__ == "__main__":
    unittest.main()
