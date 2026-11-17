"""R17-T004: Trace aggregator."""
class TraceAggregator:
    def __init__(self):
        self.events = []

    def log_event(self, request_id, event_type, timestamp_ms, payload=None):
        self.events.append({"request_id": request_id, "type": event_type, "timestamp_ms": timestamp_ms, "payload": payload or {}})

    def aggregate(self):
        grouped = {}
        for ev in self.events:
            grouped.setdefault(ev["request_id"], []).append(ev)
        summary = {}
        for rid, evs in grouped.items():
            start_ev = next((e for e in evs if e["type"] == "start"), None)
            end_ev = next((e for e in evs if e["type"] == "end"), None)
            tool_calls = sum(1 for e in evs if e["type"] == "tool_call")
            if end_ev and start_ev:
                dur = end_ev["timestamp_ms"] - start_ev["timestamp_ms"]
                status = end_ev["payload"].get("status", "success")
            else:
                dur = None
                status = "incomplete"
            summary[rid] = {"request_id": rid, "duration_ms": dur, "tool_calls": tool_calls, "status": status}
        return summary
