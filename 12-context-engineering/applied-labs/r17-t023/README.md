# Applied Lab R17-T023: Prompt-Template Escaping — Compare Two Approaches

**Lesson Context:** [Lesson 12: Context Engineering for AI Agents](../../README.md)  
**Task ID:** `R17-T023`  
**Contribution Focus:** Comparing direct single-pass substitution against an independent baseline table lookup to enforce instruction/data separation, variable validation, and literal brace preservation.

---

## 1. Overview & Pedagogical Purpose

In context engineering, managing the boundary between **system/developer instructions** and **untrusted user data** is essential to prevent prompt confusion, context poisoning, and accidental template corruption.

This lab explores and compares two distinct architectural approaches for template rendering:
1. **Approach 1 (`DirectTemplateRenderer`):** Single-pass regex substitution with strict set-theory validation of declared placeholders.
2. **Approach 2 (`TableReferenceRenderer`):** An independent baseline renderer utilizing segment boundary tokenization and an explicit substitution table.

### Security Disclaimer
> [!IMPORTANT]
> **Pedagogical Security Notice:** Parameterized templating and structural escaping separate instruction fields from user data fields, ensuring that characters like `{` and `}` in user inputs do not break template rendering or evaluate as nested variables. **However, templating alone does NOT prevent semantic prompt injection** (where untrusted text inside a variable persuades the downstream language model to deviate from its instructions). Additional defenses such as input filtering, model-level guardrails, and privilege boundaries are required.

---

## 2. Architecture & Comparison

```
              Declared Template: "Hello {name}, your topic is {topic}."
                                       │
              User Inputs: {"name": "Alice", "topic": "{code}"}
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          Approach 1 (Direct)                 Approach 2 (Reference)
     Single-pass Regex Substitution      Token Boundary Segment Lookup
                     │                                   │
                     └─────────────────┬─────────────────┘
                                       ▼
                       Outputs Match & Literal Braces Preserved:
               "Hello Alice, your topic is {code}."
```

### Comparative Analysis of Approaches

| Metric / Behavior | Approach 1: `DirectTemplateRenderer` | Approach 2: `TableReferenceRenderer` |
| :--- | :--- | :--- |
| **Parsing Technique** | Single-pass regex scan (`re.finditer` / `re.sub`) | Explicit slice index tracking & segment slicing |
| **Complexity** | $O(N)$ with compact implementation | $O(N)$ with explicit segment concatenation |
| **Missing Key Check** | Set difference (`declared - provided`) raises `MissingVariableError` | Set difference (`required - provided`) raises `MissingVariableError` |
| **Unexpected Key Check** | Set difference (`provided - declared`) raises `UnexpectedVariableError` | Set difference (`provided - required`) raises `UnexpectedVariableError` |
| **User Brace Safety** | 100% literal (replacement values never re-scanned) | 100% literal (values appended directly to segments) |

---

## 3. Scope and Limitations (Simulation Disclaimer)

> [!NOTE]
> **Explicit Simulation Scope:** This lab is a local deterministic contract fixture implemented entirely with the Python standard library. It does not connect to live Azure OpenAI endpoints, download models, require GPUs, or call external cloud services. It is designed to verify the deterministic mechanics of prompt templating and validation.

---

## 4. Inputs, Parameters & Expected Outputs

### Configuration Inputs
- Template: `"Assistant: Hello {name}. Topic: {topic}."`
- Declared Placeholders: `name`, `topic`

### Test Scenarios & Results

| Scenario | Input Data | Expected Behavior | Outcome |
| :--- | :--- | :--- | :--- |
| **Normal** | `name="Alice"`, `topic="AI"` | Both render identical output | **Pass** (`Assistant: Hello Alice. Topic: AI.`) |
| **Literal Braces** | `name="Bob"`, `topic="{inject}"` | Braces stay literal `{inject}` | **Pass** (`... Topic: {inject}.`) |
| **Missing Key** | `name="Charlie"` (no `topic`) | Fails with `MissingVariableError` | **Pass** (`Missing required template variable: 'topic'`) |
| **Unexpected Key**| `name="A"`, `topic="B"`, `extra="C"` | Fails with `UnexpectedVariableError` | **Pass** (`Unexpected template variables: ['extra']`) |

---

## 5. Verification & Test Execution

### Prerequisites
- Python 3.12+ (Standard Library only)

### Running the Concept Demonstration
```bash
python3 12-context-engineering/applied-labs/r17-t023/example.py
```

### Running the Automated Unit Test Suite
```bash
python3 -m unittest discover -s 12-context-engineering/applied-labs/r17-t023 -p "test_*.py" -v
```
