import unittest

from example import DOCS, answer_with_sources, lexical_adapter


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.search = lexical_adapter(DOCS)

    def test_red_apple_ranks_a_before_b(self):
        self.assertEqual(self.search("red apple"), ["A", "B"])

    def test_ocean_returns_no_match(self):
        self.assertEqual(self.search("ocean"), [])
        self.assertEqual(answer_with_sources("ocean", self.search)["status"], "no_match")

    def test_answer_reports_sources_from_adapter(self):
        result = answer_with_sources("red apple", self.search)
        self.assertEqual(result, {"query": "red apple", "status": "found", "sources": ["A", "B"]})

    def test_any_callable_can_replace_the_adapter(self):
        seen = []

        def fake(query):
            seen.append(query)
            return ["Z"]

        self.assertEqual(answer_with_sources("anything", fake)["sources"], ["Z"])
        self.assertEqual(seen, ["anything"])

    def test_failing_service_is_reported_not_raised(self):
        def broken(query):
            raise ConnectionError("down")

        result = answer_with_sources("red apple", broken)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["sources"], [])


if __name__ == "__main__":
    unittest.main()
