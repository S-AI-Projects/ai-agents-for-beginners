# Applied Lab: Model-Manifest Selection — Scenario Assessment (R17-T030)

## Overview & Lesson Alignment

In **Lesson 17: Creating Local AI Agents Using Microsoft Foundry Local and Qwen**, developers run agents directly on local workstations using Small Language Models (SLMs). Unlike cloud models with unlimited infrastructure behind an API, local agents operate under hard workstation resource constraints:
1. **Host RAM Budget**: The model weights and KV cache must fit into workstation RAM (e.g., 4 GB, 8 GB, 16 GB).
2. **Context Window Ceiling**: Local models have fixed maximum sequence lengths (e.g., 2048 or 4096 tokens).
3. **Tool-Calling Capability**: For agentic workflows, the model must support structured tool/function calling.

This applied lab implements a local **Manifest Selector** that screens candidate model entries from a synthetic local catalog against specified workstation hardware budgets and task context requirements.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic educational simulation implemented in the Python 3 standard library. The fixture values (Fixture A, Fixture B, Fixture C) are invented teaching fixtures designed to illustrate boundary selection rules and do not represent claims about named commercial or open-weight models. No external packages, cloud connections, or GPUs are required.

---

## Canonical Teaching Manifest & Contract

| Model Fixture | Required RAM | Max Context | Tool Support | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Fixture A** (`fixture_a`) | **4 GB** | **2048 tokens** | Yes | Lightweight local SLM |
| **Fixture B** (`fixture_b`) | **8 GB** | **4096 tokens** | Yes | Standard local SLM |
| **Fixture C** (`fixture_c`) | **2 GB** | **512 tokens** | No | Micro-SLM (chat only) |

### Canonical Scenario
- **Inputs**: Workstation RAM budget = `6 GB`, Requested context = `1024 tokens`.
- **Outcome**:
  - `fixture_a` is **ADMITTED** (RAM 4 GB <= 6 GB, Context 2048 >= 1024).
  - `fixture_b` is **EXCLUDED** (`EXCEEDS_RAM_BUDGET`: 8 GB > 6 GB).
  - `fixture_c` is **EXCLUDED** (`INSUFFICIENT_CONTEXT`: 512 < 1024, and `MISSING_TOOL_SUPPORT`).
  - **Admitted Model**: Only `fixture_a`.

---

## Applied Scenario Assessment (Three Questions)

### Question 1: Predict an Output
- **Scenario**: Given `ram_budget_gb=6` and `requested_context_tokens=1024`, predict which models are admitted.
- **Predicted Output**: `["fixture_a"]`
- **Rationale**: Fixture A requires 4 GB RAM (<= 6 GB budget) and provides 2048 tokens (>= 1024 tokens). Fixture B requires 8 GB RAM (> 6 GB budget) and is rejected.

### Question 2: Diagnose a Failure
- **Scenario**: A developer requests an 8192-token context window on a machine with 16 GB RAM. All candidates are rejected. Diagnose why.
- **Diagnosis**: `INSUFFICIENT_CONTEXT` on all models.
- **Rationale**: While 16 GB RAM satisfies the memory requirements of all models, neither Fixture A (2048) nor Fixture B (4096) supports an 8192-token context window.

### Question 3: Choose a Boundary Policy
- **Scenario**: Should an allocation where required RAM exactly equals the budget (e.g. 4 GB required on a 4 GB machine) be inclusive (`<=`) or strict (`<`)?
- **Policy Choice**: Inclusive boundary (`model.required_ram_gb <= ram_budget_gb`).
- **Rationale**: An inclusive boundary maximizes local resource utilization without causing artificial starvations or unnecessary cloud fallbacks for exact-fit workloads.

---

## Running the Lab

### Run Demonstration & Assessment Checks
```bash
python3 17-creating-local-ai-agents/applied-labs/r17-t030/example.py
```

### Run Automated Unit Test Suite
```bash
python3 -m unittest discover -s 17-creating-local-ai-agents/applied-labs/r17-t030 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (standard library only).
- Zero external package dependencies, zero cloud API keys required.
