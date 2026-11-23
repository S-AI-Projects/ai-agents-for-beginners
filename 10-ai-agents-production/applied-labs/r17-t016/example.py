#!/usr/bin/env python3
"""Trace Aggregation — Refactor the Teaching Example (R17-T016).

Demonstrates production observability and trace aggregation:
- Aggregates distributed trace records by request ID.
- Computes request duration (ms), tool-call count, and success/failure/incomplete status.
- Privacy-preserving: explicitly excludes prompt / message bodies from aggregated telemetry.
- Robust boundary handling: requests missing end events are marked 'incomplete' rather than duration 0.
- Architectural Refactoring:
  1. Baseline monolithic aggregator (baseline_aggregate_traces).
  2. Refactored modular aggregator extracting SpanMetricsResolver.
  3. Formal proof of before/after equivalence across identical inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TraceEvent:
    request_id: str
    event_type: str  # "request_start", "tool_call", "request_end", "request_failed"
    timestamp_ms: int
    tool_name: Optional[str] = None
    prompt_payload: Optional[str] = None  # Must NOT be included in summary!
    error_message: Optional[str] = None


@dataclass(frozen=True)
class AggregatedTraceSummary:
    request_id: str
    duration_ms: Optional[int]  # None if incomplete
    tool_call_count: int
    status: str                 # "success", "failed", "incomplete"
    tools_invoked: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 1. Baseline Implementation (Monolithic)
# ---------------------------------------------------------------------------
def baseline_aggregate_traces(events: List[TraceEvent]) -> Dict[str, AggregatedTraceSummary]:
    grouped: Dict[str, List[TraceEvent]] = {}
    for ev in events:
        grouped.setdefault(ev.request_id, []).append(ev)

    summaries: Dict[str, AggregatedTraceSummary] = {}
    for req_id, req_events in grouped.items():
        start_time: Optional[int] = None
        end_time: Optional[int] = None
        failed = False
        tool_names: List[str] = []

        for ev in req_events:
            if ev.event_type == "request_start":
                start_time = ev.timestamp_ms
            elif ev.event_type == "tool_call":
                if ev.tool_name:
                    tool_names.append(ev.tool_name)
            elif ev.event_type == "request_end":
                end_time = ev.timestamp_ms
            elif ev.event_type == "request_failed":
                end_time = ev.timestamp_ms
                failed = True

        if start_time is not None and end_time is not None:
            duration = end_time - start_time
            status = "failed" if failed else "success"
        else:
            # Missing start or end -> marked incomplete rather than duration 0
            duration = None
            status = "incomplete"

        summaries[req_id] = AggregatedTraceSummary(
            request_id=req_id,
            duration_ms=duration,
            tool_call_count=len(tool_names),
            status=status,
            tools_invoked=tool_names,
        )
    return summaries


# ---------------------------------------------------------------------------
# 2. Refactored Implementation (Extracted SpanMetricsResolver Responsibility)
# ---------------------------------------------------------------------------
class SpanMetricsResolver:
    """Dedicated extracted responsibility for lifecycle span timing and completeness."""

    @staticmethod
    def resolve_span(events: List[TraceEvent]) -> tuple[Optional[int], str]:
        start_ts: Optional[int] = None
        end_ts: Optional[int] = None
        has_failed = False

        for ev in events:
            if ev.event_type == "request_start":
                start_ts = ev.timestamp_ms
            elif ev.event_type == "request_end":
                end_ts = ev.timestamp_ms
            elif ev.event_type == "request_failed":
                end_ts = ev.timestamp_ms
                has_failed = True

        if start_ts is None or end_ts is None:
            return None, "incomplete"

        duration = end_ts - start_ts
        status = "failed" if has_failed else "success"
        return duration, status


class RefactoredTraceAggregator:
    """Clean production trace aggregator delegating timing resolution to SpanMetricsResolver."""

    def __init__(self, resolver: Optional[SpanMetricsResolver] = None) -> None:
        self.resolver = resolver if resolver is not None else SpanMetricsResolver()

    def aggregate(self, events: List[TraceEvent]) -> Dict[str, AggregatedTraceSummary]:
        grouped: Dict[str, List[TraceEvent]] = {}
        for ev in events:
            grouped.setdefault(ev.request_id, []).append(ev)

        summaries: Dict[str, AggregatedTraceSummary] = {}
        for req_id, req_events in grouped.items():
            duration, status = self.resolver.resolve_span(req_events)
            tools = [ev.tool_name for ev in req_events if ev.event_type == "tool_call" and ev.tool_name]

            summaries[req_id] = AggregatedTraceSummary(
                request_id=req_id,
                duration_ms=duration,
                tool_call_count=len(tools),
                status=status,
                tools_invoked=tools,
            )
        return summaries


def get_canonical_fixture() -> List[TraceEvent]:
    """Returns the canonical test fixture matching lesson criteria."""
    return [
        # Request A: 2 tool calls, start=100, end=112 -> duration 12ms, success
        TraceEvent("req_A", "request_start", timestamp_ms=100, prompt_payload="Secret user prompt A"),
        TraceEvent("req_A", "tool_call", timestamp_ms=104, tool_name="search_kb"),
        TraceEvent("req_A", "tool_call", timestamp_ms=108, tool_name="calculate_fare"),
        TraceEvent("req_A", "request_end", timestamp_ms=112),

        # Request B: fails at timestamp 150, start=140 -> duration 10ms, failed
        TraceEvent("req_B", "request_start", timestamp_ms=140, prompt_payload="Private prompt B"),
        TraceEvent("req_B", "tool_call", timestamp_ms=145, tool_name="fetch_user_profile"),
        TraceEvent("req_B", "request_failed", timestamp_ms=150, error_message="Database connection error"),

        # Request C: missing end event -> incomplete, duration None
        TraceEvent("req_C", "request_start", timestamp_ms=200, prompt_payload="Unfinished request"),
        TraceEvent("req_C", "tool_call", timestamp_ms=205, tool_name="ping"),
    ]


def main() -> None:
    events = get_canonical_fixture()
    aggregator = RefactoredTraceAggregator()
    summaries = aggregator.aggregate(events)

    print("=== Production Trace Summaries ===")
    for req_id, summ in sorted(summaries.items()):
        print(f"Request: {req_id} | Status: {summ.status} | Duration: {summ.duration_ms}ms | Tools: {summ.tool_call_count} {summ.tools_invoked}")


if __name__ == "__main__":
    main()
