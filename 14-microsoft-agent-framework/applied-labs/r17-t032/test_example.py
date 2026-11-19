import unittest
from itertools import islice

from example import CASES, expected, make_tools, run_agent


class StepBudgetTests(unittest.TestCase):
    def test_direct_run_matches_expected_table(self):
        for name, plan, status, trace in CASES:
            with self.subTest(name):
                result = run_agent(plan(), make_tools([]))
                self.assertEqual(result["status"], status)
                self.assertEqual(result["trace"], trace)

    def test_direct_run_matches_independent_calculation(self):
        for name, plan, _, _ in CASES:
            with self.subTest(name):
                result = run_agent(plan(), make_tools([]))
                status, trace = expected(list(islice(plan(), 4)))
                self.assertEqual((result["status"], result["trace"]), (status, trace))

    def test_no_tool_runs_after_stop(self):
        calls = []
        run_agent(["inspect", "stop", "answer"], make_tools(calls))
        self.assertEqual(calls, ["inspect"])

    def test_endless_plan_calls_tools_at_most_three_times(self):
        calls = []
        run_agent(iter(lambda: "inspect", None), make_tools(calls))
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
