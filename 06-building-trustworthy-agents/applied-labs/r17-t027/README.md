# Applied Lab R17-T027: Allowlisted Action Policy — Worked Example with Checks

**Lesson Context:** [Lesson 06: Building Trustworthy AI Agents](../../README.md)  
**Task ID:** `R17-T027`  
**Contribution Focus:** Deterministic action policy validation evaluating tool allowlists and argument schemas prior to execution, ensuring rejected actions never reach the backend executor.

---

## 1. Overview & Pedagogical Purpose

When autonomous agents are equipped with tools, unrestricted access to sensitive functions (such as file deletion, arbitrary command execution, or destructive database updates) poses severe operational and security risks.

To build trustworthy agents, systems must enforce **pre-execution policy guardrails**:
1. **Explicit Tool Allowlisting:** An agent may only execute tools present in an explicitly authorized allowlist (e.g. `read`). Unallowlisted tools (e.g. `delete`) are blocked immediately.
2. **Strict Argument Schema Validation:** Arguments must satisfy parameter requirements (e.g. non-empty `path` string) before execution.
3. **Pre-Execution Refusal:** Any validation failure halts processing *before* dispatching to the executor stub, ensuring rejected actions never alter state.

---

## 2. Worked Input-to-Output Explanation Table

| Case ID | Proposed Tool & Arguments | Policy Evaluation | Dispatch Action | Outcome & Stub Executor State |
| :--- | :--- | :--- | :--- | :--- |
| **`CASE_1_ALLOWED_READ`** | `read(path="/data/report.txt")` | Tool `read` is allowed; `path` is present and non-empty. | Dispatched to `StubExecutor` | **Pass:** `Successfully read from path: /data/report.txt`. Executor call count increments by 1. |
| **`CASE_2_DISALLOWED_DELETE`** | `delete(path="/data/report.txt")` | Tool `delete` is NOT in allowlist `{'read'}`. | Blocked prior to execution | **Rejected:** Raises `DisallowedToolError`. Stub executor is **never called** (call count remains 0). |
| **`CASE_3_MISSING_ARGUMENT`** | `read()` (missing `path`) | Tool `read` is allowed, but required parameter `path` is omitted. | Blocked prior to execution | **Rejected:** Raises `ArgumentValidationError`. Stub executor is **never called** (call count remains 0). |

---

## 3. Architecture & Enforcement Sequence

```
                    Agent Proposes Tool Call
                               │
                               ▼
                   GuardedActionDispatcher
                               │
                               ▼
                      AllowedActionPolicy
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   1. Is tool in allowlist?           2. Does argument schema match?
      (e.g., is tool == 'read'?)         (is 'path' present & valid?)
              │                                 │
              ├─────── No ──────────┬───────────┤
              │                     │           │
              ▼                     │           ▼
    DisallowedToolError             │   ArgumentValidationError
   (Executor NOT reached)           │   (Executor NOT reached)
                                    ▼ Yes
                               StubExecutor
                        (Executes authorized action)
```

---

## 4. Scope and Limitations (Simulation Disclaimer)

> [!NOTE]
> **Explicit Simulation Scope:** This lab is a local deterministic contract fixture implemented entirely with the Python standard library. It does not invoke live LLMs, execute real operating system file operations, or call external cloud services. It verifies the architectural guardrail enforcing pre-execution policy checks.

---

## 5. Verification & Test Execution

### Prerequisites
- Python 3.12+ (Standard Library only)

### Running the Concept Demonstration
```bash
python3 06-building-trustworthy-agents/applied-labs/r17-t027/example.py
```

### Running the Automated Unit Test Suite
```bash
python3 -m unittest discover -s 06-building-trustworthy-agents/applied-labs/r17-t027 -p "test_*.py" -v
```
