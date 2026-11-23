#!/usr/bin/env python3
"""Unit tests for Tamper-Evident Action Receipt — Worked Example with Checks (R17-T017)."""

import unittest

from example import (
    SECURITY_NOTICE,
    WORKED_EXAMPLE_RECORD,
    compute_action_digest,
    verify_receipt,
)


class TestTamperEvidentReceipt(unittest.TestCase):
    EXPECTED_CANONICAL = '{"action":"execute_transfer","actor":"agent_copilot_01","args":{"amount":2500,"currency":"USD","recipient":"vendor_account_992"},"timestamp":"2026-11-23T12:00:00Z"}'
    EXPECTED_DIGEST = "d1cc660bde4a87a9de04ae2f72226ee5af7b8366c15a5a1c2df0dca0459e7819"

    def test_worked_example_regression_hash(self) -> None:
        """Execute exact worked example as a regression test."""
        canonical, digest = compute_action_digest(WORKED_EXAMPLE_RECORD)
        self.assertEqual(canonical, self.EXPECTED_CANONICAL)
        self.assertEqual(digest, self.EXPECTED_DIGEST)
        self.assertTrue(verify_receipt(WORKED_EXAMPLE_RECORD, self.EXPECTED_DIGEST))

    def test_reordered_json_keys_preserve_digest(self) -> None:
        # Reordered JSON keys preserve the digest
        reordered = {
            "timestamp": "2026-11-23T12:00:00Z",
            "action": "execute_transfer",
            "actor": "agent_copilot_01",
            "args": {
                "currency": "USD",
                "recipient": "vendor_account_992",
                "amount": 2500,
            },
        }
        _, reordered_digest = compute_action_digest(reordered)
        self.assertEqual(reordered_digest, self.EXPECTED_DIGEST)
        self.assertTrue(verify_receipt(reordered, self.EXPECTED_DIGEST))

    def test_changing_action_argument_invalidates_receipt(self) -> None:
        # Changing an action argument invalidates it
        tampered = {
            "actor": "agent_copilot_01",
            "action": "execute_transfer",
            "args": {
                "recipient": "vendor_account_992",
                "amount": 2501,  # Altered value
                "currency": "USD",
            },
            "timestamp": "2026-11-23T12:00:00Z",
        }
        _, tampered_digest = compute_action_digest(tampered)
        self.assertNotEqual(tampered_digest, self.EXPECTED_DIGEST)
        self.assertFalse(verify_receipt(tampered, self.EXPECTED_DIGEST))

    def test_security_limitation_statement_explicitly_present(self) -> None:
        # State explicitly that a hash alone is not an authenticated signature
        self.assertIn("NOT an authenticated signature", SECURITY_NOTICE)
        self.assertIn("Ed25519", SECURITY_NOTICE)


if __name__ == "__main__":
    unittest.main()
