# Applied Lab R17-T025: Browser-Action Guard — Offline Service Adapter

**Lesson Context:** [Lesson 15: Building Computer Use Agents (CUA)](../../README.md)  
**Task ID:** `R17-T025`  
**Contribution Focus:** Decoupling browser automation behind an abstract callable interface (`BrowserServiceAdapter`) and supplying a deterministic in-memory adapter (`OfflineLocalBrowserAdapter`) with explicit identification of unsupported real-service behaviors.

---

## 1. Overview & Pedagogical Purpose

In production AI agent architectures, computer-use capabilities (navigating websites, clicking buttons, extracting content) depend on heavy external browser drivers (e.g., Playwright, Chromium over CDP). For automated testing, CI pipelines, and security validation:
1. **Interface Decoupling:** External browser dependencies should be abstracted behind a callable interface (`BrowserServiceAdapter`).
2. **Deterministic Offline Testing:** An in-memory local adapter (`OfflineLocalBrowserAdapter`) allows instantaneous validation of policy guardrails (origin restrictions and step budgets) with zero network overhead.
3. **Explicit Real-Service Gap Identification:** Tests must clearly document what real-world browser behavior the mock *does not* simulate.

---

## 2. Architecture & Adapter Contract

```
                      Agent / Policy Layer
                               │
                               ▼
                    GuardedBrowserService
            (Origin Check & Step Budget Limiter)
                               │
                               ▼
                     BrowserServiceAdapter
                  (Abstract Callable Interface)
                     ┌─────────┴─────────┐
                     ▼                   ▼
         OfflineLocalBrowserAdapter   RealPlaywrightAdapter
           (In-Memory Simulation)     (Live Chromium / CDP)
```

### Components
- **`BrowserServiceAdapter` (ABC):** Defines `navigate()`, `click()`, `extract()`, `current_url`, and `execution_history`.
- **`OfflineLocalBrowserAdapter`:** Deterministic local implementation tracking state in-memory without external processes.
- **`GuardedBrowserService`:** Intermediary validating:
  - **Origin Containment:** Only approved origins (e.g. `example.invalid`) pass; disallowed origins raise `DisallowedOriginError` prior to adapter dispatch.
  - **Step Budgeting:** Enforces a maximum step budget (e.g., 3 steps); a 4th step raises `StepBudgetExceededError`.

---

## 3. Real-Service Behaviors NOT Established by Mock

The offline adapter is a behavioral contract stub. It does **not** establish the following real-service capabilities:
1. **Real Network Transport:** Does not perform DNS resolution, TCP handshakes, TLS negotiation, or HTTP/2 multiplexing.
2. **DOM Engine & Script Execution:** Does not execute client-side JavaScript, trigger CSS layout reflows, or render single-page applications.
3. **Process Resilience:** Does not simulate browser tab crashes, out-of-memory errors, or Chrome DevTools Protocol IPC timeouts.
4. **Browser Security Sandbox:** Does not enforce Same-Origin Policy (SOP), Cross-Origin Resource Sharing (CORS), or iframe isolation.
5. **Storage & State Persistence:** Does not persist cookies, localStorage, session tokens, or HTTP cache headers.
6. **Visual & Input Fidelity:** Does not render visual viewport pixels, compute bounding boxes, or simulate physical mouse coordinate dispatch.

---

## 4. Scope and Limitations (Simulation Disclaimer)

> [!NOTE]
> **Explicit Simulation Scope:** This lab is a local deterministic contract fixture implemented entirely with the Python standard library. It does not launch Chrome, connect to CDP, use Playwright, or consume cloud LLM tokens. It provides an architectural adapter pattern for safety guardrail verification.

---

## 5. Inputs, Parameters & Expected Outputs

| Attempt | Action Type | Target | Guardrail Check | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `NAVIGATE` | `https://example.invalid/home` | Origin allowed; Budget 1/3 | **Pass** (`Offline adapter navigated`) |
| **2** | `CLICK` | `#login-btn` | Budget 2/3 | **Pass** (`Offline adapter clicked`) |
| **3** | `NAVIGATE` | `https://example.invalid/dashboard` | Origin allowed; Budget 3/3 | **Pass** (`Offline adapter navigated`) |
| **4** | `EXTRACT` | `#stats` | Budget 4/3 -> Exceeded | **Blocked** (`StepBudgetExceededError`) |
| **—** | `NAVIGATE` | `https://malicious.invalid/leak` | Disallowed origin | **Blocked** (`DisallowedOriginError` before execution) |

---

## 6. Verification & Test Execution

### Prerequisites
- Python 3.12+ (Standard Library only)

### Running the Concept Demonstration
```bash
python3 15-browser-use/applied-labs/r17-t025/example.py
```

### Running the Automated Unit Test Suite
```bash
python3 -m unittest discover -s 15-browser-use/applied-labs/r17-t025 -p "test_*.py" -v
```
