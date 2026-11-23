#!/usr/bin/env python3
"""Trace Aggregation — Failure and Recovery Example (R17-T018).

Demonstrates resilient production telemetry processing:
- Aggregates distributed events by request ID.
- Computes request duration, tool-call count, and status without leaking prompt payloads.
- Marks spans with missing end events as 'incomplete' (duration=None, never 0).
- Exercises a documented invalid/corrupt data case (e.g. negative timestamps or missing correlation IDs).
- Demonstrates immediate, clean recovery on the subsequent valid input.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TraceEvent:
    request_id: Optional[str]
    event_type: str
    timestamp_ms: Optional[int]
    tool_name: Optional[str] = None
    prompt_payload: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class RequestSummary:
    request_id: str
    duration_ms: Optional[int]
    tool_call_count: int
    status: str                 # "success", "failed", "incomplete", "corrupt_data"
    diagnostic_error: Optional[str] = None
    tools_invoked: List[str] = field(default_factory=list)


class ResilientTraceAggregator:
    """Aggregates trace events with explicit error detection and recovery."""

    def __init__(self) -> None:
        self.diagnostic_log: List[str] = []

    def process_event_stream(self, events: List[TraceEvent]) -> Tuple[Dict[str, RequestSummary], List[str]]:
        grouped: Dict[str, List[TraceEvent]] = {}
        anomalies: List[str] = []

        for idx, ev in enumerate(events):
            # 1. Validation for missing or empty request ID
            if not ev.request_id or not isinstance(ev.request_id, str):
                anomalies.append(f"Event at index {idx} discarded: missing or non-string request_id")
                continue

            # 2. Validation for invalid timestamps
            if ev.timestamp_ms is None or ev.timestamp_ms < 0:
                anomalies.append(f"Event for request '{ev.request_id}' at index {idx} contains invalid timestamp: {ev.timestamp_ms}")
                grouped.setdefault(ev.request_id, []).append(ev)
                continue

            grouped.setdefault(ev.request_id, []).append(ev)

        summaries: Dict[str, RequestSummary] = {}

        for req_id, req_events in grouped.items():
            # Check if any event had corrupt timestamps
            has_corrupt_ts = any(e.timestamp_ms is None or e.timestamp_ms < 0 for e in req_events)
            if has_corrupt_ts:
                summaries[req_id] = RequestSummary(
                    request_id=req_id,
                    duration_ms=None,
                    tool_call_count=0,
                    status="corrupt_data",
                    diagnostic_error="Detected corrupted or negative timestamp event",
                )
                continue

            start_ts: Optional[int] = None
            end_ts: Optional[int] = None
            failed = False
            tools: List[str] = []

            for ev in req_events:
                if ev.event_type == "request_start":
                    start_ts = ev.timestamp_ms
                elif ev.event_type == "tool_call":
                    if ev.tool_name:
                        tools.append(ev.tool_name)
                elif ev.event_type == "request_end":
                    end_ts = ev.timestamp_ms
                elif ev.event_type == "request_failed":
                    end_ts = ev.timestamp_ms
                    failed = True

            if start_ts is not None and end_ts is not None:
                duration = end_ts - start_ts
                status = "failed" if failed else "success"
            else:
                duration = None
                status = "incomplete"

            summaries[req_id] = RequestSummary(
                request_id=req_id,
                duration_ms=duration,
                tool_call_count=len(tools),
                status=status,
                tools_invoked=tools,
            )

        return summaries, anomalies


def main() -> None:
    aggregator = ResilientTraceAggregator()

    # Stream showing valid -> corrupt -> recovery
    stream = [
        # Request A: valid (2 tool calls, duration 12ms)
        TraceEvent("req_A", "request_start", 100),
        TraceEvent("req_A", "tool_call", 104, tool_name="fetch_kb"),
        TraceEvent("req_A", "tool_call", 108, tool_name="summarize"),
        TraceEvent("req_A", "request_end", 112),

        # Corrupted input: event with invalid negative timestamp
        TraceEvent("req_corrupt", "request_start", -50),

        # Request B: fails normally
        TraceEvent("req_B", "request_start", 200),
        TraceEvent("req_B", "request_failed", 215, error_message="Model timeout"),

        # Request C: missing end event -> incomplete
        TraceEvent("req_C", "request_start", 300),

        # Request D: recovery! subsequent valid request completes normally
        TraceEvent("req_D", "request_start", 400),
        TraceEvent("req_D", "tool_call", 405, tool_name="calc"),
        TraceEvent("req_D", "request_end", 420),
    ]

    summaries, anomalies = aggregator.process_event_stream(stream)
    print("Detected anomalies:", anomalies)
    for rid, summ in summaries.items():
        print(f"[{rid}] Status: {summ.status} | Duration: {summ.duration_ms}ms | Tools: {summ.tool_call_count}")


if __name__ == "__main__":
    main()
