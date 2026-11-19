# Applied Lab R17-T024: Agent-Component Routing — Invariant and State Trace

**Lesson Context:** [Lesson 02: Explore AI Agent Frameworks](../../README.md)  
**Task ID:** `R17-T024`  
**Contribution Focus:** Deterministic agent-component routing with explicit intent priority, fallback handling, auditable decision logging, and formal state-trace invariants.

---

## 1. Overview & Pedagogical Purpose

In multi-agent frameworks, an orchestrator or supervisor agent routes incoming user requests to specialized sub-agents or component handlers (e.g. support, calculation, fallback). When queries are ambiguous or contain overlapping intent triggers, an agent architecture must:
1. **Apply Explicit Priority Ordering:** Resolve ambiguity via deterministic rules rather than probabilistic guessing.
2. **Log Auditable Decisions:** Record why a specific handler and rule were selected.
3. **Capture Intermediate State Traces:** Maintain step-by-step state snapshots throughout request lifecycle (`RECEIVED` -> `ANALYZED` -> `ROUTED` -> `DISPATCHED` -> `COMPLETED`).
4. **Enforce Formal Invariants:** Verify that final outputs mathematically match the intermediate state decisions.

---

## 2. Architecture & Priority Policy

```
                             Incoming Request
                                    │
                                    ▼
                          [Step 1: RECEIVED]
                                    │
                                    ▼
                          [Step 2: ANALYZED]
                        (Detect Intent Signals)
                                    │
                                    ▼
                          [Step 3: ROUTED]
                     (Evaluate Priority Rules)
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
                   help         calculate       unknown
                     │              │              │
                     ▼              ▼              ▼
                 support        calculator      fallback
               (Priority 1)   (Priority 2)   (Priority 99)
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                         [Step 4: DISPATCHED]
                                    │
                                    ▼
                          [Step 5: COMPLETED]
```

### Policy & Priority Table

| Rule ID | Intent | Target Handler | Priority | Description |
| :--- | :--- | :--- | :--- | :--- |
| `RULE_HELP_PRIORITY` | `help` | `support` | **1** (Highest) | Directs assistance/help queries to the support handler |
| `RULE_CALCULATE_PRIORITY` | `calculate` | `calculator` | **2** | Directs math and computational queries to calculator |
| `RULE_FALLBACK_DEFAULT` | `unknown` | `fallback` | **99** (Lowest) | Catches unclassified or unrecognized queries |

*Ambiguity Rule:* When both `help` and `calculate` triggers are present (e.g. *"Can you help me calculate our taxes?"*), the router evaluates `priority` in ascending order, selecting `RULE_HELP_PRIORITY` and routing to `support`.

---

## 3. Formal Invariants Linking State to Output

The router formally checks that intermediate execution traces maintain causal consistency with the returned output:
1. **Phase Sequence Invariant:** Traces must record exactly `[RECEIVED, ANALYZED, ROUTED, DISPATCHED, COMPLETED]` in order.
2. **Parity Invariant:** `target_handler` decided at `ROUTED` must strictly equal `dispatched_to` at `DISPATCHED`, `handler_name` at `COMPLETED`, and final `result.handler_name`.
3. **Priority Invariant:** If `help` is detected in ambiguous inputs, target handler must be `support`.

---

## 4. Scope and Limitations (Simulation Disclaimer)

> [!NOTE]
> **Explicit Simulation Scope:** This lab is a local deterministic contract fixture implemented entirely with the Python standard library. It does not initiate real Azure OpenAI network connections, deploy cloud agents to Microsoft Foundry, or require GPUs. It models the core architectural routing logic and state audit invariants taught in Lesson 02.

---

## 5. Inputs, Parameters & Expected Outputs

| Input Query | Detected Intents | Chosen Rule | Target Handler | Trace Steps |
| :--- | :--- | :--- | :--- | :--- |
| `"I need help with my account"` | `[help]` | `RULE_HELP_PRIORITY` | `support` | 5 |
| `"Please calculate 45 * 12"` | `[calculate]` | `RULE_CALCULATE_PRIORITY` | `calculator` | 5 |
| `"What is the weather outside?"` | `[unknown]` | `RULE_FALLBACK_DEFAULT` | `fallback` | 5 |
| `"Can you help me calculate taxes?"`| `[help, calculate]` | `RULE_HELP_PRIORITY` | `support` | 5 |

---

## 6. Verification & Test Execution

### Prerequisites
- Python 3.12+ (Standard Library only)

### Running the Concept Demonstration
```bash
python3 02-explore-agentic-frameworks/applied-labs/r17-t024/example.py
```

### Running the Automated Unit Test Suite
```bash
python3 -m unittest discover -s 02-explore-agentic-frameworks/applied-labs/r17-t024 -p "test_*.py" -v
```
