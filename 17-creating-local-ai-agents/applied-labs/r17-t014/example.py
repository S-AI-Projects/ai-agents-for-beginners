#!/usr/bin/env python3
"""Model-Manifest Selection — Invariant and State Trace (R17-T014).

Demonstrates local model selection against explicit hardware and context constraints:
- Evaluates synthetic model manifest entries using RAM budget and requested context window.
- Produces explicit rejection reasons for excluded models.
- Records intermediate evaluation states at each filter stage.
- Tests formal invariants linking progressive states to the final admitted set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ModelEntry:
    model_id: str
    required_ram_gb: int
    max_context_tokens: int
    description: str


@dataclass
class StageTrace:
    stage_name: str
    input_candidate_ids: List[str]
    admitted_candidate_ids: List[str]
    rejections: Dict[str, str]  # model_id -> reason


@dataclass
class ManifestSelectionResult:
    admitted_models: List[str]
    stage_traces: List[StageTrace]
    all_rejections: Dict[str, str]


# Synthetic educational manifest
TEACHING_MANIFEST: List[ModelEntry] = [
    ModelEntry(model_id="fixture_a", required_ram_gb=4, max_context_tokens=2048, description="Fixture A (Lightweight SLM)"),
    ModelEntry(model_id="fixture_b", required_ram_gb=8, max_context_tokens=4096, description="Fixture B (Standard SLM)"),
    ModelEntry(model_id="fixture_c", required_ram_gb=2, max_context_tokens=512, description="Fixture C (Micro SLM)"),
]


class ManifestSelectorWithTrace:
    """Selects eligible local models with explicit intermediate state recording."""

    def __init__(self, manifest: Optional[List[ModelEntry]] = None) -> None:
        self.manifest = manifest if manifest is not None else TEACHING_MANIFEST

    def select(self, ram_budget_gb: int, requested_context_tokens: int) -> ManifestSelectionResult:
        traces: List[StageTrace] = []
        all_rejections: Dict[str, str] = {}

        # Stage 1: RAM Filter
        stage1_inputs = [m.model_id for m in self.manifest]
        stage1_admitted: List[str] = []
        stage1_rejections: Dict[str, str] = {}

        for model in self.manifest:
            if model.required_ram_gb <= ram_budget_gb:
                stage1_admitted.append(model.model_id)
            else:
                reason = f"EXCEEDS_RAM_BUDGET: requires {model.required_ram_gb}GB, budget is {ram_budget_gb}GB"
                stage1_rejections[model.model_id] = reason
                all_rejections[model.model_id] = reason

        traces.append(StageTrace(
            stage_name="RAM_FILTER",
            input_candidate_ids=stage1_inputs,
            admitted_candidate_ids=stage1_admitted,
            rejections=stage1_rejections,
        ))

        # Stage 2: Context Window Filter
        model_map = {m.model_id: m for m in self.manifest}
        stage2_inputs = list(stage1_admitted)
        stage2_admitted: List[str] = []
        stage2_rejections: Dict[str, str] = {}

        for model_id in stage2_inputs:
            model = model_map[model_id]
            if model.max_context_tokens >= requested_context_tokens:
                stage2_admitted.append(model.model_id)
            else:
                reason = f"INSUFFICIENT_CONTEXT: provides {model.max_context_tokens} tokens, requested {requested_context_tokens}"
                stage2_rejections[model.model_id] = reason
                all_rejections[model.model_id] = reason

        traces.append(StageTrace(
            stage_name="CONTEXT_FILTER",
            input_candidate_ids=stage2_inputs,
            admitted_candidate_ids=stage2_admitted,
            rejections=stage2_rejections,
        ))

        return ManifestSelectionResult(
            admitted_models=stage2_admitted,
            stage_traces=traces,
            all_rejections=all_rejections,
        )


def main() -> None:
    selector = ManifestSelectorWithTrace()
    # Canonical scenario: RAM budget 6 GB, requested context 1024 tokens
    res = selector.select(ram_budget_gb=6, requested_context_tokens=1024)
    print("Canonical Selection (RAM=6GB, Context=1024):")
    print("Admitted Models:", res.admitted_models)
    for trace in res.stage_traces:
        print(f"Stage {trace.stage_name}: input={trace.input_candidate_ids} -> admitted={trace.admitted_candidate_ids}")
        if trace.rejections:
            print(f"  Rejections: {trace.rejections}")


if __name__ == "__main__":
    main()
