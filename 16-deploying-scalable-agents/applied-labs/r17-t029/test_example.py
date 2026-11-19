#!/usr/bin/env python3
"""Unit tests for Trace Aggregator and Evaluation Experiment (Task R17-T029).

Validates canonical telemetry contract: Request A (2 tools, 12ms), Request B (failure),
incomplete span handling (None duration, not zero), privacy/prompt exclusion, and
controlled evaluation experiment metrics.
"""

import unittest
from typing import Dict, Any

from example import (
    AggregatedRequestSummary,
    TraceAggregator,
    TraceEvent,
    get_canonical_benchmark_events,
    run_controlled_evaluation_experiment,
)


class TestTraceAggregatorCanonicalContract(unittest.TestCase):
    """Verifies the core canonical contract required by Task R17-T029."""

    def setUp(self) -> None:
        self.aggregator = TraceAggregator()
        self.events = get_canonical_benchmark_events()
        self.summaries = self.aggregator.aggregate(self.events)

    def test_request_a_metrics(self) -> None:
        """Request A has two tool calls and duration 12ms; terminates successfully."""
        summary = self.summaries.get("request_A")
        self.assertIsNotNone(summary)
        assert summary is not None

        self.assertEqual(summary.duration_ms, 12.0)
        self.assertEqual(summary.tool_call_count, 2)
        self.assertEqual(summary.status, "success")
        self.assertTrue(summary.is_complete)
        self.assertEqual(summary.tool_names, ["get_user_profile", "update_user_preference"])

    def test_request_b_failure(self) -> None:
        """Request B fails with appropriate status and error telemetry."""
        summary = self.summaries.get("request_B")
        self.assertIsNotNone(summary)
        assert summary is not None

        self.assertEqual(summary.status, "failure")
        self.assertTrue(summary.is_complete)
        self.assertEqual(summary.tool_call_count, 1)
        self.assertIn("insufficient funds", summary.error_message or "")

    def test_missing_end_events_marked_incomplete_not_zero(self) -> None:
        """Missing end events are marked incomplete rather than assigned duration zero."""
        summary = self.summaries.get("request_C")
        self.assertIsNotNone(summary)
        assert summary is not None

        self.assertEqual(summary.status, "incomplete")
        self.assertFalse(summary.is_complete)
        # Invariant: duration_ms must be None, NOT 0.0 or 0
        self.assertIsNone(summary.duration_ms)
        self.assertNotEqual(summary.duration_ms, 0.0)
        self.assertNotEqual(summary.duration_ms, 0)
        self.assertEqual(summary.tool_call_count, 1)


class TestTracePrivacyAndGuards(unittest.TestCase):
    """Verifies telemetry privacy and security invariants."""

    def setUp(self) -> None:
        self.aggregator = TraceAggregator()

    def test_prompt_contents_completely_excluded(self) -> None:
        """Aggregated summaries must never expose or contain raw prompt contents."""
        secret_prompt = "CONFIDENTIAL_PATIENT_SSN_12345"
        raw_events = [
            TraceEvent(
                request_id="req_priv",
                event_type="start",
                timestamp_ms=10.0,
                prompt=secret_prompt,
            ),
            TraceEvent(
                request_id="req_priv",
                event_type="end",
                timestamp_ms=20.0,
                status="success",
            ),
        ]
        summaries = self.aggregator.aggregate(raw_events)
        summary = summaries["req_priv"]

        summary_dict = summary.to_dict()
        # Prompt key must not exist in output dictionary
        self.assertNotIn("prompt", summary_dict)
        # Secret prompt string must not be present anywhere in serialized summary
        serialized = str(summary_dict)
        self.assertNotIn(secret_prompt, serialized)

    def test_empty_event_stream_returns_empty_dict(self) -> None:
        """Aggregator handles empty event lists safely."""
        summaries = self.aggregator.aggregate([])
        self.assertEqual(summaries, {})


class TestControlledEvaluationExperiment(unittest.TestCase):
    """Verifies the controlled evaluation experiment comparing 3 input configurations."""

    def test_experiment_runs_three_configurations(self) -> None:
        """Experiment must evaluate Small, Medium, and Large configurations."""
        exp = run_controlled_evaluation_experiment()

        expected_configs = ["Config_S_Small", "Config_M_Medium", "Config_L_Large"]
        for cfg in expected_configs:
            self.assertIn(cfg, exp)
            cfg_data = exp[cfg]
            self.assertGreater(cfg_data["event_count"], 0)
            self.assertGreater(cfg_data["request_count"], 0)
            self.assertGreater(cfg_data["avg_latency_us"], 0.0)
            self.assertGreater(cfg_data["throughput_eps"], 0.0)
            # Invariants must hold across all configurations
            self.assertTrue(cfg_data["invariants_verified"]["zero_prompt_leakage"])
            self.assertTrue(cfg_data["invariants_verified"]["incomplete_marked_none_not_zero"])

    def test_observed_trade_offs_monotonic_latency(self) -> None:
        """Processing latency scales predictably with input size (S < M < L)."""
        exp = run_controlled_evaluation_experiment()
        lat_s = exp["Config_S_Small"]["avg_latency_us"]
        lat_m = exp["Config_M_Medium"]["avg_latency_us"]
        lat_l = exp["Config_L_Large"]["avg_latency_us"]

        self.assertLess(lat_s, lat_m)
        self.assertLess(lat_m, lat_l)


if __name__ == "__main__":
    unittest.main()
