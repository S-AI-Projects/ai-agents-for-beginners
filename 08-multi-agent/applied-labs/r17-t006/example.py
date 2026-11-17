"""R17-T006: Refactored dependency plan validation."""
class BaselinePlanner:
    def order_plan(self, tasks):
        all_tasks = set(tasks.keys())
        for task, deps in tasks.items():
            for d in deps:
                if d not in all_tasks:
                    raise ValueError(f"Unknown dependency: {d}")
        visited, order = {}, []
        def dfs(node):
            if visited.get(node) == 1:
                raise ValueError("Cycle detected")
            if visited.get(node) == 2:
                return
            visited[node] = 1
            for dep in sorted(tasks.get(node, [])):
                dfs(dep)
            visited[node] = 2
            order.append(node)
        for t in sorted(tasks.keys()):
            if visited.get(t) != 2:
                dfs(t)
        return order

class DependencyValidator:
    def validate(self, tasks):
        all_tasks = set(tasks.keys())
        for task, deps in tasks.items():
            for d in deps:
                if d not in all_tasks:
                    raise ValueError(f"Unknown dependency: {d}")

class PlanScheduler:
    def __init__(self, validator=None):
        self.validator = validator or DependencyValidator()

    def order_plan(self, tasks):
        self.validator.validate(tasks)
        visited, order = {}, []
        def dfs(node):
            if visited.get(node) == 1:
                raise ValueError("Cycle detected")
            if visited.get(node) == 2:
                return
            visited[node] = 1
            for dep in sorted(tasks.get(node, [])):
                dfs(dep)
            visited[node] = 2
            order.append(node)
        for t in sorted(tasks.keys()):
            if visited.get(t) != 2:
                dfs(t)
        return order
