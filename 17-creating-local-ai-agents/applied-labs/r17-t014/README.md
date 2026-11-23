# Applied Lab: Model-Manifest Selection — Invariant and State Trace (R17-T014)

## Overview & Lesson Alignment

In **Lesson 17: Creating Local AI Agents Using Microsoft Foundry Local and Qwen**, developers evaluate Small Language Models (SLMs) to execute agent tasks within workstation constraints. Because local hardware environments have strictly bounded RAM and context windows, model selection must follow a deterministic, auditable pipeline:
1. **Host RAM Budget Screening**: Filters out models requiring more physical RAM than the host workstation budget.
2. **Context Window Requirement**: Ensures candidate models provide sufficient context token length for the agent prompt and tool schemas.
3. **Traceability & Invariants**: Records explicit intermediate states after each filter stage and guarantees formal pipeline invariants between stage outputs and final admissions.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic educational fixture written in standard Python 3. The models (Fixture A, Fixture B, Fixture C) are invented teaching representations designed to illustrate pipeline invariants and do not represent claims about named commercial models.

---

## Canonical Teaching Manifest

| Model | Required RAM | Max Context Tokens | Description |
| :--- | :--- | :--- | :--- |
| **Fixture A** | **4 GB** | **2048** | Lightweight SLM |
| **Fixture B** | **8 GB** | **4096** | Standard SLM |
| **Fixture C** | **2 GB** | **512** | Micro SLM |

### Canonical Scenario
- **Inputs**: Workstation RAM budget = `6 GB`, Requested context = `1024 tokens`.
- **Stage 1 (RAM)**:
  - Admitted: `fixture_a` (4 GB <= 6 GB), `fixture_c` (2 GB <= 6 GB).
  - Rejected: `fixture_b` (`EXCEEDS_RAM_BUDGET`: 8 GB > 6 GB).
- **Stage 2 (Context)**:
  - Admitted: `fixture_a` (2048 >= 1024).
  - Rejected: `fixture_c` (`INSUFFICIENT_CONTEXT`: 512 < 1024).
- **Final Admitted Model**: `["fixture_a"]`.

---

## State Invariants Tested
1. **Partition Invariant**: At each stage, `input_candidates == admitted_candidates ∪ rejected_candidates`, with zero intersection.
2. **Sequential Hand-off Invariant**: `stage2.inputs == stage1.admitted_candidates`.
3. **Pipeline Invariant**: `final_admitted == stage2.admitted_candidates`.

---

## Running the Lab

### Run Demonstration
```bash
python3 17-creating-local-ai-agents/applied-labs/r17-t014/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 17-creating-local-ai-agents/applied-labs/r17-t014 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (Python standard library only).
- No GPU, model weights download, or API keys required.
