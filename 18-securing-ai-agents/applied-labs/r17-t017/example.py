#!/usr/bin/env python3
"""Tamper-Evident Action Receipt — Worked Example with Checks (R17-T017).

Demonstrates cryptographic receipts for securing AI agent actions:
- Canonical JSON serialization (RFC 8785 principles: sorted keys, compact separators).
- SHA-256 digest computation for tamper detection.
- Reordered dictionary keys produce identical canonical JSON and matching digests.
- Modifying any argument or field invalidates the receipt digest.
- Explicit security limitation: a hash alone is NOT an authenticated signature.
  A digest provides tamper evidence against accidental mutation; authentication
  requires an asymmetric private key signature (e.g. Ed25519) or HMAC.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


# Explicit Security Notice
SECURITY_NOTICE = (
    "SECURITY LIMITATION: A cryptographic hash (e.g. SHA-256) alone is NOT an authenticated signature. "
    "Anyone with access to the payload can recompute a valid hash over tampered data. "
    "True non-repudiation and origin authenticity require asymmetric cryptographic signatures (such as Ed25519) "
    "or keyed message authentication codes (HMAC) holding a private secret."
)


@dataclass(frozen=True)
class ActionReceipt:
    canonical_payload: str
    sha256_digest: str
    is_valid: bool
    notice: str = SECURITY_NOTICE


def canonicalize_record(record: Dict[str, Any]) -> str:
    """Canonicalize a dictionary into deterministic JSON (sorted keys, compact delimiters)."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_action_digest(record: Dict[str, Any]) -> Tuple[str, str]:
    """Computes canonical JSON string and its SHA-256 hex digest."""
    canonical = canonicalize_record(record)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return canonical, digest


def verify_receipt(record: Dict[str, Any], expected_digest: str) -> bool:
    """Verifies that re-canonicalizing the record produces the expected SHA-256 digest."""
    _, computed_digest = compute_action_digest(record)
    return computed_digest == expected_digest


# Worked example action record
WORKED_EXAMPLE_RECORD: Dict[str, Any] = {
    "actor": "agent_copilot_01",
    "action": "execute_transfer",
    "args": {
        "recipient": "vendor_account_992",
        "amount": 2500,
        "currency": "USD"
    },
    "timestamp": "2026-11-23T12:00:00Z"
}


def main() -> None:
    print("=== Tamper-Evident Action Receipt Worked Example ===")
    print("Notice:\n", SECURITY_NOTICE, "\n")

    canonical, digest = compute_action_digest(WORKED_EXAMPLE_RECORD)
    print("1. Original Record:", WORKED_EXAMPLE_RECORD)
    print("2. Canonical JSON:", canonical)
    print("3. SHA-256 Digest:", digest)

    # Key reordering test
    reordered_record = {
        "timestamp": "2026-11-23T12:00:00Z",
        "action": "execute_transfer",
        "actor": "agent_copilot_01",
        "args": {
            "currency": "USD",
            "amount": 2500,
            "recipient": "vendor_account_992"
        }
    }
    reordered_canonical, reordered_digest = compute_action_digest(reordered_record)
    print("4. Reordered Digest matches:", reordered_digest == digest)

    # Tampered argument test
    tampered_record = dict(WORKED_EXAMPLE_RECORD)
    tampered_record["args"] = dict(WORKED_EXAMPLE_RECORD["args"])
    tampered_record["args"]["amount"] = 999999  # Tampered!
    is_valid_tampered = verify_receipt(tampered_record, digest)
    print("5. Tampered Record verified:", is_valid_tampered)


if __name__ == "__main__":
    main()
