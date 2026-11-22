# Applied Lab: Browser Action Validation with Origin and Step Guards (R17-T045)

## Overview & Lesson Alignment

In **Lesson 15: Building Computer Use Agents (CUA)**, autonomous browser agents interact with web applications by planning and executing action sequences (navigating URLs, clicking selectors, typing inputs, extracting data). Because browser agents operate in untrusted environments, establishing **deterministic pre-execution guardrails** is essential:
1. **Origin Isolation**: Agents must never navigate to unauthorized domains, phishing sites, or external redirects.
2. **Step Budgets**: Infinite loops or recursive clicking must be bounded by strict maximum action quotas.
3. **Pre-Execution Rejection**: Actions must be validated *before* hitting the browser session (fail-fast security).
4. **Modular Architecture**: Decoupling validation logic into dedicated, composable guard components improves testability and maintainability over monolithic scripts.

This applied lab implements **Browser Action Pre-Execution Guardrails** and refactors a monolithic validation example into dedicated `OriginGuard` and `StepBudgetGuard` components with proven before/after equivalence.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a zero-dependency educational module implemented exclusively with the Python 3 standard library (`dataclasses`, `urllib.parse`, `typing`, `unittest`). No live browser instances, CDP connections, cloud models, or Playwright drivers are required to validate the action sequence policies.

---

## Core Contract & Invariant Guarantees

The validator evaluates proposed `BrowserAction` sequences against configured security policies:

| Rule | Contract Specification | Expected Outcome | Error Type |
| :--- | :--- | :--- | :--- |
| **Allowed Origin Navigation** | Navigation targets approved origin (`example.invalid`) | **PASS** | None |
| **Disallowed Origin Navigation** | Navigation targets unapproved origin (`untrusted-site.com`) | **REJECTED** | `OriginValidationError` |
| **Step Budget Limit** | Action sequence has $\le 3$ steps under a 3-step budget | **PASS** | None |
| **Step Budget Exceeded** | 4th step proposed under a 3-step budget | **REJECTED** | `StepBudgetExceededError` |
| **Pre-Execution Check** | Validation runs prior to any browser interaction | **FAIL-FAST** | Execution halted immediately |

---

## Refactoring Architecture: Monolithic to Decomposed Guards

### 1. Monolithic Approach (Before)
`MonolithicBrowserActionValidator` handles URL parsing, domain normalization, step counting, and exception generation in a single monolithic class. While functional, it couples security boundaries with resource quota enforcement.

### 2. Decomposed Approach (After)
Validation is refactored into dedicated, single-responsibility components:
- **`OriginGuard`**: Encapsulates origin normalization and domain whitelisting for navigation actions.
- **`StepBudgetGuard`**: Encapsulates step-count quota policies.
- **`DecomposedBrowserActionValidator`**: Composes guards into a clean pre-execution validation pipeline.

```text
[ Proposed Browser Action Sequence ]
                │
                ▼
      ┌──────────────────┐
      │ StepBudgetGuard  │ ──(Exceeds Budget)──► Raise StepBudgetExceededError
      └──────────────────┘
                │ (Pass)
                ▼
      ┌──────────────────┐
      │   OriginGuard    │ ──(Unknown Origin)──► Raise OriginValidationError
      └──────────────────┘
                │ (Pass)
                ▼
  [ Approved for Execution ]
```

---

## Before / After Equivalence Matrix

| Fixture Scenario | Input Action Sequence | Monolithic Validator | Decomposed Validator | Equivalence Status |
| :--- | :--- | :--- | :--- | :--- |
| **Valid Canonical Sequence** | `navigate(example.invalid)` $\to$ `click(#search)` $\to$ `extract(.results)` (3 steps) | **PASS** | **PASS** | **Identical** |
| **Step Budget Exceeded** | 4 steps under a budget of 3 | `StepBudgetExceededError` | `StepBudgetExceededError` | **Identical** |
| **Disallowed Origin** | `navigate(https://untrusted-site.com)` | `OriginValidationError` | `OriginValidationError` | **Identical** |
| **Boundary: Zero Steps** | `[]` (Empty sequence) | **PASS** | **PASS** | **Identical** |
| **Boundary: Single Step** | `[navigate(https://example.invalid)]` | **PASS** | **PASS** | **Identical** |
| **Dictionary Format** | Raw dict inputs `[{"action_type": "navigate", "target": "..."}]` | **PASS** | **PASS** | **Identical** |

---

## Quick Invocation & Testing

```bash
# Run demonstration script and view before/after comparative outcomes
python3 15-browser-use/applied-labs/r17-t045/example.py

# Run automated unit test suite
python3 -m unittest discover -s 15-browser-use/applied-labs/r17-t045 -p "test_*.py" -v
```

