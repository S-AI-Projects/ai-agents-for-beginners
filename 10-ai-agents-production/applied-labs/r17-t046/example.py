"""Applied Lab: Production Trace Aggregation and Privacy Safeguarding (R17-T046)

Lesson Alignment:
10-ai-agents-production (Observability, Telemetry & Evaluation)

Contract & Goals:
- Aggregate telemetry trace events by request ID.
- Report metrics per request: duration (ms), tool-call count, and status (SUCCESS / FAILED / INCOMPLETE).
- Canonical Fixtures:
    * Request A: 2 tool calls, duration exactly 12ms, status SUCCESS.
    * Request B: Encounters error, status FAILED.
    * Request C: Missing end event, marked status INCOMPLETE with duration None (not 0).
- Privacy Safeguarding: Prompt contents and raw inputs are strictly omitted from aggregated metrics.
- Worked Example: Provides clear input-to-output explanation with assertions and demonstrations.
- Zero external dependencies: pure Python 3 standard library.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class TraceEvent:
    """Represents a discrete telemetry event in an agent's execution trace."""
    event_type: str        # 'START', 'TOOL_CALL', 'END', 'ERROR'
    request_id: str        # Unique correlation ID for the request
    timestamp_ms: float    # Monotonic or epoch timestamp in milliseconds
    payload: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TraceEvent({self.event_type} @ {self.timestamp_ms}ms, req={self.request_id})"


@dataclass(frozen=True)
class AggregatedMetrics:
    """Aggregated production metrics for an individual agent request.
    
    Privacy Contract:
    Prompt text, user queries, and raw conversation payloads are strictly excluded
    from this schema to safeguard privacy and comply with data minimization principles.
    """
    request_id: str
    duration_ms: Optional[float]
    tool_call_count: int
    status: str  # 'SUCCESS', 'FAILED', 'INCOMPLETE'

    def to_dict(self) -> Dict[str, Any]:
        """Serializes metrics to a dictionary without sensitive prompt data."""
        return asdict(self)


# Canonical Worked Example Event Stream
CANONICAL_TRACE_EVENTS: List[Dict[str, Any]] = [
    # Request A: Complete successful execution (2 tool calls, duration 12ms)
    {
        "event_type": "START",
        "request_id": "A",
        "timestamp_ms": 1000.0,
        "payload": {"prompt": "User query: calculate annual budget and exchange rates", "user_id": "usr-123"},
    },
    {
        "event_type": "TOOL_CALL",
        "request_id": "A",
        "timestamp_ms": 1004.0,
        "payload": {"tool_name": "currency_converter", "args": {"from": "USD", "to": "EUR"}},
    },
    {
        "event_type": "TOOL_CALL",
        "request_id": "A",
        "timestamp_ms": 1009.0,
        "payload": {"tool_name": "budget_calculator", "args": {"base": 50000}},
    },
    {
        "event_type": "END",
        "request_id": "A",
        "timestamp_ms": 1012.0,
        "payload": {"status": "SUCCESS", "output_tokens": 142},
    },

    # Request B: Failed execution
    {
        "event_type": "START",
        "request_id": "B",
        "timestamp_ms": 2000.0,
        "payload": {"prompt": "User query: execute confidential contract transfer", "user_id": "usr-456"},
    },
    {
        "event_type": "TOOL_CALL",
        "request_id": "B",
        "timestamp_ms": 2005.0,
        "payload": {"tool_name": "smart_contract_signer", "args": {"tx_id": "0x987"}},
    },
    {
        "event_type": "ERROR",
        "request_id": "B",
        "timestamp_ms": 2018.0,
        "payload": {"error": "AuthenticationFailedException", "error_code": 401},
    },

    # Request C: Incomplete execution (Missing end event)
    {
        "event_type": "START",
        "request_id": "C",
        "timestamp_ms": 3000.0,
        "payload": {"prompt": "User query: stream real-time sensor telemetry", "user_id": "usr-789"},
    },
    {
        "event_type": "TOOL_CALL",
        "request_id": "C",
        "timestamp_ms": 3015.0,
        "payload": {"tool_name": "iot_sensor_stream", "args": {"sensor_id": "temp-1"}},
    },
    # Notice: No END or ERROR event emitted for Request C
]


