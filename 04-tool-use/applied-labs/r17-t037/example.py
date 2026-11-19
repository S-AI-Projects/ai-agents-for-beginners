import json

TOOLS = {
    "add": lambda a, b: a + b,
    "multiply": lambda a, b: a * b,
}


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def dispatch(raw, tools=TOOLS):
    try:
        call = json.loads(raw)
        name = call["tool"]
        args = call["args"]
    except (ValueError, KeyError, TypeError):
        return {"ok": False, "error": "malformed_call"}
    if not isinstance(name, str) or name not in tools:
        return {"ok": False, "error": "unknown_tool"}
    if not isinstance(args, dict) or set(args) != {"a", "b"} or not all(map(is_number, args.values())):
        return {"ok": False, "error": "invalid_arguments"}
    return {"ok": True, "result": tools[name](**args)}


def run_calls(calls, tools=TOOLS):
    results = []
    for raw in calls:
        result = dispatch(raw, tools)
        results.append(result)
        if not result["ok"]:
            break
    return results


if __name__ == "__main__":
    calls = [
        '{"tool": "add", "args": {"a": 2, "b": 3}}',
        '{"tool": "multiply", "args": {"a": 2, "b": 3}}',
        '{"tool": "divide", "args": {"a": 2, "b": 3}}',
        '{"tool": "add", "args": {"a": "2", "b": 3}}',
    ]
    for raw in calls:
        print(raw, "->", json.dumps(dispatch(raw)))
