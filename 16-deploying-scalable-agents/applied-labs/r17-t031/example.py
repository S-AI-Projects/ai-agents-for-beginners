import json

TRACE = [
    {"request_id": "A", "event": "start", "ts_ms": 0, "prompt": "plan a trip to Lisbon"},
    {"request_id": "B", "event": "start", "ts_ms": 2, "prompt": "book a hotel in Porto"},
    {"request_id": "A", "event": "tool_call", "ts_ms": 3, "tool": "search_flights"},
    {"request_id": "C", "event": "start", "ts_ms": 4, "prompt": "cancel my booking"},
    {"request_id": "A", "event": "tool_call", "ts_ms": 7, "tool": "search_hotels"},
    {"request_id": "B", "event": "end", "ts_ms": 9, "ok": False},
    {"request_id": "C", "event": "tool_call", "ts_ms": 10, "tool": "lookup_booking"},
    {"request_id": "A", "event": "end", "ts_ms": 12, "ok": True},
]


def aggregate(records):
    runs = {}
    for record in records:
        run = runs.setdefault(
            record["request_id"],
            {"start": None, "end": None, "tool_calls": 0, "ok": None},
        )
        event = record["event"]
        if event == "start":
            run["start"] = record["ts_ms"]
        elif event == "tool_call":
            run["tool_calls"] += 1
        elif event == "end":
            run["end"] = record["ts_ms"]
            run["ok"] = record["ok"]

    summary = {}
    for request_id, run in runs.items():
        complete = run["start"] is not None and run["end"] is not None
        if not complete:
            status = "incomplete"
        else:
            status = "success" if run["ok"] else "failure"
        summary[request_id] = {
            "duration_ms": run["end"] - run["start"] if complete else None,
            "tool_calls": run["tool_calls"],
            "status": status,
        }
    return summary


if __name__ == "__main__":
    print(json.dumps(aggregate(TRACE), indent=2))