def aggregate_trace_events(
    events: List[Union[TraceEvent, Dict[str, Any]]]
) -> Dict[str, AggregatedMetrics]:
    """Aggregates a stream of raw telemetry events into structured metrics by request ID.

    Aggregation Rules:
    1. Group all events by `request_id`.
    2. Count `TOOL_CALL` events per request.
    3. Determine execution duration:
       - If both START and END/ERROR events exist: duration_ms = end_timestamp - start_timestamp.
       - If END or ERROR is missing: duration_ms is None (explicitly NOT 0).
    4. Determine status:
       - 'SUCCESS': If completed with an END event (or status == 'SUCCESS').
       - 'FAILED': If terminated with an ERROR event.
       - 'INCOMPLETE': If no terminating END or ERROR event is present.
    5. Privacy Safeguard: Prompt contents, user queries, and tool payloads are
       strictly excluded from the output metrics.

    Args:
        events: List of TraceEvent instances or event dictionaries.

    Returns:
        Dictionary mapping request_id -> AggregatedMetrics.
    """
    # Group events by request ID in encounter order
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for item in events:
        if isinstance(item, TraceEvent):
            event_dict = {
                "event_type": item.event_type.upper(),
                "request_id": item.request_id,
                "timestamp_ms": item.timestamp_ms,
                "payload": item.payload,
            }
        elif isinstance(item, dict):
            event_dict = {
                "event_type": str(item.get("event_type", "")).upper(),
                "request_id": str(item.get("request_id", "")),
                "timestamp_ms": float(item.get("timestamp_ms", 0.0)),
                "payload": item.get("payload", item),
            }
        else:
            raise ValueError(f"Unsupported event type: {type(item)}")

        req_id = event_dict["request_id"]
        if req_id not in grouped:
            grouped[req_id] = []
        grouped[req_id].append(event_dict)

    results: Dict[str, AggregatedMetrics] = {}

    for req_id, req_events in grouped.items():
        start_time: Optional[float] = None
        end_time: Optional[float] = None
        tool_count: int = 0
        has_error: bool = False
        has_end: bool = False

        for ev in req_events:
            etype = ev["event_type"]
            t = ev["timestamp_ms"]

            if etype == "START":
                if start_time is None or t < start_time:
                    start_time = t
            elif etype == "TOOL_CALL":
                tool_count += 1
            elif etype == "END":
                has_end = True
                end_time = t
            elif etype == "ERROR":
                has_error = True
                end_time = t

        # Determine status and duration
        duration_ms: Optional[float] = None

        if has_error:
            status = "FAILED"
            if start_time is not None and end_time is not None and end_time >= start_time:
                duration_ms = end_time - start_time
        elif has_end:
            status = "SUCCESS"
            if start_time is not None and end_time is not None and end_time >= start_time:
                duration_ms = end_time - start_time
        else:
            status = "INCOMPLETE"
            # Explicit contract requirement: duration is None for incomplete requests, NOT 0
            duration_ms = None

        results[req_id] = AggregatedMetrics(
            request_id=req_id,
            duration_ms=duration_ms,
            tool_call_count=tool_count,
            status=status,
        )

    return results


def run_worked_example() -> Dict[str, AggregatedMetrics]:
    """Executes the canonical worked example and asserts core contract satisfaction."""
    aggregated = aggregate_trace_events(CANONICAL_TRACE_EVENTS)

    # 1. Check Request A: 2 tool calls, duration 12ms, SUCCESS
    metric_a = aggregated["A"]
    assert metric_a.tool_call_count == 2, f"Expected 2 tool calls for A, got {metric_a.tool_call_count}"
    assert metric_a.duration_ms == 12.0, f"Expected duration 12.0ms for A, got {metric_a.duration_ms}"
    assert metric_a.status == "SUCCESS", f"Expected SUCCESS for A, got {metric_a.status}"

    # 2. Check Request B: FAILED
    metric_b = aggregated["B"]
    assert metric_b.status == "FAILED", f"Expected FAILED for B, got {metric_b.status}"
    assert metric_b.tool_call_count == 1, f"Expected 1 tool call for B, got {metric_b.tool_call_count}"

    # 3. Check Request C: INCOMPLETE with duration None (not 0)
    metric_c = aggregated["C"]
    assert metric_c.status == "INCOMPLETE", f"Expected INCOMPLETE for C, got {metric_c.status}"
    assert metric_c.duration_ms is None, f"Expected duration None for C, got {metric_c.duration_ms}"
    assert metric_c.duration_ms != 0, "Duration for incomplete request must not be 0"

    # 4. Check Privacy: No prompt text leaked into metrics
    for m in aggregated.values():
        d = m.to_dict()
        assert "prompt" not in d, "Privacy leak: prompt field present in aggregated metrics"
        for v in d.values():
            if isinstance(v, str):
                assert "User query" not in v, f"Privacy leak: user query detected in {v}"

    return aggregated


def main():
    print("=== Production Trace Aggregation & Privacy Safeguarding (R17-T046) ===\n")

    print("Input Raw Trace Events:")
    for ev in CANONICAL_TRACE_EVENTS:
        prompt_snippet = ev.get("payload", {}).get("prompt", "")
        if prompt_snippet:
            print(f"  [{ev['request_id']}] {ev['event_type']:<9} @ {ev['timestamp_ms']}ms | Prompt: '{prompt_snippet[:40]}...'")
        else:
            print(f"  [{ev['request_id']}] {ev['event_type']:<9} @ {ev['timestamp_ms']}ms | Payload: {ev.get('payload', {})}")

    print("\nProcessing Aggregation...")
    results = run_worked_example()

    print("\nAggregated Metrics by Request ID (Privacy Safeguarded):")
    for req_id, m in results.items():
        dur_str = f"{m.duration_ms:.1f} ms" if m.duration_ms is not None else "None (INCOMPLETE)"
        print(f"  Request '{req_id}': Status = {m.status:<10} | Tool Calls = {m.tool_call_count} | Duration = {dur_str}")

    print("\nPrivacy Audit Verification:")
    for req_id, m in results.items():
        serialized = m.to_dict()
        keys_present = list(serialized.keys())
        has_prompt = "prompt" in serialized
        print(f"  Request '{req_id}': Fields = {keys_present} | Prompt Excluded = {not has_prompt}")

    print("\nAll worked example assertions verified successfully.")


if __name__ == "__main__":
    main()
