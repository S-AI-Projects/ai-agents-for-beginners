# Applied Lab R17-T022: Deterministic Typed Tool Dispatch

**Lesson Context:** [Lesson 04: Tool Use Design Pattern](../../README.md)  
**Task ID:** `R17-T022`  
**Contribution Focus:** Deterministic typed tool dispatch, explicit tool allowlisting, strict numeric argument validation, and failure-containment state invariants.

---

## 1. Overview & Pedagogical Purpose

In agentic architectures, an AI agent interacts with external environments through tools. The language model generates structured tool calls (typically JSON envelopes specifying a tool name and argument dictionary). However, relying on unvalidated model output introduces severe operational and security risks:
1. **Tool Name Hallucination & Execution:** Models may request non-existent tools or attempt dangerous functions outside the intended scope.
2. **Schema & Type Mismatches:** Models frequently emit uncoerced string arguments (e.g., `"2"` instead of `2`) or booleans which violate strict backend contracts.
3. **Cascading Failure Corruption:** When a tool call in an automated sequence fails, continuing execution on a compromised or unhandled session can corrupt downstream business logic.

This applied lab provides a minimal, self-contained, and deterministic runnable example of a **`ToolDispatcher`** enforcing:
- **Explicit Allowlisting:** Restricting invocation strictly to `{"add", "multiply"}`.
- **Strict Numeric Validation:** Validating arguments as `int` or `float` while explicitly rejecting booleans (which subclass `int` in Python) and non-numeric strings.
- **Pre-Execution State Invariance:** Ensuring that if an invocation fails validation, execution history and session state remain completely unmutated.
- **Failure Containment Latch:** Enforcing that once an execution fails, the dispatcher locks to prevent subsequent tool execution in that session ("a failed call cannot execute another tool").

---

## 2. Architecture & Components

```
                +---------------------------------------+
                |        Incoming Tool Call             |
                |   (ToolCall or JSON message payload)  |
                +-------------------+-------------------+
                                    |
                                    v
                +---------------------------------------+
                |           ToolDispatcher              |
                |                                       |
                | 1. Failure Latch Check:               |
                |    is_blocked?                        |
                |    -> If blocked: RAISE               |
                |       ToolExecutionBlockedError       |
                |                                       |
                | 2. Allowlist Check:                   |
                |    name in allowed_tools?             |
                |    -> If unlisted: RAISE              |
                |       UnknownToolError & LATCH        |
                |                                       |
                | 3. Strict Argument & Type Check:      |
                |    a, b present?                      |
                |    not isinstance(val, bool)?         |
                |    isinstance(val, (int, float))?     |
                |    no extraneous parameters?          |
                |    -> If invalid: RAISE               |
                |       ToolArgumentError & LATCH       |
                +-------------------+-------------------+
                                    | (Validation Passed)
                                    v
                +---------------------------------------+
                |       Tool Primitives (Pure)          |
                |    add_tool(a, b) -> a + b            |
                |    multiply_tool(a, b) -> a * b       |
                +-------------------+-------------------+
                                    |
                                    v
                +---------------------------------------+
                |        ToolResult & History           |
                |  (Records success result in session)  |
                +---------------------------------------+
```

### Components:
- **`ToolCall`**: Frozen dataclass modeling tool requests (`name`, `arguments`, `call_id`).
- **`ToolResult`**: Frozen dataclass capturing execution outcomes (`call_id`, `tool_name`, `success`, `result`, `error`).
- **`ToolDispatcher`**: Middleware and dispatcher managing execution lifecycle, allowlisting, and failure state.
- **Exceptions Hierarchy**:
  - `ToolDispatchError`: Base domain exception.
  - `UnknownToolError`: Raised when tool is not allowlisted.
  - `ToolArgumentError`: Raised when arguments are missing, extraneous, non-numeric, or boolean.
  - `ToolExecutionBlockedError`: Raised when calls are attempted on a blocked session.

---

## 3. Scope and Limitations (Simulation Disclaimer)

> [!NOTE]
> **Explicit Simulation Scope:** Deterministic local simulation fixture implemented in standard Python. Does not require cloud API keys, external models, or real hardware. It does not implement a full remote Model Context Protocol (MCP) wire transport or connect to live model endpoints.

---

## 4. Inputs, Parameters & Expected Outputs

### Supported Tools and Parameters

| Tool Name | Parameters | Types | Output Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| `add` | `a`, `b` | `int \| float` (excluding `bool`) | `int \| float` | Computes arithmetic sum `a + b` |
| `multiply` | `a`, `b` | `int \| float` (excluding `bool`) | `int \| float` | Computes arithmetic product `a * b` |

### Dispatch Behaviors & Boundary Decisions

| Scenario | Input | Validation Decision | Expected Result | State Invariant |
| :--- | :--- | :--- | :--- | :--- |
| **Normal Addition** | `add(2, 3)` | Passes allowlist and type checks | `ToolResult(result=5, success=True)` | Recorded in `execution_history` |
| **Normal Multiplication** | `multiply(2, 3)` | Passes allowlist and type checks | `ToolResult(result=6, success=True)` | Recorded in `execution_history` |
| **Float Precision** | `add(1.5, 2.5)` | Valid floating-point operands | `ToolResult(result=4.0, success=True)` | Recorded in `execution_history` |
| **Unknown Tool** | `divide(10, 2)` | Rejected: not in `{"add", "multiply"}` | `UnknownToolError` raised | History unmutated; session blocked |
| **String Argument** | `add("2", 3)` | Rejected: no automatic type coercion | `ToolArgumentError` raised | History unmutated; session blocked |
| **Boolean Argument** | `add(True, 3)` | Rejected: `bool` subclasses `int` in Python | `ToolArgumentError` raised | History unmutated; session blocked |
| **Missing Parameter** | `multiply(a=5)` | Rejected: missing parameter `'b'` | `ToolArgumentError` raised | History unmutated; session blocked |
| **Extra Parameter** | `add(a=2, b=3, c=4)`| Rejected: unexpected parameter `'c'` | `ToolArgumentError` raised | History unmutated; session blocked |
| **Call After Failure**| `add(2, 3)` on blocked session | Rejected: prior failure tripped latch | `ToolExecutionBlockedError` raised | History unmutated; remains blocked |

---

## 5. Verification & Test Execution

### Prerequisites
- Python 3.12+ (Standard Library only)

### Running the Concept Demonstration
```bash
python3 04-tool-use/applied-labs/r17-t022/example.py
```

### Running the Automated Unit Test Suite
```bash
python3 -m unittest discover -s 04-tool-use/applied-labs/r17-t022 -p "test_*.py" -v
```
