#!/usr/bin/env python3
"""Model-Manifest Selection — Scenario Assessment (R17-T030).

Demonstrates local model selection against explicit hardware and context constraints:
- Evaluates synthetic model manifest entries using RAM budget and requested context window.
- Produces explicit rejection reasons for excluded models.
- Fixture A (RAM 4 / context 2048) and Fixture B (RAM 8 / context 4096) with budget RAM 6
  and requested context 1024 admits only Fixture A.
- Includes 3 applied scenario assessment questions: predict an output, diagnose a failure,
  and choose a boundary policy, complete with rationales and executable checks.

Educational simulation: Uses pure Python 3 standard library with zero external dependencies.
Values are invented teaching fixtures, not claims about named real models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any, Callable, Dict, List, Optional


class RejectionCode(str, Enum):
    """Machine-readable rejection error codes."""
    EXCEEDS_RAM_BUDGET = "EXCEEDS_RAM_BUDGET"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    MISSING_TOOL_SUPPORT = "MISSING_TOOL_SUPPORT"


@dataclass
class ModelEntry:
    """Synthetic model metadata in the local manifest."""
    id: str
    name: str
    required_ram_gb: int
    max_context_tokens: int
    supports_tools: bool = True
    quantization: str = "q4_k_m"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "required_ram_gb": self.required_ram_gb,
            "max_context_tokens": self.max_context_tokens,
            "supports_tools": self.supports_tools,
            "quantization": self.quantization,
        }


@dataclass
class RejectionRecord:
    """Detailed rejection diagnostic for an excluded model."""
    code: RejectionCode
    message: str
    remediation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message,
            "remediation": self.remediation,
        }


@dataclass
class SelectionResult:
    """Result of manifest selection query."""
    ram_budget_gb: int
    requested_context_tokens: int
    eligible_models: List[ModelEntry]
    excluded_models: Dict[str, List[RejectionRecord]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ram_budget_gb": self.ram_budget_gb,
            "requested_context_tokens": self.requested_context_tokens,
            "admitted_model_ids": [m.id for m in self.eligible_models],
            "eligible_models": [m.to_dict() for m in self.eligible_models],
            "excluded_models": {
                model_id: [r.to_dict() for r in reasons]
                for model_id, reasons in self.excluded_models.items()
            },
        }


# Canonical teaching manifest fixtures
TEACHING_MANIFEST: List[ModelEntry] = [
    ModelEntry(
        id="fixture_a",
        name="Teaching-SLM-Small (Fixture A)",
        required_ram_gb=4,
        max_context_tokens=2048,
        supports_tools=True,
    ),
    ModelEntry(
        id="fixture_b",
        name="Teaching-SLM-Large (Fixture B)",
        required_ram_gb=8,
        max_context_tokens=4096,
        supports_tools=True,
    ),
    ModelEntry(
        id="fixture_c",
        name="Teaching-SLM-Micro (Fixture C)",
        required_ram_gb=2,
        max_context_tokens=512,
        supports_tools=False,
    ),
]


class ManifestSelector:
    """Selects eligible models from a manifest given operational constraints."""

    def __init__(self, manifest: Optional[List[ModelEntry]] = None) -> None:
        self.manifest = manifest if manifest is not None else list(TEACHING_MANIFEST)

    def select(
        self,
        ram_budget_gb: int,
        requested_context_tokens: int,
        require_tools: bool = True,
    ) -> SelectionResult:
        """Filter manifest models based on hardware constraints and requirements.

        Boundary Policy:
        - RAM: model.required_ram_gb <= ram_budget_gb (inclusive)
        - Context: model.max_context_tokens >= requested_context_tokens (inclusive)
        - Tools: model.supports_tools == True (if require_tools=True)
        """
        eligible: List[ModelEntry] = []
        excluded: Dict[str, List[RejectionRecord]] = {}

        for model in self.manifest:
            reasons: List[RejectionRecord] = []

            # 1. RAM check
            if model.required_ram_gb > ram_budget_gb:
                reasons.append(
                    RejectionRecord(
                        code=RejectionCode.EXCEEDS_RAM_BUDGET,
                        message=(
                            f"Model requires {model.required_ram_gb} GB RAM, "
                            f"exceeding budget of {ram_budget_gb} GB."
                        ),
                        remediation=(
                            f"Increase workstation RAM allocation or select a smaller model."
                        ),
                    )
                )

            # 2. Context window check
            if model.max_context_tokens < requested_context_tokens:
                reasons.append(
                    RejectionRecord(
                        code=RejectionCode.INSUFFICIENT_CONTEXT,
                        message=(
                            f"Model maximum context window ({model.max_context_tokens} tokens) "
                            f"is less than requested ({requested_context_tokens} tokens)."
                        ),
                        remediation=(
                            "Reduce prompt/chunk context size or pick an extended-context model."
                        ),
                    )
                )

            # 3. Tool-calling capability check
            if require_tools and not model.supports_tools:
                reasons.append(
                    RejectionRecord(
                        code=RejectionCode.MISSING_TOOL_SUPPORT,
                        message="Model does not support function/tool calling required for agentic workflows.",
                        remediation="Select a model fine-tuned for tool execution (e.g. Qwen function calling).",
                    )
                )

            if reasons:
                excluded[model.id] = reasons
            else:
                eligible.append(model)

        return SelectionResult(
            ram_budget_gb=ram_budget_gb,
            requested_context_tokens=requested_context_tokens,
            eligible_models=eligible,
            excluded_models=excluded,
        )


# ============================================================================
# Focus: Three Applied Assessment Questions
# ============================================================================

def check_q1_predict_output() -> bool:
    """Executable check for Question 1: Predict an Output."""
    selector = ManifestSelector()
    res = selector.select(ram_budget_gb=6, requested_context_tokens=1024, require_tools=True)
    admitted_ids = [m.id for m in res.eligible_models]
    # Prediction: Only Fixture A is admitted
    return admitted_ids == ["fixture_a"]


def check_q2_diagnose_failure() -> bool:
    """Executable check for Question 2: Diagnose a Failure."""
    selector = ManifestSelector()
    # High RAM (16GB) but oversized context request (8192 tokens)
    res = selector.select(ram_budget_gb=16, requested_context_tokens=8192, require_tools=True)
    if res.eligible_models:
        return False
    # Verify both fixture_a and fixture_b are excluded specifically for INSUFFICIENT_CONTEXT
    for mid in ["fixture_a", "fixture_b"]:
        if mid not in res.excluded_models:
            return False
        codes = [r.code for r in res.excluded_models[mid]]
        if RejectionCode.INSUFFICIENT_CONTEXT not in codes:
            return False
        if RejectionCode.EXCEEDS_RAM_BUDGET in codes:
            # 16GB RAM must NOT fail on RAM
            return False
    return True


def check_q3_boundary_policy() -> bool:
    """Executable check for Question 3: Choose a Boundary Policy."""
    selector = ManifestSelector()
    # Boundary test: RAM exactly equals model requirement (4GB), context exactly equals (2048)
    res = selector.select(ram_budget_gb=4, requested_context_tokens=2048, require_tools=True)
    admitted_ids = [m.id for m in res.eligible_models]
    # Under inclusive boundary policy (<= and >=), Fixture A must be admitted
    return "fixture_a" in admitted_ids and len(admitted_ids) == 1


APPLIED_QUESTIONS: Dict[str, Dict[str, Any]] = {
    "question_1_predict_output": {
        "title": "Predict an Output",
        "scenario": (
            "Given the teaching manifest containing Fixture A (RAM 4 GB, context 2048) and "
            "Fixture B (RAM 8 GB, context 4096), what models are admitted with a RAM budget "
            "of 6 GB and requested context of 1024 tokens?"
        ),
        "expected_answer": ["fixture_a"],
        "rationale": (
            "Fixture A requires 4 GB RAM (<= 6 GB budget) and provides 2048 tokens (>= 1024 tokens), "
            "satisfying both constraints. Fixture B requires 8 GB RAM (> 6 GB budget) and is excluded."
        ),
        "check": check_q1_predict_output,
    },
    "question_2_diagnose_failure": {
        "title": "Diagnose a Failure",
        "scenario": (
            "A developer running on a high-spec workstation with 16 GB RAM requests an 8192-token "
            "context window for a large RAG query. Both Fixture A and Fixture B are rejected. "
            "Diagnose why the selection failed."
        ),
        "expected_answer": "INSUFFICIENT_CONTEXT for all candidate models",
        "rationale": (
            "Although 16 GB RAM exceeds the RAM requirements of both Fixture A (4 GB) and "
            "Fixture B (8 GB), neither model supports an 8192-token context window (Fixture A caps at "
            "2048 tokens, and Fixture B caps at 4096 tokens). The failure is diagnosed as context starvation."
        ),
        "check": check_q2_diagnose_failure,
    },
    "question_3_boundary_policy": {
        "title": "Choose a Boundary Policy",
        "scenario": (
            "When evaluating a model whose required RAM exactly matches the workstation budget "
            "(e.g., 4 GB required on a 4 GB machine) and whose context window exactly matches "
            "the requested context (2048 tokens), should the selection policy be inclusive or strict?"
        ),
        "expected_answer": "Inclusive policy (<= RAM, >= Context), admitting exact-fit models",
        "rationale": (
            "An inclusive comparison policy allows exact-fit allocations, maximizing hardware utilization. "
            "A strict policy (< RAM or > Context) would reject viable exact matches, causing unnecessary "
            "workstation stalls or unwanted fallbacks."
        ),
        "check": check_q3_boundary_policy,
    },
}


def run_demo() -> Dict[str, Any]:
    """Execute canonical selection and run assessment checks."""
    selector = ManifestSelector()

    # Canonical scenario: budget RAM 6, context 1024
    canonical_result = selector.select(ram_budget_gb=6, requested_context_tokens=1024)

    # Run assessment checks
    question_evaluations = {}
    for q_key, q_data in APPLIED_QUESTIONS.items():
        is_passed = q_data["check"]()
        question_evaluations[q_key] = {
            "title": q_data["title"],
            "expected_answer": q_data["expected_answer"],
            "rationale": q_data["rationale"],
            "check_passed": is_passed,
        }

    return {
        "canonical_selection": canonical_result.to_dict(),
        "applied_questions": question_evaluations,
    }


if __name__ == "__main__":
    demo = run_demo()
    print("=== Canonical Manifest Selection Result ===")
    can = demo["canonical_selection"]
    print(f"RAM Budget: {can['ram_budget_gb']} GB, Requested Context: {can['requested_context_tokens']} tokens")
    print(f"Admitted Models: {can['admitted_model_ids']}")
    print("Excluded Models & Reasons:")
    for mid, reasons in can["excluded_models"].items():
        print(f"  [{mid}]: {reasons[0]['code']} -> {reasons[0]['message']}")

    print("\n=== Applied Scenario Assessment (3 Questions) ===")
    for q_id, q_eval in demo["applied_questions"].items():
        status = "PASS" if q_eval["check_passed"] else "FAIL"
        print(f"[{status}] {q_eval['title']}")
        print(f"  Expected: {q_eval['expected_answer']}")
        print(f"  Rationale: {q_eval['rationale']}")
