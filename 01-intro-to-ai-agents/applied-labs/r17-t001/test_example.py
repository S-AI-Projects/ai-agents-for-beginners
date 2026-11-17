import unittest
try:
    from .example import ScriptedAgent
except (ImportError, ValueError):
    from example import ScriptedAgent

class TestScriptedAgent(unittest.TestCase):
    def test_normal_termination(self):
        agent = ScriptedAgent(max_steps=3)
        res = agent.run(["inspect", "answer", "stop"])
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["trace"], ["inspect", "answer", "stop"])
        self.assertEqual(res["steps"], 3)

    def test_budget_exceeded(self):
        agent = ScriptedAgent(max_steps=3)
        res = agent.run(["inspect"] * 10)
        self.assertEqual(res["status"], "budget_exceeded")
        self.assertEqual(len(res["trace"]), 3)
        self.assertEqual(res["steps"], 3)

    def test_no_tool_after_stop(self):
        agent = ScriptedAgent(max_steps=3)
        res = agent.run(["inspect", "stop", "answer"])
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["trace"], ["inspect", "stop"])
        self.assertNotIn("answer", res["trace"])
