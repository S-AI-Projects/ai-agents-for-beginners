# Applied Lab R17-T021: Browser-Action Guard

**Lesson Context:** [Lesson 15: Building Computer Use Agents (CUA)](../../README.md)  
**Task ID:** `R17-T021`  
**Contribution Focus:** Deterministic browser-action guard for origin containment and step budget enforcement.

---

## 1. Overview & Pedagogical Purpose

In autonomous computer-use and browser automation, an AI agent operates in an interactive environment where unconstrained actions can introduce major safety and operational risks:
1. **Navigating to Malicious Origins:** A prompt injection, untrusted link, or model error might direct the browser to an unapproved external domain.
2. **Unbounded Execution Loops:** An ambiguous page state or failure recovery loop could lead to runaway actions that waste compute and flood web endpoints.

This applied lab provides a minimal, self-contained, and deterministic runnable example of a **`BrowserActionGuard`** intercepting and validating browser actions prior to dispatch.

---

## 2. Architecture & Components

```
                +---------------------------------------+
                |         Proposed Action               |
                |  (navigate, click, type, extract)     |
                +-------------------+-------------------+
                                    |
                                    v
                +---------------------------------------+
                |        BrowserActionGuard             |
                |                                       |
                | 1. Step Budget Check:                 |
                |    step_count < step_budget?          |
                |    -> If exceeded: HALT               |
                |                                       |
                | 2. Origin Policy Check:               |
                |    origin in allowed_origins?         |
                |    -> If disallowed: REJECT           |
                +-------------------+-------------------+
                                    | (Passed)
                                    v
                +---------------------------------------+
                |          MockBrowserSession           |
                |  (Deterministic local browser stub)   |
                +---------------------------------------+
```

### Components:
- **`BrowserAction`**: Typed dataclass defining the atomic action (`action_type`, `url`, `selector`, `value`).
- **`BrowserActionGuard`**: Middleware enforcing:
  - **Origin Containment**: Validates that target navigation URLs belong to the approved domain set (e.g., `example.invalid`). Disallowed origins are rejected *before* any browser navigation occurs.
  - **Step Budgeting**: Limits total agent actions to a configured threshold (e.g., `step_budget = 3`). Attempting a 4th step raises `StepBudgetExceededError`.
- **`MockBrowserSession`**: Deterministic in-memory browser stub tracking `current_url`, `history`, and `executed_actions`.

---

## 3. Scope and Limitations (Simulation Disclaimer)

> [!NOTE]
> **Explicit Simulation Scope:** This lab is a local deterministic concept fixture implemented entirely with the Python standard library. It does not initiate a real Chrome process, connect to Chrome DevTools Protocol (CDP), communicate with Playwright, or consume LLM/cloud tokens. It does not make any claim regarding real-world cloud performance or physical device automation.

---

## 4. Inputs, Parameters & Expected Outputs

### Configuration Inputs
- `allowed_origins`: `["example.invalid"]`
- `step_budget`: `3`

### Action Sequence & Expected Results

| Step | Action Type | Target / Payload | Guard Validation | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `NAVIGATE` | `https://example.invalid/search` | Origin is allowed; Budget: 1/3 | **Passed** (`Navigated to https://example.invalid/search`) |
| **2** | `CLICK` | `#search-button` | In-page action; Budget: 2/3 | **Passed** (`Clicked element matching '#search-button'`) |
| **3** | `NAVIGATE` | `https://example.invalid/results?page=2` | Origin is allowed; Budget: 3/3 | **Passed** (`Navigated to https://example.invalid/results?page=2`) |
| **4** | `EXTRACT` | `.listing-title` | Budget: 4/3 -> **Exceeded** | **Rejected** (`StepBudgetExceededError`) |
| **—** | `NAVIGATE` | `https://malicious.invalid/phishing` | Disallowed origin | **Rejected** (`DisallowedOriginError` before execution) |

---

## 5. Verification & Test Execution

### Prerequisites
- Python 3.12+ (Standard Library only)

### Running the Concept Demonstration
```bash
python3 15-browser-use/applied-labs/r17-t021/example.py
```

### Running the Automated Unit Test Suite
```bash
python3 -m unittest discover -s 15-browser-use/applied-labs/r17-t021 -p "test_*.py" -v
```
