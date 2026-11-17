import unittest
try:
    from .example import MetacognitiveRouter
except (ImportError, ValueError):
    from example import MetacognitiveRouter

class TestMetacognitiveRouter(unittest.TestCase):
    def setUp(self):
        self.router = MetacognitiveRouter()

    def test_routing(self):
        self.assertEqual(self.router.route(0.8, 2), "answer")
        self.assertEqual(self.router.route(0.79, 5), "review")
        self.assertEqual(self.router.route(0.9, 1), "review")

    def test_invalid_confidence(self):
        with self.assertRaises(ValueError):
            self.router.route(1.5, 2)
