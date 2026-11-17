import unittest
try:
    from .example import BaselinePlanner, PlanScheduler, DependencyValidator
except (ImportError, ValueError):
    from example import BaselinePlanner, PlanScheduler, DependencyValidator

class TestPlanner(unittest.TestCase):
    def setUp(self):
        self.b = BaselinePlanner()
        self.r = PlanScheduler(DependencyValidator())

    def test_plan_ordering(self):
        tasks = {"A": [], "B": ["A"], "C": ["B"]}
        self.assertEqual(self.b.order_plan(tasks), ["A", "B", "C"])
        self.assertEqual(self.r.order_plan(tasks), ["A", "B", "C"])

    def test_cycle_and_unknown(self):
        with self.assertRaises(ValueError):
            self.r.order_plan({"A": ["B"], "B": ["A"]})
        with self.assertRaises(ValueError):
            self.r.order_plan({"A": ["MISSING"]})
