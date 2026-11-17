import unittest
try:
    from .example import BoundedServiceAgent, DeterministicAdapter
except (ImportError, ValueError):
    from example import BoundedServiceAgent, DeterministicAdapter

class TestBoundedServiceAgent(unittest.TestCase):
    def test_adapter_calls(self):
        adapter = DeterministicAdapter()
        agent = BoundedServiceAgent(adapter, max_steps=3)
        res = agent.run(["inspect", "answer", "stop"])
        self.assertEqual(res["status"], "completed")
        self.assertEqual(adapter.call_history, ["inspect", "answer"])

    def test_budget_exceeded(self):
        adapter = DeterministicAdapter()
        agent = BoundedServiceAgent(adapter, max_steps=3)
        res = agent.run(["inspect"] * 10)
        self.assertEqual(res["status"], "budget_exceeded")
        self.assertEqual(len(adapter.call_history), 3)

    def test_no_call_after_stop(self):
        adapter = DeterministicAdapter()
        agent = BoundedServiceAgent(adapter, max_steps=3)
        agent.run(["inspect", "stop", "answer"])
        self.assertNotIn("answer", adapter.call_history)
