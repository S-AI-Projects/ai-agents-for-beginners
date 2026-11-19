"""Unit tests for Prompt-Template Escaping — Approach Comparison.

Lesson 12: Context Engineering for AI Agents
Task: R17-T023
Automated check: python3 -m unittest discover -s 12-context-engineering/applied-labs/r17-t023 -p "test_*.py" -v
"""

import unittest

from example import (
    ComparisonResult,
    DirectTemplateRenderer,
    MissingVariableError,
    TableReferenceRenderer,
    UnexpectedVariableError,
    compare_approaches,
)


class TestHappyPath(unittest.TestCase):
    """Test standard valid template rendering across both approaches."""

    def setUp(self) -> None:
        self.template = "Hello {name}, your discussion topic is {topic}."

    def test_name_and_topic_rendered_correctly(self) -> None:
        """Both approaches render declared variables identically."""
        inputs = {"name": "Alice", "topic": "Context Engineering"}
        expected = "Hello Alice, your discussion topic is Context Engineering."

        direct_out = DirectTemplateRenderer(self.template).render(**inputs)
        ref_out = TableReferenceRenderer(self.template).render(**inputs)

        self.assertEqual(direct_out, expected)
        self.assertEqual(ref_out, expected)
        self.assertEqual(direct_out, ref_out)

    def test_compare_approaches_utility(self) -> None:
        """Comparison helper confirms identity of outputs."""
        inputs = {"name": "Bob", "topic": "Tool Loadouts"}
        result = compare_approaches(self.template, inputs)

        self.assertTrue(result.outputs_match)
        self.assertIsNone(result.direct_error)
        self.assertIsNone(result.reference_error)
        self.assertEqual(result.direct_output, result.reference_output)

    def test_repeated_variables_rendered(self) -> None:
        """Templates referencing the same variable multiple times render properly."""
        tmpl = "User: {name}. Confirming name: {name}."
        inputs = {"name": "Charlie"}
        expected = "User: Charlie. Confirming name: Charlie."

        direct_out = DirectTemplateRenderer(tmpl).render(**inputs)
        ref_out = TableReferenceRenderer(tmpl).render(**inputs)

        self.assertEqual(direct_out, expected)
        self.assertEqual(ref_out, expected)


class TestRejectionGuardPath(unittest.TestCase):
    """Test strict validation and rejection of missing or unexpected keys."""

    def setUp(self) -> None:
        self.template = "Subject: {name} | Topic: {topic}"

    def test_missing_topic_fails(self) -> None:
        """Missing 'topic' must raise MissingVariableError on both approaches."""
        inputs = {"name": "Alice"}

        with self.assertRaises(MissingVariableError) as ctx1:
            DirectTemplateRenderer(self.template).render(**inputs)
        self.assertEqual(ctx1.exception.missing_variable, "topic")

        with self.assertRaises(MissingVariableError) as ctx2:
            TableReferenceRenderer(self.template).render(**inputs)
        self.assertEqual(ctx2.exception.missing_variable, "topic")

    def test_missing_name_fails(self) -> None:
        """Missing 'name' must raise MissingVariableError."""
        inputs = {"topic": "AI Safety"}

        with self.assertRaises(MissingVariableError) as ctx:
            DirectTemplateRenderer(self.template).render(**inputs)
        self.assertEqual(ctx.exception.missing_variable, "name")

    def test_unexpected_keys_rejected(self) -> None:
        """Providing extra/undeclared keys raises UnexpectedVariableError."""
        inputs = {"name": "Alice", "topic": "Safety", "extra_admin_flag": "true"}

        with self.assertRaises(UnexpectedVariableError) as ctx1:
            DirectTemplateRenderer(self.template).render(**inputs)
        self.assertIn("extra_admin_flag", ctx1.exception.unexpected_variables)

        with self.assertRaises(UnexpectedVariableError) as ctx2:
            TableReferenceRenderer(self.template).render(**inputs)
        self.assertIn("extra_admin_flag", ctx2.exception.unexpected_variables)


class TestLiteralBracePreservation(unittest.TestCase):
    """Test that braces in user input remain literal and do not trigger secondary formatting."""

    def setUp(self) -> None:
        self.template = "Prompt: Evaluate {name} on {topic}."

    def test_braces_in_user_data_remain_literal(self) -> None:
        """Braces inside variable content must remain literal characters."""
        inputs = {
            "name": "User_{id_123}",
            "topic": "Code with {SYSTEM: override} and JSON {'key': 'val'}",
        }
        expected = "Prompt: Evaluate User_{id_123} on Code with {SYSTEM: override} and JSON {'key': 'val'}."

        direct_out = DirectTemplateRenderer(self.template).render(**inputs)
        ref_out = TableReferenceRenderer(self.template).render(**inputs)

        self.assertEqual(direct_out, expected)
        self.assertEqual(ref_out, expected)
        self.assertIn("{SYSTEM: override}", direct_out)

    def test_double_curly_braces_in_user_input(self) -> None:
        """F-string or jinja style double braces in user input remain literal."""
        inputs = {
            "name": "{{admin_role}}",
            "topic": "Template syntax: {{variable}}",
        }
        expected = "Prompt: Evaluate {{admin_role}} on Template syntax: {{variable}}."

        direct_out = DirectTemplateRenderer(self.template).render(**inputs)
        ref_out = TableReferenceRenderer(self.template).render(**inputs)

        self.assertEqual(direct_out, expected)
        self.assertEqual(ref_out, expected)


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary conditions, types, and edge cases."""

    def test_empty_string_values_handled(self) -> None:
        """Empty string values for valid variables are valid inputs."""
        tmpl = "Name: [{name}], Topic: [{topic}]"
        inputs = {"name": "", "topic": ""}
        expected = "Name: [], Topic: []"

        direct_out = DirectTemplateRenderer(tmpl).render(**inputs)
        ref_out = TableReferenceRenderer(tmpl).render(**inputs)

        self.assertEqual(direct_out, expected)
        self.assertEqual(ref_out, expected)

    def test_numeric_and_boolean_values_coerced_cleanly(self) -> None:
        """Non-string primitives render via str() conversion without error."""
        tmpl = "ID: {name}, TopicCount: {topic}"
        inputs = {"name": 42, "topic": 100}
        expected = "ID: 42, TopicCount: 100"

        direct_out = DirectTemplateRenderer(tmpl).render(**inputs)
        ref_out = TableReferenceRenderer(tmpl).render(**inputs)

        self.assertEqual(direct_out, expected)
        self.assertEqual(ref_out, expected)

    def test_template_without_placeholders(self) -> None:
        """Templates with no declared variables render static content."""
        tmpl = "Static instruction with no placeholders."
        direct_out = DirectTemplateRenderer(tmpl).render()
        ref_out = TableReferenceRenderer(tmpl).render()

        self.assertEqual(direct_out, tmpl)
        self.assertEqual(ref_out, tmpl)


if __name__ == "__main__":
    unittest.main()
