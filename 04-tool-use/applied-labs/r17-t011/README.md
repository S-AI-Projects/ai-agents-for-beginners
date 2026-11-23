# Applied Lab: Typed Tool Dispatch — Runnable Concept Example (R17-T011)

## Overview & Lesson Alignment

In **Lesson 04: Tool Use Design Pattern**, agents extend their reasoning capabilities by calling external tools or APIs. To execute tool calls safely and reliably:
1. **Explicit Allowlist**: The agent runtime only routes requests to pre-registered, vetted functions.
2. **Schema & Type Validation**: Function arguments must strictly conform to expected numeric types; non-numeric inputs like strings must be rejected early.
3. **Structured Error Envelopes**: Errors (such as unknown tools or invalid argument types) must return machine-readable diagnostics rather than unhandled runtime crashes.
4. **Execution Guardrails**: When a tool call in a sequence fails, subsequent tools must not be executed, preserving safe system boundaries.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a deterministic educational fixture implemented using standard Python. It demonstrates local JSON contract validation and dispatch. It is not a full Model Context Protocol (MCP) transport server or cloud API integration.

---

## Contract & Expected Behavior

| Tool Name | Parameters | Allowed Types | Expected Output |
| :--- | :--- | :--- | :--- |
| `add` | `a`, `b` | `int`, `float` | `a + b` |
| `multiply` | `a`, `b` | `int`, `float` | `a * b` |

### Scenarios
- `add(2, 3)` -> Returns structured success with `5`.
- `multiply(2, 3)` -> Returns structured success with `6`.
- `unknown_tool` -> Returns structured error envelope with `error_code="UNKNOWN_TOOL"`.
- `add("2", 3)` -> Returns structured error envelope with `error_code="TYPE_ERROR"`.
- Sequence `[add(2, 3), invalid_call, multiply(2, 3)]` -> Executes `add`, encounters error on `invalid_call`, stops immediately, and does not execute `multiply`.

---

## Running the Lab

### Run Demonstration
```bash
python3 04-tool-use/applied-labs/r17-t011/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 04-tool-use/applied-labs/r17-t011 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (Python standard library only).
- No external packages or API keys required.
