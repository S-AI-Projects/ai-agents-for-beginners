import unittest
try:
    from .example import IntentRouter
except (ImportError, ValueError):
    from example import IntentRouter

class TestIntentRouter(unittest.TestCase):
    def setUp(self):
        self.router = IntentRouter()

    def test_help_routing(self):
        self.assertEqual(self.router.route("need help")["handler"], "support")

    def test_calc_routing(self):
        self.assertEqual(self.router.route("please calculate tax")["handler"], "calculator")

    def test_fallback_routing(self):
        self.assertEqual(self.router.route("random query")["handler"], "fallback")

    def test_ambiguous_intent(self):
        res = self.router.route("help calculate this")
        self.assertEqual(res["handler"], "support")
        self.assertEqual(res["rule"], "priority:help_over_calculate")
