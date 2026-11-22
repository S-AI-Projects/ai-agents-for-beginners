"""Automated Unit Tests for Safe Template Rendering & Context Evaluation (R17-T048)

Lesson Alignment:
12-context-engineering (Context Engineering: Variable Substitution, Template Safety & Prompt Injection Boundaries)

Contract Checks:
1. Render templates from declared variables.
2. Missing keys are rejected with MissingTemplateVariableError specifying the missing key.
3. Braces inside user data remain literal and are never evaluated as nested template keys.
4. Security boundary: Documentation explicitly disclaims that templating alone prevents prompt injection.
5. Evaluation experiment across 3 controlled variations (standard, nested injection braces, large payload).
"""

import unittest
try:
    from example import (
        SafeTemplateRenderer,
        render_template,
        MissingTemplateVariableError,
        run_evaluation_experiment,
        PROMPT_INJECTION_SECURITY_DISCLAIMER,
    )
except ImportError:
    from .example import (
        SafeTemplateRenderer,
        render_template,
        MissingTemplateVariableError,
        run_evaluation_experiment,
        PROMPT_INJECTION_SECURITY_DISCLAIMER,
    )


class TestSafeTemplateRenderer(unittest.TestCase):
    """Test suite verifying safe template substitution, literal brace handling, and evaluation."""

    def test_canonical_variable_rendering(self):
        """Templates render successfully using declared variables."""
        template = "Hello {name}, your role is {{role}}."
        variables = {"name": "Alice", "role": "Engineer"}
        rendered = render_template(template, variables)
        self.assertEqual(rendered, "Hello Alice, your role is Engineer.")

    def test_missing_variable_raises_exception(self):
        """Missing placeholder variable raises MissingTemplateVariableError identifying missing key."""
        template = "Greeting: {greeting}, User: {user_id}"
        with self.assertRaises(MissingTemplateVariableError) as ctx:
            render_template(template, {"greeting": "Welcome"})

        self.assertEqual(ctx.exception.missing_key, "user_id")
        self.assertIn("user_id", str(ctx.exception))
        self.assertIn("greeting", ctx.exception.available_keys)

    def test_literal_braces_in_user_data_never_evaluated(self):
        """Braces inside user data remain literal and are NEVER evaluated as nested template keys."""
        template = "System Instruction: {instruction}\nUser Query: {user_query}"
        adversarial_query = (
            "Here is a curly brace {secret_api_key} and double {{system_password}} "
            "and JSON payload: {\"action\": \"delete_all\", \"count\": 42}."
        )
        variables = {
            "instruction": "Answer queries helpfully.",
            "user_query": adversarial_query,
            # Notice: 'secret_api_key' and 'system_password' are NOT in variables!
            # If the engine tried to evaluate nested braces in user_query, it would fail or crash.
        }

        rendered = render_template(template, variables)

        # Invariant: The adversarial query must exist verbatim in the rendered string
        self.assertIn(adversarial_query, rendered)
        self.assertIn("{secret_api_key}", rendered)
        self.assertIn("{{system_password}}", rendered)
        self.assertIn("{\"action\": \"delete_all\", \"count\": 42}", rendered)

    def test_nested_macro_injection_does_not_expand(self):
        """Nested macro syntax like {{7*7}} or {eval(x)} in user data is treated as plain text."""
        template = "User Message: {msg}"
        raw_msg = "{{7*7}} {10+20} {{import os}}"
        rendered = render_template(template, {"msg": raw_msg})
        self.assertEqual(rendered, f"User Message: {raw_msg}")
        self.assertNotIn("49", rendered)
        self.assertNotIn("30", rendered)

    def test_security_disclaimer_presence_and_claims(self):
        """Does NOT claim templating alone prevents prompt injection; documents semantic limits."""
        disclaimer = PROMPT_INJECTION_SECURITY_DISCLAIMER
        self.assertIn("TEMPLATING ALONE DOES NOT PREVENT SEMANTIC PROMPT INJECTION", disclaimer)
        self.assertIn("syntactic isolation", disclaimer)
        self.assertIn("defense-in-depth", disclaimer)

    def test_evaluation_experiment_benchmarks_three_variations(self):
        """Evaluation experiment benchmarks 3 controlled variations with all invariants passing."""
        benchmarks = run_evaluation_experiment()
        self.assertEqual(len(benchmarks), 3)

        variation_names = [b.variation_name for b in benchmarks]
        self.assertIn("Standard Payload", variation_names)
        self.assertIn("Nested Injection Braces Payload", variation_names)
        self.assertIn("Large Context Payload (50KB+)", variation_names)

        for b in benchmarks:
            self.assertTrue(b.literal_braces_preserved)
            self.assertTrue(b.missing_key_enforced)
            self.assertTrue(b.security_disclaimer_acknowledged)
            self.assertGreater(b.rendered_size_chars, 0)
            self.assertGreaterEqual(b.duration_ms, 0.0)

    def test_empty_template_and_empty_variables(self):
        """Empty templates and non-variable templates render cleanly."""
        self.assertEqual(render_template("", {}), "")
        self.assertEqual(render_template("Static text without variables", {}), "Static text without variables")

    def test_referenced_keys_property(self):
        """SafeTemplateRenderer correctly exposes all declared keys in template."""
        renderer = SafeTemplateRenderer("A: {a}, B: {{b}}, C: {c}, D: {{d}}")
        self.assertEqual(renderer.referenced_keys, {"a", "b", "c", "d"})


if __name__ == "__main__":
    unittest.main()
