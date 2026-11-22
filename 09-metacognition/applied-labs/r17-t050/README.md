# Applied Lab: Metacognitive Routing and Self-Calibration (R17-T050)

**Lesson Alignment**: [Lesson 09: Metacognition in AI Agents](../../README.md)

---

## Overview

Metacognition—"thinking about thinking"—allows an AI agent to monitor, reflect upon, and regulate its own reasoning processes. In production systems, agents frequently produce outputs with subjective confidence estimates and varying levels of supporting evidence. Without metacognitive oversight, overconfident agents may act autonomously on unsubstantiated conclusions (hallucinations), while underconfident agents may unnecessarily route well-supported decisions to humans.

This applied lab implements:
1. **Confidence & Evidence Gating Rules**:
   - `confidence >= 0.8` AND `evidence >= 2` $\rightarrow$ **`ANSWER`** (autonomous resolution)
   - `confidence < 0.8` (e.g., `0.79`) OR `evidence < 2` $\rightarrow$ **`REVIEW`** (expert/human verification)
   - Out-of-bounds confidence (outside `[0.0, 1.0]`) strictly rejected with a `ValueError`.
2. **Metacognitive Self-Calibration**:
   - Bridges raw agent assertions directly to calibrated confidence scoring.
   - Detects cognitive alignment states:
     - **`OVERCONFIDENT`**: High confidence ($> 0.8$) paired with sparse evidence ($< 2$ sources). Gated to `REVIEW`.
     - **`UNDERCONFIDENT`**: Low confidence ($< 0.8$) despite robust evidence ($\ge 2$ sources). Gated to `REVIEW` for safety.
     - **`CALIBRATED_ADEQUATE`**: High confidence backed by $\ge 2$ empirical sources. Approved for `ANSWER`.
     - **`UNCERTAIN_INSUFFICIENT`**: Low confidence and sparse evidence. Routed to `REVIEW`.
3. **Runnable Concept Example**:
   - Demonstrates calibration diagnosis, evidence support scaling, and routing decisions across real-world query scenarios.

---

## Routing Contract

| Stated Confidence | Evidence Count | Decision | Rationale |
| :--- | :--- | :--- | :--- |
| $\ge 0.80$ (e.g., $0.80$, $0.95$, $1.00$) | $\ge 2$ | **`ANSWER`** | Stated confidence meets threshold and is corroborated by multiple independent evidence items. |
| $< 0.80$ (e.g., $0.79$, $0.50$, $0.00$) | $\ge 2$ | **`REVIEW`** | Insufficient model confidence requires verification, even with evidence. |
| $\ge 0.80$ | $< 2$ (e.g., $1$, $0$) | **`REVIEW`** | Overconfidence prevention; claims lacking multi-source evidence cannot be autonomously answered. |
| $< 0.80$ | $< 2$ | **`REVIEW`** | High uncertainty and sparse evidence warrant human inspection. |
| $< 0.0$ or $> 1.0$ (or NaN) | Any | **`ValueError`** | Confidence score is out of the valid probability range $[0.0, 1.0]$. |

---

## Lab Files

- `example.py`: Core routing function (`route_agent_result`), metacognitive self-calibrator (`MetacognitiveCalibrator`), data structures (`AgentOutput`, `CalibrationReport`), and interactive demonstration (`run_metacognitive_demonstration`).
- `test_example.py`: Comprehensive test suite verifying all boundary conditions (`0.80` vs `0.79`, `2` vs `1`), invalid confidence ranges, type validations, and self-calibration reporting.

---

## Running the Lab and Tests

### 1. Run the Concept Demonstration
```bash
python3 09-metacognition/applied-labs/r17-t050/example.py
```

### 2. Run the Unit Test Suite
```bash
python3 -m unittest discover -s 09-metacognition/applied-labs/r17-t050 -p "test_*.py" -v
```
