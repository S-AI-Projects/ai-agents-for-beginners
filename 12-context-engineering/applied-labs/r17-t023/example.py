"""Prompt-Template Escaping — Compare Two Approaches.

Lesson 12: Context Engineering for AI Agents
Task: R17-T023

This module implements and compares two approaches for prompt-template rendering:
1. DirectTemplateRenderer: Single-pass regex-based parameter substitution with strict
   variable declarations and boundary isolation.
2. TableReferenceRenderer: An independent baseline approach using token segment lookup
   and explicit replacement tables.

Core Guarantees:
- Declared placeholders ({name}, {topic}) are strictly validated.
- Missing required keys (e.g. topic) fail with MissingVariableError.
- Unknown/extra keys fail with UnexpectedVariableError.
- Braces inside user data (e.g. {malicious_tag}) remain 100% literal characters.
- Explicit pedagogical note: Templating alone does NOT prevent semantic prompt injection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set, Tuple


SECURITY_NOTE = (
    "Pedagogical Notice: Parameterized templating and structural escaping separate "
    "instruction fields from user data fields. However, templating alone does NOT "
    "prevent semantic prompt injection (e.g. untrusted instructions embedded within "
    "a variable's content that deceive the downstream language model)."
)


class TemplateError(Exception):
    """Base exception for all template validation and rendering failures."""


class MissingVariableError(TemplateError):
    """Raised when a declared template variable is missing from provided arguments."""

    def __init__(self, missing_variable: str, required_variables: Set[str]) -> None:
        self.missing_variable = missing_variable
        self.required_variables = required_variables
        super().__init__(
            f"Missing required template variable: '{missing_variable}'. "
            f"Required variables: {sorted(required_variables)}"
        )


class UnexpectedVariableError(TemplateError):
    """Raised when unexpected or undeclared variables are supplied."""

    def __init__(self, unexpected_variables: Set[str], allowed_variables: Set[str]) -> None:
        self.unexpected_variables = unexpected_variables
        self.allowed_variables = allowed_variables
        super().__init__(
            f"Unexpected template variables supplied: {sorted(unexpected_variables)}. "
            f"Allowed variables: {sorted(allowed_variables)}"
        )


class DirectTemplateRenderer:
    """Approach 1: Single-pass regex substitution with strict boundary validation."""

    VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def __init__(self, template: str) -> None:
        if not isinstance(template, str):
            raise TypeError("Template must be a string")
        self.template = template
        self.declared_variables: Set[str] = set(self.VARIABLE_PATTERN.findall(template))

    def render(self, **variables: Any) -> str:
        """Render template with strict variable validation and literal brace preservation."""
        provided_keys = set(variables.keys())

        # Check for missing variables
        missing = self.declared_variables - provided_keys
        if missing:
            # Deterministically raise for the first sorted missing variable
            first_missing = sorted(missing)[0]
            raise MissingVariableError(first_missing, self.declared_variables)

        # Check for unexpected variables
        extra = provided_keys - self.declared_variables
        if extra:
            raise UnexpectedVariableError(extra, self.declared_variables)

        # Single-pass substitution: ensures values containing braces are not re-evaluated
        def replace_match(match: re.Match) -> str:
            var_name = match.group(1)
            return str(variables[var_name])

        return self.VARIABLE_PATTERN.sub(replace_match, self.template)


class TableReferenceRenderer:
    """Approach 2: Independent baseline using segment tokenization and replacement lookup."""

    def __init__(self, template: str) -> None:
        if not isinstance(template, str):
            raise TypeError("Template must be a string")
        self.template = template
        # Tokenize by finding all placeholder occurrences with exact slice bounds
        self.placeholders: List[Tuple[str, int, int]] = []
        for match in re.finditer(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template):
            self.placeholders.append((match.group(1), match.start(), match.end()))
        self.required_variables: Set[str] = {p[0] for p in self.placeholders}

    def render(self, **variables: Any) -> str:
        """Render using sequential segment concatenation from an explicit replacement table."""
        provided_keys = set(variables.keys())

        # Check for missing variables
        missing = self.required_variables - provided_keys
        if missing:
            first_missing = sorted(missing)[0]
            raise MissingVariableError(first_missing, self.required_variables)

        # Check for unexpected variables
        extra = provided_keys - self.required_variables
        if extra:
            raise UnexpectedVariableError(extra, self.required_variables)

        # Build output segment by segment to guarantee user values remain literal
        segments: List[str] = []
        last_idx = 0
        for var_name, start_pos, end_pos in self.placeholders:
            # Append static text prior to placeholder
            segments.append(self.template[last_idx:start_pos])
            # Append exact string value from replacement table
            segments.append(str(variables[var_name]))
            last_idx = end_pos
        segments.append(self.template[last_idx:])

        return "".join(segments)


@dataclass(frozen=True)
class ComparisonResult:
    """Holds comparative execution results from both rendering approaches."""
    template: str
    inputs: Dict[str, Any]
    direct_output: Optional[str]
    reference_output: Optional[str]
    outputs_match: bool
    direct_error: Optional[str] = None
    reference_error: Optional[str] = None


def compare_approaches(template: str, inputs: Dict[str, Any]) -> ComparisonResult:
    """Compare Approach 1 (Direct) and Approach 2 (Table Reference) on identical inputs."""
    direct_renderer = DirectTemplateRenderer(template)
    reference_renderer = TableReferenceRenderer(template)

    direct_out: Optional[str] = None
    direct_err: Optional[str] = None
    ref_out: Optional[str] = None
    ref_err: Optional[str] = None

    try:
        direct_out = direct_renderer.render(**inputs)
    except Exception as exc:
        direct_err = type(exc).__name__

    try:
        ref_out = reference_renderer.render(**inputs)
    except Exception as exc:
        ref_err = type(exc).__name__

    outputs_match = (direct_out == ref_out) and (direct_err == ref_err)

    return ComparisonResult(
        template=template,
        inputs=inputs,
        direct_output=direct_out,
        reference_output=ref_out,
        outputs_match=outputs_match,
        direct_error=direct_err,
        reference_error=ref_err,
    )


def run_concept_demo() -> None:
    """Demonstrate the two approaches on standard, boundary, and injection test cases."""
    print("=" * 70)
    print("Prompt-Template Escaping — Approach Comparison Demo (Lesson 12)")
    print("=" * 70)
    print(f"\n{SECURITY_NOTE}\n")

    template = "Assistant Instructions:\nUser: {name}\nTopic to address: {topic}\nPlease respond appropriately."
    print(f"Declared Template:\n---\n{template}\n---")

    # Scenario 1: Normal rendering with valid variables
    print("\n[Scenario 1] Normal Rendering:")
    inputs1 = {"name": "Alice", "topic": "Context Windows"}
    res1 = compare_approaches(template, inputs1)
    print(f"Inputs: {inputs1}")
    print(f"Approach 1 (Direct) Output:\n{res1.direct_output}")
    print(f"Approach 2 (Reference) Output:\n{res1.reference_output}")
    print(f"Outputs Match: {res1.outputs_match}")

    # Scenario 2: User data with literal braces (e.g. potential template injection probe)
    print("\n[Scenario 2] Braces Inside User Data (Preserved Literal):")
    inputs2 = {
        "name": "Bob {admin}",
        "topic": "Python dicts: {'key': 'value'} and {SYSTEM: override instructions}",
    }
    res2 = compare_approaches(template, inputs2)
    print(f"Inputs with braces: {inputs2}")
    print(f"Approach 1 Output:\n{res2.direct_output}")
    print(f"Outputs Match: {res2.outputs_match}")
    print(f"Are braces in 'topic' literal? {'{SYSTEM: override instructions}' in res2.direct_output}")

    # Scenario 3: Missing required key ('topic')
    print("\n[Scenario 3] Missing Key Rejection:")
    inputs3 = {"name": "Charlie"}
    res3 = compare_approaches(template, inputs3)
    print(f"Inputs: {inputs3}")
    print(f"Approach 1 Error: {res3.direct_error}")
    print(f"Approach 2 Error: {res3.reference_error}")
    print(f"Both failed consistently: {res3.outputs_match}")

    # Scenario 4: Unexpected extra key
    print("\n[Scenario 4] Unexpected Key Rejection:")
    inputs4 = {"name": "Dana", "topic": "Robotics", "unauthorized_role": "admin"}
    res4 = compare_approaches(template, inputs4)
    print(f"Inputs: {inputs4}")
    print(f"Approach 1 Error: {res4.direct_error}")
    print(f"Approach 2 Error: {res4.reference_error}")
    print(f"Both failed consistently: {res4.outputs_match}")

    print("\nConcept demonstration completed successfully.")


if __name__ == "__main__":
    run_concept_demo()
