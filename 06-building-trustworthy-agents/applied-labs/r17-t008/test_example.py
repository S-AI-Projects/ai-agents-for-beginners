import unittest
try:
    from .example import PolicyEnforcer, StubExecutor
except (ImportError, ValueError):
    from example import PolicyEnforcer, StubExecutor

class TestPolicyEnforcer(unittest.TestCase):
    def setUp(self):
        self.executor = StubExecutor()
        self.enforcer = PolicyEnforcer(self.executor)

    def test_allowlist_and_recovery(self):
        self.assertEqual(self.enforcer.process("read", {"path": "/p"})["status"], "success")
        self.assertEqual(self.enforcer.process("delete", {"path": "/p"})["status"], "rejected")
        self.assertEqual(self.enforcer.process("read", {})["status"], "rejected")
        self.assertEqual(len(self.executor.executed), 1)
        # Recovery
        self.assertEqual(self.enforcer.process("read", {"path": "/p2"})["status"], "success")
        self.assertEqual(len(self.executor.executed), 2)
