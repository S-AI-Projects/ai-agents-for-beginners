"""Automated Unit Tests for Canonical JSON and Action Digest Verification (R17-T049)

Lesson Alignment:
18-securing-ai-agents (Securing AI Agents with Cryptographic Receipts)

Contract Checks:
1. Canonicalize action records to deterministic JSON and compute SHA-256 digests.
2. Reordered dictionary keys must preserve the digest.
3. Modifying arguments must invalidate the digest.
4. State explicitly that a hash digest alone is not an authenticated digital signature.
5. Scenario assessment: 3 applied scenario assessment questions with executable checks.
"""

import hashlib
import unittest
try:
    from example import (
        canonicalize_json,
        compute_sha256_digest,
        verify_action_integrity,
        ActionRecord,
        CANONICAL_ACTION_RECORD,
        PREDICTED_CANONICAL_JSON,
        PREDICTED_SHA256_DIGEST,
        APPLIED_QUESTIONS,
        HASH_VS_SIGNATURE_BOUNDARY_STATEMENT,
    )
except ImportError:
    from .example import (
        canonicalize_json,
        compute_sha256_digest,
        verify_action_integrity,
        ActionRecord,
        CANONICAL_ACTION_RECORD,
        PREDICTED_CANONICAL_JSON,
        PREDICTED_SHA256_DIGEST,
        APPLIED_QUESTIONS,
        HASH_VS_SIGNATURE_BOUNDARY_STATEMENT,
    )


class TestActionDigestVerification(unittest.TestCase):
    """Test suite verifying JSON canonicalization, SHA-256 digests, tamper detection, and scenario checks."""

    def test_reordered_dictionary_keys_preserve_digest(self):
        """Reordering dictionary keys produces identical canonical JSON and identical SHA-256 digest."""
        dict_a = {"action": "book_flight", "flight_id": "FL-101", "price": 450.00}
        dict_b = {"price": 450.00, "action": "book_flight", "flight_id": "FL-101"}
        dict_c = {"flight_id": "FL-101", "price": 450.00, "action": "book_flight"}

        canon_a = canonicalize_json(dict_a)
        canon_b = canonicalize_json(dict_b)
        canon_c = canonicalize_json(dict_c)

        self.assertEqual(canon_a, canon_b)
        self.assertEqual(canon_b, canon_c)

        digest_a = compute_sha256_digest(dict_a)
        digest_b = compute_sha256_digest(dict_b)
        digest_c = compute_sha256_digest(dict_c)

        self.assertEqual(digest_a, digest_b)
        self.assertEqual(digest_b, digest_c)

    def test_nested_reordered_keys_preserve_digest(self):
        """Nested dictionaries with differing key orders are canonicalized identically."""
        payload_1 = {
            "agent": "travel-bot",
            "metadata": {"region": "us-west", "tier": "gold"},
            "params": {"passengers": [{"name": "Bob", "seat": "12A"}]},
        }
        payload_2 = {
            "params": {"passengers": [{"seat": "12A", "name": "Bob"}]},
            "metadata": {"tier": "gold", "region": "us-west"},
            "agent": "travel-bot",
        }

        self.assertEqual(canonicalize_json(payload_1), canonicalize_json(payload_2))
        self.assertEqual(compute_sha256_digest(payload_1), compute_sha256_digest(payload_2))

    def test_modifying_argument_invalidates_digest(self):
        """Altering any argument or field invalidates the SHA-256 digest and fails integrity check."""
        original = {"action": "transfer", "amount": 100, "to": "Alice"}
        original_digest = compute_sha256_digest(original)

        tampered_variants = [
            {"action": "transfer", "amount": 101, "to": "Alice"},
            {"action": "transfer", "amount": 100, "to": "Mallory"},
            {"action": "withdraw", "amount": 100, "to": "Alice"},
            {"action": "transfer", "amount": 100, "to": "Alice", "extra": "injected"},
        ]

        for variant in tampered_variants:
            with self.subTest(variant=variant):
                variant_digest = compute_sha256_digest(variant)
                self.assertNotEqual(original_digest, variant_digest)
                self.assertFalse(verify_action_integrity(variant, original_digest))

    def test_canonical_json_compactness_no_whitespace(self):
        """Canonical JSON contains no insignificant whitespace between keys and values."""
        data = {"b": 2, "a": 1}
        canon = canonicalize_json(data)
        self.assertEqual(canon, '{"a":1,"b":2}')
        self.assertNotIn(" ", canon)
        self.assertNotIn("\n", canon)

    def test_action_record_dataclass_methods(self):
        """ActionRecord methods compute matching canonical JSON and digests."""
        record = ActionRecord(
            action_type="cancel_ticket",
            target_service="airline_api",
            arguments={"ticket_id": "TK-999", "fee": 25.0},
        )
        canon = record.to_canonical_json()
        digest = record.compute_digest()

        self.assertTrue(verify_action_integrity(asdict_data := {
            "action_type": "cancel_ticket",
            "target_service": "airline_api",
            "arguments": {"fee": 25.0, "ticket_id": "TK-999"},
            "agent_id": "agent-contoso-travel",
        }, digest))

    def test_signature_boundary_statement_explicitly_stated(self):
        """System explicitly documents that a hash digest alone is NOT a digital signature."""
        stmt = HASH_VS_SIGNATURE_BOUNDARY_STATEMENT
        self.assertIn("NOT AN AUTHENTICATED DIGITAL SIGNATURE", stmt)
        self.assertIn("tamper detection", stmt.lower())
        self.assertIn("asymmetric", stmt.lower())
        self.assertIn("ed25519", stmt.lower())

    def test_applied_question_1_output_prediction(self):
        """Applied Question 1: Output prediction matches predicted canonical JSON and digest."""
        q1 = APPLIED_QUESTIONS["question_1_output_prediction"]
        self.assertEqual(q1["expected_canonical_json"], PREDICTED_CANONICAL_JSON)
        self.assertEqual(q1["expected_digest"], PREDICTED_SHA256_DIGEST)
        self.assertTrue(q1["check"]())

    def test_applied_question_2_tamper_detection(self):
        """Applied Question 2: Tamper detection check executes and passes."""
        q2 = APPLIED_QUESTIONS["question_2_tamper_detection"]
        self.assertTrue(q2["check"]())

    def test_applied_question_3_signature_boundary(self):
        """Applied Question 3: Signature boundary check executes and passes."""
        q3 = APPLIED_QUESTIONS["question_3_signature_boundary"]
        self.assertTrue(q3["check"]())

    def test_all_applied_questions_pass(self):
        """All applied scenario assessment questions evaluate to True."""
        for q_id, q_data in APPLIED_QUESTIONS.items():
            with self.subTest(question=q_id):
                self.assertTrue(q_data["check"](), f"Check failed for {q_id}")


if __name__ == "__main__":
    unittest.main()
