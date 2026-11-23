# Applied Lab: Browser-Action Guard — Compare Two Approaches (R17-T013)

## Overview & Lesson Alignment

In **Lesson 15: Building Computer Use Agents (CUA)**, browser agents interact with web applications by synthesizing navigation, click, and form interaction events. Because web pages represent untrusted external environments, an unconstrained browser agent presents serious security and cost risks:
1. **Malicious Navigations**: Unvetted URLs can expose the agent session to phishing, malicious scripts, or data exfiltration.
2. **Infinite Navigation Loops**: Misdirected action planners can traverse unending web links, incurring substantial token and compute consumption.

This lab implements and validates a local browser-action guard that:
- Restricts navigations to an allowlisted origin (`example.invalid`).
- Halts execution when an origin is disallowed prior to executing the action.
- Limits total browser interactions to a maximum step budget of 3 steps (rejecting the 4th step).
- Formally compares two independent evaluation approaches (direct stateful guard vs. declarative reference evaluator) across identical inputs.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic, local contract fixture implemented in the Python 3 standard library. It simulates URL inspection and step limits without launching a live Chromium or Playwright instance.

---

## Contract & Expected Behavior

| Action Sequence | Budget | Expected Status | Reason / Invariant |
| :--- | :--- | :--- | :--- |
| `navigate("https://example.invalid")` -> `click("#btn")` | 3 | `PASSED` | Origin in allowlist; steps within budget (2 <= 3) |
| `navigate("https://unauthorized.org")` | 3 | `ORIGIN_DISALLOWED` | Unknown origin rejected before executing |
| 4 actions on `example.invalid` | 3 | `BUDGET_EXCEEDED` | 4th step rejected at step 3 boundary |

---

## Comparing Two Approaches

To ensure verification integrity without circular dependencies, the lab compares:
1. **Direct Implementation (`BrowserActionGuard`)**: Stateful evaluator that extracts URL netloc/host and tracks progressive action traces.
2. **Independent Reference Calculation (`reference_evaluate_plan`)**: Declarative ruleset implementing identical constraints independently.

All test suites verify 100% equivalence between the two implementations.

---

## Running the Lab

### Run Demonstration
```bash
python3 15-browser-use/applied-labs/r17-t013/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 15-browser-use/applied-labs/r17-t013 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (Python standard library only).
- No browser binary, GPU, or external package required.
