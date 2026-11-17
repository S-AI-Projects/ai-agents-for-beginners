import unittest
try:
    from .example import order_plan
except (ImportError, ValueError):
    from example import order_plan

class TestPlanRegression(unittest.TestCase):
    def test_valid_worked_example(self):
        self.assertEqual(order_plan({"A": [], "B": ["A"], "C": ["B"]}), ["A", "B", "C"])

    def test_cycle_rejection(self):
        with self.assertRaises(ValueError):
            order_plan({"A": ["B"], "B": ["A"]})

    def test_unknown_dependency(self):
        with self.assertRaises(ValueError) as ctx:
            order_plan({"A": ["UNKNOWN"]})
        self.assertIn("UNKNOWN", str(ctx.exception))
