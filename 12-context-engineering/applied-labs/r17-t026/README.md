# Applied Lab R17-T026: Prompt-Template Escaping — Refactor the Teaching Example

**Lesson Context:** [Lesson 12: Context Engineering for AI Agents](../../README.md)  
**Task ID:** `R17-T026`  
**Contribution Focus:** Refactoring a monolithic prompt-template renderer by extracting a single named responsibility (`TemplateVariableValidator`), maintaining the exact behavioral contract, and proving before/after equivalence on all fixtures.

---

## 1. Overview & Pedagogical Purpose

In context engineering, prompt templating is used to maintain clean structural boundaries between system instructions and untrusted user inputs. However, monolithic implementations that couple variable validation with string interpolation become hard to maintain, test, and extend.

This lab demonstrates:
1. **Baseline Monolithic Implementation (`BaselineTemplateRenderer`):** Couples declaration parsing, dictionary key validation, and regex substitution in a single class.
2. **Extraction of a Single Named Responsibility (`TemplateVariableValidator`):** Isolates parameter declaration extraction and set-based missing/unexpected variable checking into a dedicated, unit-testable validator.
3. **Refactored Renderer (`RefactoredTemplateRenderer`):** Focuses solely on safe string replacement by delegating validation to the extracted validator.
4. **Behavioral Equivalence Proof:** Verifies that the refactored system behaves identically to the baseline on both valid and invalid fixtures.

### Security Disclaimer
> [!IMPORTANT]
> **Pedagogical Security Notice:** Parameterized templating and structural escaping ensure user inputs with `{` and `}` do not break formatting or trigger secondary substitution. **However, templating alone does NOT prevent semantic prompt injection** (where user text manipulates model instructions). Additional semantic validation and system prompts are required.

---

## 2. Architecture: Before vs After Refactoring

```
BEFORE (Monolithic Baseline):
┌────────────────────────────────────────────────────────┐
│               BaselineTemplateRenderer                 │
│  - Extracts declared placeholders ({name}, {topic})    │
│  - Validates missing/unexpected variables              │
│  - Performs string substitution                        │
└────────────────────────────────────────────────────────┘

AFTER (Extracted Single Responsibility):
┌─────────────────────────────────┐      ┌───────────────────────────────────┐
│    TemplateVariableValidator    │◄─────┤     RefactoredTemplateRenderer    │
│  - Extracts declared variables  │      │  - Delegates validation           │
│  - Validates required inputs    │      │  - Performs single-pass safe sub  │
│  - Raises diagnostic errors     │      │  - Preserves literal user braces  │
└─────────────────────────────────┘      └───────────────────────────────────┘
```

---

## 3. Scope and Limitations (Simulation Disclaimer)

> [!NOTE]
> **Explicit Simulation Scope:** This lab is a local deterministic contract fixture implemented entirely with the Python standard library. It does not connect to live Azure OpenAI endpoints, download models, require GPUs, or call external cloud services.

---

## 4. Inputs, Parameters & Expected Outputs

| Scenario | Input Data | Baseline Output / Error | Refactored Output / Error | Equivalence |
| :--- | :--- | :--- | :--- | :--- |
| **Normal** | `name="Alice"`, `topic="Context"` | `User: Alice, Topic: Context` | `User: Alice, Topic: Context` | **Strict Match** |
| **Literal Braces** | `name="Bob"`, `topic="{inject}"` | `... Topic: {inject}` | `... Topic: {inject}` | **Strict Match** |
| **Missing Key** | `name="Charlie"` (no `topic`) | `MissingVariableError` | `MissingVariableError` | **Strict Match** |
| **Unexpected Key**| `name="A"`, `topic="B"`, `extra="C"` | `UnexpectedVariableError` | `UnexpectedVariableError` | **Strict Match** |

---

## 5. Verification & Test Execution

### Prerequisites
- Python 3.12+ (Standard Library only)

### Running the Concept Demonstration
```bash
python3 12-context-engineering/applied-labs/r17-t026/example.py
```

### Running the Automated Unit Test Suite
```bash
python3 -m unittest discover -s 12-context-engineering/applied-labs/r17-t026 -p "test_*.py" -v
```
