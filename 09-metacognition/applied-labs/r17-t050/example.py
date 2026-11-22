"""Applied Lab: Metacognitive Routing and Self-Calibration (R17-T050)

Lesson Alignment:
09-metacognition (Metacognition in AI Agents)

Goal & Core Contract:
- Route local agent results based on confidence and evidence thresholds:
  - confidence >= 0.8 AND evidence >= 2 -> ANSWER
  - confidence < 0.8 (e.g. 0.79) OR evidence < 2 -> REVIEW
  - Confidence outside [0.0, 1.0] must be rejected with ValueError.
- Runnable concept example: connect inputs/outputs directly to metacognitive self-calibration.
- Pure Python 3 standard library with zero external dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Sequence, Union


class RoutingDecision(str, Enum):
    """Routing decisions for agent responses."""
    ANSWER = "ANSWER"
    REVIEW = "REVIEW"

    def __str__(self) -> str:
        return self.value


CONFIDENCE_THRESHOLD: float = 0.8
EVIDENCE_THRESHOLD: int = 2


def route_agent_result(
    confidence: float,
    evidence: Union[int, Sequence[Any]],
) -> RoutingDecision:
    """Routes an agent result based on metacognitive confidence and evidence thresholds.

    Rules:
    - If confidence < 0.0 or confidence > 1.0 (or NaN): raises ValueError.
    - If confidence >= 0.8 AND evidence >= 2: returns RoutingDecision.ANSWER.
    - If confidence < 0.8 (e.g. 0.79) OR evidence < 2 (e.g. 1, 0): returns RoutingDecision.REVIEW.
    """
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise TypeError(f"Confidence must be a numeric float/int, got {type(confidence).__name__}")

    if math.isnan(confidence) or confidence < 0.0 or confidence > 1.0:
        raise ValueError(
            f"Confidence {confidence} is outside valid range [0.0, 1.0]."
        )

    if isinstance(evidence, int):
        evidence_count = evidence
    elif hasattr(evidence, "__len__"):
        evidence_count = len(evidence)
    else:
        raise TypeError("Evidence must be an integer count or a sequence of evidence items.")

    if confidence >= CONFIDENCE_THRESHOLD and evidence_count >= EVIDENCE_THRESHOLD:
        return RoutingDecision.ANSWER
    else:
        return RoutingDecision.REVIEW


@dataclass
class AgentOutput:
    """Raw output from an agent task or reasoning loop."""
    query: str
    proposed_answer: str
    stated_confidence: float
    evidence_items: List[str] = field(default_factory=list)


@dataclass
class CalibrationReport:
    """Detailed metacognitive evaluation and calibration report."""
    query: str
    proposed_answer: str
    stated_confidence: float
    calibrated_confidence: float
    evidence_count: int
    decision: RoutingDecision
    calibration_status: str
    rationale: str


class MetacognitiveCalibrator:
    """Self-calibrating metacognitive monitor for agent reasoning outputs.

    Connects agent outputs directly to metacognitive self-calibration:
    1. Evaluates alignment between stated subjective confidence and empirical evidence.
    2. Identifies cognitive biases:
       - Overconfidence: High stated confidence (> 0.8) with sparse evidence (< 2 items).
       - Underconfidence: Low stated confidence (< 0.8) despite solid evidence (>= 2 items).
       - Well-calibrated: Stated confidence accurately mirrors empirical evidence support.
    3. Computes a calibrated confidence score adjusted for evidence support.
    4. Routes the final action to ANSWER (autonomous emission) or REVIEW (human/expert oversight).
    """

    def __init__(
        self,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        evidence_threshold: int = EVIDENCE_THRESHOLD,
    ):
        self.confidence_threshold = confidence_threshold
        self.evidence_threshold = evidence_threshold

    def calibrate_and_route(self, agent_output: AgentOutput) -> CalibrationReport:
        """Evaluates an agent output, performs self-calibration, and decides routing."""
        # 1. Base contract routing
        decision = route_agent_result(
            confidence=agent_output.stated_confidence,
            evidence=agent_output.evidence_items,
        )

        stated = agent_output.stated_confidence
        evidence_count = len(agent_output.evidence_items)

        # 2. Metacognitive self-calibration reasoning
        # Estimate empirical evidence backing (evidence support factor)
        # 0 items -> 0.2 factor, 1 item -> 0.6 factor, 2+ items -> 1.0 factor
        if evidence_count >= self.evidence_threshold:
            evidence_factor = 1.0
        elif evidence_count == 1:
            evidence_factor = 0.75
        else:
            evidence_factor = 0.3

        calibrated = round(stated * evidence_factor, 4)

        # Diagnose calibration state
        if stated >= self.confidence_threshold and evidence_count < self.evidence_threshold:
            calibration_status = "OVERCONFIDENT"
            rationale = (
                f"Agent expressed high confidence ({stated:.2f}) but provided only "
                f"{evidence_count} evidence items (required: {self.evidence_threshold}). "
                f"Gated to REVIEW to prevent hallucination propagation."
            )
        elif stated < self.confidence_threshold and evidence_count >= self.evidence_threshold:
            calibration_status = "UNDERCONFIDENT"
            rationale = (
                f"Agent provided robust evidence ({evidence_count} items) but expressed "
                f"conservative confidence ({stated:.2f} < {self.confidence_threshold:.2f}). "
                f"Routed to REVIEW for safety verification."
            )
        elif stated >= self.confidence_threshold and evidence_count >= self.evidence_threshold:
            calibration_status = "CALIBRATED_ADEQUATE"
            rationale = (
                f"Agent demonstrated high confidence ({stated:.2f} >= {self.confidence_threshold:.2f}) "
                f"backed by sufficient empirical evidence ({evidence_count} >= {self.evidence_threshold}). "
                f"Approved for immediate autonomous ANSWER."
            )
        else:
            calibration_status = "UNCERTAIN_INSUFFICIENT"
            rationale = (
                f"Low confidence ({stated:.2f}) and insufficient evidence ({evidence_count}). "
                f"Routed to REVIEW for human inspection."
            )

        return CalibrationReport(
            query=agent_output.query,
            proposed_answer=agent_output.proposed_answer,
            stated_confidence=stated,
            calibrated_confidence=calibrated,
            evidence_count=evidence_count,
            decision=decision,
            calibration_status=calibration_status,
            rationale=rationale,
        )


def run_metacognitive_demonstration() -> List[CalibrationReport]:
    """Runs a demonstration connecting varied inputs to metacognitive calibration & routing."""
    sample_cases = [
        AgentOutput(
            query="What is the refund policy for Contoso basic flight bookings?",
            proposed_answer="Refundable within 24 hours of purchase if departure is >= 7 days away.",
            stated_confidence=0.92,
            evidence_items=[
                "Contoso Terms of Carriage §4.1 (24-hour grace window)",
                "DOT airline cancellation requirement guidelines",
            ],
        ),
        AgentOutput(
            query="Can passenger change departure city on non-flexible ticket?",
            proposed_answer="Yes, without paying any fare difference.",
            stated_confidence=0.88,
            evidence_items=[
                "Customer forum post from 2021 (single unverified source)",
            ],
        ),
        AgentOutput(
            query="Are pets allowed in the cabin on cross-country flights?",
            proposed_answer="Small dogs and cats in approved carriers are permitted for an extra fee.",
            stated_confidence=0.79,  # Boundary test case: exactly 0.79 with 2 evidence items
            evidence_items=[
                "Contoso Pet Policy Guide 2026",
                "Aircraft configuration cabin pet allowance table",
            ],
        ),
        AgentOutput(
            query="What is the lounge access fee for economy ticket holders?",
            proposed_answer="Lounge access is $45 per person at Terminal 2.",
            stated_confidence=0.40,
            evidence_items=[],
        ),
    ]

    calibrator = MetacognitiveCalibrator()
    reports = []
    print("=" * 70)
    print("Metacognitive Self-Calibration and Result Routing Demonstration")
    print("=" * 70)

    for i, case in enumerate(sample_cases, 1):
        report = calibrator.calibrate_and_route(case)
        reports.append(report)
        print(f"\n[Case {i}] Query: {report.query}")
        print(f"  Stated Confidence   : {report.stated_confidence:.2f}")
        print(f"  Evidence Count      : {report.evidence_count}")
        print(f"  Calibrated Score    : {report.calibrated_confidence:.2f}")
        print(f"  Calibration Status  : {report.calibration_status}")
        print(f"  Routing Decision    : >>> {report.decision} <<<")
        print(f"  Rationale           : {report.rationale}")

    print("\n" + "=" * 70)
    print("Core Boundary Verification:")
    print("  confidence=0.80, evidence=2 ->", route_agent_result(0.80, 2))
    print("  confidence=0.79, evidence=2 ->", route_agent_result(0.79, 2))
    print("  confidence=0.80, evidence=1 ->", route_agent_result(0.80, 1))
    print("  confidence=0.79, evidence=1 ->", route_agent_result(0.79, 1))

    try:
        route_agent_result(1.2, 2)
    except ValueError as e:
        print("  confidence=1.20, evidence=2 -> Rejection:", e)

    try:
        route_agent_result(-0.05, 2)
    except ValueError as e:
        print("  confidence=-0.05, evidence=2 -> Rejection:", e)

    print("=" * 70)
    return reports


if __name__ == "__main__":
    run_metacognitive_demonstration()
