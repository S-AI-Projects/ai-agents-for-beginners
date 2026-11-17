"""R17-T008: Policy enforcer."""
class StubExecutor:
    def __init__(self):
        self.executed = []
    def execute(self, tool, args):
        self.executed.append((tool, args))
        return f"ok_{tool}"

class PolicyEnforcer:
    ALLOWED = {"read": ["path"]}
    def __init__(self, executor=None):
        self.executor = executor or StubExecutor()

    def process(self, tool, args):
        if tool not in self.ALLOWED:
            return {"status": "rejected", "error": f"Unknown tool: {tool}"}
        for a in self.ALLOWED[tool]:
            if a not in args or not args[a]:
                return {"status": "rejected", "error": f"Missing required argument: {a}"}
        res = self.executor.execute(tool, args)
        return {"status": "success", "result": res}
