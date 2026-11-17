"""R17-T001: Bounded agent loop runnable concept example."""
class ScriptedAgent:
    def __init__(self, max_steps=3):
        self.max_steps = max_steps
        self.trace = []

    def run(self, plan):
        self.trace = []
        for step, action in enumerate(plan, start=1):
            if step > self.max_steps:
                return {"status": "budget_exceeded", "trace": list(self.trace), "steps": self.max_steps}
            self.trace.append(action)
            if action == "stop":
                return {"status": "completed", "trace": list(self.trace), "steps": step}
        return {"status": "completed", "trace": list(self.trace), "steps": len(self.trace)}
