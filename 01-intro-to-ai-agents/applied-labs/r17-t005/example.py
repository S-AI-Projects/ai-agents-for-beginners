"""R17-T005: Service adapter."""
class ServiceAdapter:
    def execute(self, action):
        raise NotImplementedError

class DeterministicAdapter(ServiceAdapter):
    def __init__(self):
        self.call_history = []

    def execute(self, action):
        self.call_history.append(action)
        return f"result_{action}"

class BoundedServiceAgent:
    def __init__(self, adapter: ServiceAdapter, max_steps=3):
        self.adapter = adapter
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
            self.adapter.execute(action)
        return {"status": "completed", "trace": list(self.trace), "steps": len(self.trace)}
