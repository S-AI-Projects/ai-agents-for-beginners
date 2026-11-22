"""Unit Tests for Metacognitive Routing and Self-Calibration (R17-T050)"""

import math
import unittest

try:
    from example import (
        CONFIDENCE_THRESHOLD,
        EVIDENCE_THRESHOLD,
        AgentOutput,
        CalibrationReport,
        MetacognitiveCalibrator,
        RoutingDecision,
        route_agent_result,
        run_metacognitive_demonstration,
    )
except ImportError:
    from .example import (
        CONFIDENCE_THRESHOLD,
        EVIDENCE_THRESHOLD,
        AgentOutput,
        CalibrationReport,
        MetacognitiveCalibrator,
        RoutingDecision,
        route_agent_result,
        run_metacognitive_demonstration,
    )


class TestMetacognitiveRoutingAndCalibration(unittest.TestCase):
    """Test suite covering confidence & evidence routing and self-calibration."""

    def test_route_answer_high_confidence_sufficient_evidence(self):
        """Routing yields ANSWER when confidence >= 0.8 and evidence >= 2."""
        # Exact boundary
        self.assertEqual(route_agent_result(0.8, 2), RoutingDecision.ANSWER)
        self.assertEqual(route_agent_result(0.8, 2), "ANSWER")

        # Well above boundary
        self.assertEqual(route_agent_result(0.85, 3), RoutingDecision.ANSWER)
        self.assertEqual(route_agent_result(0.99, 5), RoutingDecision.ANSWER)
        self.assertEqual(route_agent_result(1.0, 2), RoutingDecision.ANSWER)
        self.assertEqual(route_agent_result(1.0, 100), RoutingDecision.ANSWER)

    def test_route_review_marginal_confidence_boundary(self):
        """Routing yields REVIEW when confidence < 0.8, even if evidence >= 2."""
        # Exact boundary: 0.79
        self.assertEqual(route_agent_result(0.79, 2), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.79, 2), "REVIEW")

        # Other marginal confidence values
        self.assertEqual(route_agent_result(0.7999, 2), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.7999, 10), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.5, 4), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.1, 2), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.0, 2), RoutingDecision.REVIEW)

    def test_route_review_insufficient_evidence(self):
        """Routing yields REVIEW when evidence < 2, even if confidence >= 0.8."""
        # High confidence, 1 evidence item
        self.assertEqual(route_agent_result(0.8, 1), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.85, 1), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.99, 1), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(1.0, 1), RoutingDecision.REVIEW)

        # High confidence, 0 evidence items
        self.assertEqual(route_agent_result(0.8, 0), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.95, 0), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(1.0, 0), RoutingDecision.REVIEW)

    def test_route_review_both_below_threshold(self):
        """Routing yields REVIEW when both confidence < 0.8 and evidence < 2."""
        self.assertEqual(route_agent_result(0.79, 1), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.65, 1), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.40, 0), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.0, 0), RoutingDecision.REVIEW)

    def test_invalid_confidence_raises_value_error(self):
        """Confidence values strictly outside [0.0, 1.0] raise ValueError."""
        # Strictly below 0.0
        with self.assertRaises(ValueError):
            route_agent_result(-0.01, 2)
        with self.assertRaises(ValueError):
            route_agent_result(-0.5, 3)
        with self.assertRaises(ValueError):
            route_agent_result(-1.0, 1)

        # Strictly above 1.0
        with self.assertRaises(ValueError):
            route_agent_result(1.01, 2)
        with self.assertRaises(ValueError):
            route_agent_result(1.0001, 2)
        with self.assertRaises(ValueError):
            route_agent_result(2.0, 5)
        with self.assertRaises(ValueError):
            route_agent_result(100.0, 2)

        # NaN
        with self.assertRaises(ValueError):
            route_agent_result(float("nan"), 2)

    def test_evidence_as_sequence_of_items(self):
        """Evidence passed as a collection/sequence is evaluated by its length."""
        two_sources = ["doc_flight_rules.pdf", "dot_cancellation_faq.html"]
        one_source = ["forum_post_2021.txt"]
        empty_sources = []

        # High confidence (0.85)
        self.assertEqual(route_agent_result(0.85, two_sources), RoutingDecision.ANSWER)
        self.assertEqual(route_agent_result(0.85, one_source), RoutingDecision.REVIEW)
        self.assertEqual(route_agent_result(0.85, empty_sources), RoutingDecision.REVIEW)

        # Marginal confidence (0.79)
        self.assertEqual(route_agent_result(0.79, two_sources), RoutingDecision.REVIEW)

    def test_invalid_types_raise_type_error(self):
        """Invalid types for confidence or evidence raise TypeError."""
        # Boolean passed as confidence (bool is a subclass of int in Python)
        with self.assertRaises(TypeError):
            route_agent_result(True, 2)

        # Non-numeric confidence
        with self.assertRaises(TypeError):
            route_agent_result("0.85", 2)  # type: ignore

        with self.assertRaises(TypeError):
            route_agent_result(None, 2)  # type: ignore

        # Non-sequence, non-int evidence
        with self.assertRaises(TypeError):
            route_agent_result(0.85, 2.5)  # type: ignore

        with self.assertRaises(TypeError):
            route_agent_result(0.85, None)  # type: ignore

    def test_metacognitive_calibrator_diagnostics(self):
        """MetacognitiveCalibrator correctly assesses over/under/calibrated conditions."""
        calibrator = MetacognitiveCalibrator()

        # Overconfident: high confidence, sparse evidence
        overconfident_case = AgentOutput(
            query="Change departure city",
            proposed_answer="Allowed with no fees",
            stated_confidence=0.90,
            evidence_items=["Single forum link"],
        )
        report1 = calibrator.calibrate_and_route(overconfident_case)
        self.assertEqual(report1.decision, RoutingDecision.REVIEW)
        self.assertEqual(report1.calibration_status, "OVERCONFIDENT")
        self.assertLess(report1.calibrated_confidence, report1.stated_confidence)

        # Underconfident: robust evidence, low confidence
        underconfident_case = AgentOutput(
            query="Cabin pet fee",
            proposed_answer="$125 each way",
            stated_confidence=0.75,
            evidence_items=["Policy manual §2", "Aircraft configuration chart"],
        )
        report2 = calibrator.calibrate_and_route(underconfident_case)
        self.assertEqual(report2.decision, RoutingDecision.REVIEW)
        self.assertEqual(report2.calibration_status, "UNDERCONFIDENT")

        # Well-calibrated: robust evidence, high confidence
        calibrated_case = AgentOutput(
            query="Flight refund window",
            proposed_answer="24 hours from purchase",
            stated_confidence=0.95,
            evidence_items=["Policy §4.1", "DOT guidelines"],
        )
        report3 = calibrator.calibrate_and_route(calibrated_case)
        self.assertEqual(report3.decision, RoutingDecision.ANSWER)
        self.assertEqual(report3.calibration_status, "CALIBRATED_ADEQUATE")

    def test_demonstration_run(self):
        """The concept demonstration executes cleanly and returns expected count of reports."""
        reports = run_metacognitive_demonstration()
        self.assertEqual(len(reports), 4)
        decisions = [r.decision for r in reports]
        # Case 1: ANSWER, Case 2: REVIEW (overconfident), Case 3: REVIEW (0.79), Case 4: REVIEW (0.40)
        self.assertEqual(decisions, [
            RoutingDecision.ANSWER,
            RoutingDecision.REVIEW,
            RoutingDecision.REVIEW,
            RoutingDecision.REVIEW,
        ])


if __name__ == "__main__":
    unittest.main()
