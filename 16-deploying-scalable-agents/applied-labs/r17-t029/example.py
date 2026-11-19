#!/usr/bin/env python3
"""Trace Aggregation — Evaluation Experiment (R17-T029).

Demonstrates local trace aggregation for production agent observability:
- Aggregates discrete telemetry spans by correlation ID (request ID).
- Reports duration, tool-call count, and success/failure status.
- Enforces strict telemetry privacy by completely excluding prompt contents.
- Correctly identifies missing end events as 'incomplete' rather than assigning duration zero.
- Evaluates 3 controlled batch sizes across aggregation latency, throughput, and completeness metrics.

Educational simulation: Uses pure Python 3 standard library with zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
from typing import Any, Dict, List, Optional, Union


@dataclass
class TraceEvent:
    """Individual telemetry event record representing an execution milestone."""
    request_id: str
    event_type: str  # "start", "tool_call", "end", "error"
    timestamp_ms: float
    tool_name: Optional[str] = None
    status: Optional[str] = None  # "success", "failure"
    error_message: Optional[str] = None
    prompt: Optional[str] = None  # Raw prompt data to test redaction/exclusion

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TraceEvent:
        return cls(
            request_id=str(data["request_id"]),
            event_type=str(data["event_type"]),
            timestamp_ms=float(data["timestamp_ms"]),
            tool_name=data.get("tool_name"),
            status=data.get("status"),
            error_message=data.get("error_message"),
            prompt=data.get("prompt"),
        )


@dataclass
class AggregatedRequestSummary:
    """Aggregated operational metrics for a correlated request ID.

    Guarantees:
    - prompt contents are never included in the summary.
    - requests missing end events have duration_ms = None (never 0.0).
    """
    request_id: str
    duration_ms: Optional[float]
    tool_call_count: int
    status: str  # "success", "failure", "incomplete"
    is_complete: bool
    tool_names: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "duration_ms": self.duration_ms,
            "tool_call_count": self.tool_call_count,
            "status": self.status,
            "is_complete": self.is_complete,
            "tool_names": self.tool_names,
            "error_message": self.error_message,
        }


class TraceAggregator:
    """Aggregates raw telemetry events by request ID into operational summaries."""

    def aggregate(
        self,
        events: List[Union[TraceEvent, Dict[str, Any]]],
    ) -> Dict[str, AggregatedRequestSummary]:
        """Aggregate trace events by request ID.

        Rules:
        1. Calculate duration: end.timestamp_ms - start.timestamp_ms.
        2. If no 'end' event is found, mark as incomplete with duration_ms = None (never 0.0).
        3. Count all 'tool_call' events.
        4. Exclude prompt contents entirely from resulting summaries.
        5. If 'error' event exists or end status is 'failure', mark as 'failure'.
        """
        # Group raw events by request_id
        grouped: Dict[str, List[TraceEvent]] = {}
        for item in events:
            ev = item if isinstance(item, TraceEvent) else TraceEvent.from_dict(item)
            grouped.setdefault(ev.request_id, []).append(ev)

        summaries: Dict[str, AggregatedRequestSummary] = {}

        for req_id, req_events in grouped.items():
            start_event: Optional[TraceEvent] = None
            end_event: Optional[TraceEvent] = None
            tool_calls: List[str] = []
            has_error = False
            error_msg: Optional[str] = None

            for ev in req_events:
                if ev.event_type == "start":
                    if start_event is None or ev.timestamp_ms < start_event.timestamp_ms:
                        start_event = ev
                elif ev.event_type == "tool_call":
                    tool_calls.append(ev.tool_name or "unknown_tool")
                elif ev.event_type == "end":
                    if end_event is None or ev.timestamp_ms > end_event.timestamp_ms:
                        end_event = ev
                    if ev.status == "failure":
                        has_error = True
                        if ev.error_message:
                            error_msg = ev.error_message
                elif ev.event_type == "error":
                    has_error = True
                    error_msg = ev.error_message or "Execution error encountered"

            # Check completion status
            if start_event is not None and end_event is not None:
                is_complete = True
                duration = round(end_event.timestamp_ms - start_event.timestamp_ms, 3)
                if has_error:
                    status = "failure"
                else:
                    status = "success"
            else:
                # Missing end event: marked incomplete rather than assigned duration zero!
                is_complete = False
                status = "incomplete"
                duration = None

            summary = AggregatedRequestSummary(
                request_id=req_id,
                duration_ms=duration,
                tool_call_count=len(tool_calls),
                status=status,
                is_complete=is_complete,
                tool_names=tool_calls,
                error_message=error_msg,
            )
            summaries[req_id] = summary

        return summaries


def get_canonical_benchmark_events() -> List[TraceEvent]:
    """Generates the required canonical benchmark events:

    - Request A: 2 tool calls, duration 12ms, success.
    - Request B: fails.
    - Request C: missing end event, marked incomplete rather than duration zero.
    """
    return [
        # Request A: Start at 100.0, 2 tool calls, ends at 112.0 (duration: 12ms)
        TraceEvent(
            request_id="request_A",
            event_type="start",
            timestamp_ms=100.0,
            prompt="Find user profile and update preference.",
        ),
        TraceEvent(
            request_id="request_A",
            event_type="tool_call",
            timestamp_ms=104.0,
            tool_name="get_user_profile",
        ),
        TraceEvent(
            request_id="request_A",
            event_type="tool_call",
            timestamp_ms=108.0,
            tool_name="update_user_preference",
        ),
        TraceEvent(
            request_id="request_A",
            event_type="end",
            timestamp_ms=112.0,
            status="success",
        ),

        # Request B: Start at 200.0, 1 tool call, ends with failure
        TraceEvent(
            request_id="request_B",
            event_type="start",
            timestamp_ms=200.0,
            prompt="Charge subscription renewal.",
        ),
        TraceEvent(
            request_id="request_B",
            event_type="tool_call",
            timestamp_ms=205.0,
            tool_name="process_payment",
        ),
        TraceEvent(
            request_id="request_B",
            event_type="end",
            timestamp_ms=215.0,
            status="failure",
            error_message="Card authorization declined: insufficient funds",
        ),

        # Request C: Start at 300.0, 1 tool call, missing end event
        TraceEvent(
            request_id="request_C",
            event_type="start",
            timestamp_ms=300.0,
            prompt="Stream long-running analytical report.",
        ),
        TraceEvent(
            request_id="request_C",
            event_type="tool_call",
            timestamp_ms=308.0,
            tool_name="stream_query",
        ),
        # Note: No 'end' event for Request C
    ]


def generate_synthetic_workload(num_requests: int) -> List[TraceEvent]:
    """Generates a reproducible synthetic workload of varying sizes."""
    events: List[TraceEvent] = []
    base_ts = 1000.0

    for i in range(num_requests):
        req_id = f"req_{i:04d}"
        req_start = base_ts + (i * 50.0)

        # 1. Start event
        events.append(
            TraceEvent(
                request_id=req_id,
                event_type="start",
                timestamp_ms=req_start,
                prompt=f"Confidential customer prompt for task {i}",
            )
        )

        # Vary tool count: 0, 1, 2, or 3 tools
        num_tools = i % 4
        for t in range(num_tools):
            events.append(
                TraceEvent(
                    request_id=req_id,
                    event_type="tool_call",
                    timestamp_ms=req_start + 5.0 + (t * 4.0),
                    tool_name=f"tool_step_{t}",
                )
            )

        # Every 7th request fails; every 5th request has a missing end event (incomplete)
        if i % 5 == 0:
            # Drop end event to model crash/timeout
            continue
        elif i % 7 == 0:
            events.append(
                TraceEvent(
                    request_id=req_id,
                    event_type="end",
                    timestamp_ms=req_start + 25.0,
                    status="failure",
                    error_message=f"Synthetic operational error in request {i}",
                )
            )
        else:
            events.append(
                TraceEvent(
                    request_id=req_id,
                    event_type="end",
                    timestamp_ms=req_start + 18.0,
                    status="success",
                )
            )

    return events


def run_controlled_evaluation_experiment() -> Dict[str, Any]:
    """Focus: Compare 3 controlled input sizes using duration, throughput, and completeness metrics.

    Controlled Configurations:
    - Config S (Small): 3 canonical requests (7 events)
    - Config M (Medium): 25 synthetic requests (approx 80 events)
    - Config L (Large): 100 synthetic requests (approx 320 events)
    """
    aggregator = TraceAggregator()

    configs = {
        "Config_S_Small": get_canonical_benchmark_events(),
        "Config_M_Medium": generate_synthetic_workload(25),
        "Config_L_Large": generate_synthetic_workload(100),
    }

    experiment_results: Dict[str, Any] = {}

    for config_name, workload in configs.items():
        # Measure processing duration
        t_start = time.perf_counter_ns()
        # Warmup and 50 iterations for stable timing
        iterations = 50
        summaries: Dict[str, AggregatedRequestSummary] = {}
        for _ in range(iterations):
            summaries = aggregator.aggregate(workload)
        t_end = time.perf_counter_ns()

        elapsed_total_us = (t_end - t_start) / 1000.0
        avg_run_us = elapsed_total_us / iterations
        event_count = len(workload)
        request_count = len(summaries)

        # Compute metric aggregates
        complete_count = sum(1 for s in summaries.values() if s.is_complete)
        incomplete_count = sum(1 for s in summaries.values() if not s.is_complete)
        failure_count = sum(1 for s in summaries.values() if s.status == "failure")
        success_count = sum(1 for s in summaries.values() if s.status == "success")
        total_tool_calls = sum(s.tool_call_count for s in summaries.values())

        # Verify privacy constraint: zero prompt leakage
        prompt_leakage = False
        for s in summaries.values():
            s_dict = s.to_dict()
            if "prompt" in s_dict or any("prompt" in str(v).lower() and "confidential" in str(v).lower() for v in s_dict.values()):
                prompt_leakage = True

        # Check incomplete duration invariant: none must have duration zero
        invalid_duration_zero = any(s.duration_ms == 0.0 for s in summaries.values() if not s.is_complete)

        experiment_results[config_name] = {
            "event_count": event_count,
            "request_count": request_count,
            "avg_latency_us": round(avg_run_us, 2),
            "throughput_eps": round((event_count / (avg_run_us / 1_000_000.0)), 2) if avg_run_us > 0 else 0,
            "metrics": {
                "success_count": success_count,
                "failure_count": failure_count,
                "incomplete_count": incomplete_count,
                "total_tool_calls": total_tool_calls,
                "mean_tools_per_request": round(total_tool_calls / request_count, 2) if request_count > 0 else 0,
            },
            "invariants_verified": {
                "zero_prompt_leakage": not prompt_leakage,
                "incomplete_marked_none_not_zero": not invalid_duration_zero,
            },
        }

    return experiment_results


if __name__ == "__main__":
    print("=== Trace Aggregator Canonical Verification ===")
    aggregator = TraceAggregator()
    canonical_summaries = aggregator.aggregate(get_canonical_benchmark_events())

    for req_id, summary in canonical_summaries.items():
        print(f"\n[{req_id}]")
        print(f"  Duration: {summary.duration_ms} ms")
        print(f"  Tool Calls: {summary.tool_call_count} ({summary.tool_names})")
        print(f"  Status: {summary.status} (Complete: {summary.is_complete})")
        if summary.error_message:
            print(f"  Error: {summary.error_message}")

    print("\n=== Controlled Evaluation Experiment (3 Configurations) ===")
    exp = run_controlled_evaluation_experiment()
    for cfg, data in exp.items():
        print(f"\n{cfg}:")
        print(f"  Events: {data['event_count']}, Requests: {data['request_count']}")
        print(f"  Avg Latency: {data['avg_latency_us']} µs | Throughput: {data['throughput_eps']} events/sec")
        print(f"  Outcomes: Success={data['metrics']['success_count']}, Failure={data['metrics']['failure_count']}, Incomplete={data['metrics']['incomplete_count']}")
        print(f"  Invariants: Zero Leakage={data['invariants_verified']['zero_prompt_leakage']}, Incomplete Not Zero={data['invariants_verified']['incomplete_marked_none_not_zero']}")
