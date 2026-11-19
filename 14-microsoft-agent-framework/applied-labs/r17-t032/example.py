from itertools import cycle, islice

MAX_STEPS = 3


def make_tools(calls):
    return {
        "inspect": lambda: calls.append("inspect"),
        "answer": lambda: calls.append("answer"),
    }


def run_agent(plan, tools, max_steps=MAX_STEPS):
    trace = []
    for step, action in enumerate(plan, start=1):
        if step > max_steps:
            return {"status": "budget_exceeded", "trace": trace}
        trace.append(action)
        if action == "stop":
            return {"status": "completed", "trace": trace}
        tools[action]()
    return {"status": "completed", "trace": trace}


def expected(prefix, max_steps=MAX_STEPS):
    window = prefix[:max_steps]
    if "stop" in window:
        return "completed", window[: window.index("stop") + 1]
    if len(prefix) > max_steps:
        return "budget_exceeded", window
    return "completed", window


CASES = [
    ("normal", lambda: ["inspect", "answer", "stop"], "completed", ["inspect", "answer", "stop"]),
    ("endless", lambda: cycle(["inspect"]), "budget_exceeded", ["inspect", "inspect", "inspect"]),
    ("stop first", lambda: ["stop", "answer"], "completed", ["stop"]),
    ("stop at step 4", lambda: ["inspect", "inspect", "inspect", "stop"], "budget_exceeded", ["inspect", "inspect", "inspect"]),
]


if __name__ == "__main__":
    for name, plan, status, trace in CASES:
        result = run_agent(plan(), make_tools([]))
        print(f"{name}: {result['status']} {result['trace']}")
