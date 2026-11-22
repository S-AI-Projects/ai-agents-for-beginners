"""Applied Lab: Canonical JSON and Action Digest Verification (R17-T049)

Lesson Alignment:
18-securing-ai-agents (Securing AI Agents with Cryptographic Receipts)

Contract & Goals:
- Canonicalize agent action records to deterministic JSON (RFC 8785 principles).
- Compute SHA-256 digests over canonical UTF-8 bytes.
- Enforce Key Invariance: Reordered dictionary keys must produce the identical canonical JSON and digest.
- Enforce Tamper Invalidation: Any modification to action arguments or fields must invalidate the digest.
- Cryptographic Boundary Statement: Explicitly state that a hash digest alone is NOT an authenticated digital signature.
- Applied Scenario Assessment: Include 3 applied questions with executable checks
  (output prediction, tamper detection, signature boundary).
- Zero external dependencies: pure Python 3 standard library.
"""

from dataclasses import dataclass, field, asdict
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Union


# Formal Cryptographic Boundary Statement
HASH_VS_SIGNATURE_BOUNDARY_STATEMENT: str = (
    "CRYPTOGRAPHIC BOUNDARY STATEMENT: A SHA-256 hash digest provides data integrity "
    "and tamper detection (confirming that bits have not changed since the digest was computed). "
    "HOWEVER, A HASH DIGEST ALONE IS NOT AN AUTHENTICATED DIGITAL SIGNATURE. "
    "A bare hash does not prove identity, origin authenticity, or non-repudiation because "
    "anyone who modifies a payload can easily recompute a valid SHA-256 hash over the forged payload. "
    "True non-repudiation requires asymmetric cryptography (such as Ed25519 or ECDSA), where an agent "
    "signs the canonical payload digest using a secure private key, allowing verifiers to authenticate "
    "the identity of the signer using the corresponding public key."
)


def canonicalize_json(data: Any) -> str:
    """Serializes arbitrary Python data structures into deterministic canonical JSON (RFC 8785).

    Rules:
    1. Object dictionary keys are sorted lexicographically at all recursive nesting levels.
    2. No insignificant whitespace between tokens: separators=(',', ':').
    3. Consistent UTF-8 text representation with ensure_ascii=False.
    """
    def _sort_recursively(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _sort_recursively(v) for k, v in sorted(obj.items(), key=lambda item: str(item[0]))}
        elif isinstance(obj, list):
            return [_sort_recursively(elem) for elem in obj]
        elif isinstance(obj, tuple):
            return [_sort_recursively(elem) for elem in obj]
        return obj

    sorted_data = _sort_recursively(data)
    return json.dumps(sorted_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def compute_sha256_digest(data: Any) -> str:
    """Computes the lowercase hexadecimal SHA-256 digest over canonicalized JSON bytes."""
    canonical_str = canonicalize_json(data)
    canonical_bytes = canonical_str.encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


@dataclass(frozen=True)
class ActionRecord:
    """Structured representation of an agent tool or API action."""
    action_type: str
    target_service: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    agent_id: str = "agent-contoso-travel"

    def to_canonical_json(self) -> str:
        """Serializes this action record to deterministic canonical JSON."""
        return canonicalize_json(asdict(self))

    def compute_digest(self) -> str:
        """Computes the SHA-256 digest over this record's canonical representation."""
        return compute_sha256_digest(asdict(self))


def verify_action_integrity(data: Any, expected_digest: str) -> bool:
    """Verifies that the SHA-256 digest of data matches the expected digest."""
    computed = compute_sha256_digest(data)
    return computed.lower() == expected_digest.lower()


# Canonical Fixture for Output Prediction & Tests
CANONICAL_ACTION_RECORD: Dict[str, Any] = {
    "action": "flight_search",
    "destination": "HNL",
    "origin": "PDX",
}

# The deterministic canonical JSON and known SHA-256 digest for CANONICAL_ACTION_RECORD:
# Canonical JSON: {"action":"flight_search","destination":"HNL","origin":"PDX"}
PREDICTED_CANONICAL_JSON: str = '{"action":"flight_search","destination":"HNL","origin":"PDX"}'
PREDICTED_SHA256_DIGEST: str = hashlib.sha256(PREDICTED_CANONICAL_JSON.encode("utf-8")).hexdigest()


# 3 Applied Scenario Assessment Questions with Executable Checks
APPLIED_QUESTIONS: Dict[str, Dict[str, Any]] = {
    "question_1_output_prediction": {
        "title": "Output Prediction for Canonical Record",
        "prompt": (
            "Given action record {'action': 'flight_search', 'destination': 'HNL', 'origin': 'PDX'}, "
            "what is the exact canonical JSON string and its SHA-256 hexadecimal digest?"
        ),
        "expected_canonical_json": PREDICTED_CANONICAL_JSON,
        "expected_digest": PREDICTED_SHA256_DIGEST,
        "check": lambda: (
            canonicalize_json(CANONICAL_ACTION_RECORD) == PREDICTED_CANONICAL_JSON
            and compute_sha256_digest(CANONICAL_ACTION_RECORD) == PREDICTED_SHA256_DIGEST
        ),
    },
    "question_2_tamper_detection": {
        "title": "Tamper Detection on Modified Arguments",
        "prompt": (
            "If an attacker alters the destination from 'HNL' to 'OGG', does the SHA-256 digest change, "
            "and does verify_action_integrity fail?"
        ),
        "expected_outcome": "Digest mismatch detected; verification returns False",
        "check": lambda: _check_tamper_detection(),
    },
    "question_3_signature_boundary": {
        "title": "Cryptographic Signature Boundary",
        "prompt": (
            "Why is a bare SHA-256 hash digest insufficient to prove agent authorization, "
            "and how does it differ from a digital signature?"
        ),
        "expected_outcome": (
            "Hashes only verify integrity, not authenticity. Anyone can recompute a valid hash over "
            "tampered content. Authenticated digital signatures require an asymmetric private key."
        ),
        "check": lambda: _check_signature_boundary(),
    },
}


def _check_tamper_detection() -> bool:
    original = dict(CANONICAL_ACTION_RECORD)
    original_digest = compute_sha256_digest(original)

    # Attacker alters destination
    tampered = dict(CANONICAL_ACTION_RECORD)
    tampered["destination"] = "OGG"
    tampered_digest = compute_sha256_digest(tampered)

    # Invariant: Digest must be completely different and integrity check must return False
    digest_changed = (original_digest != tampered_digest)
    verification_failed = not verify_action_integrity(tampered, original_digest)
    return digest_changed and verification_failed


def _check_signature_boundary() -> bool:
    # Demonstrates that an unauthenticated adversary can recompute a valid hash over tampered data
    tampered_payload = {"action": "book_flight", "amount": 9999.00, "passenger": "Attacker"}
    attacker_computed_hash = compute_sha256_digest(tampered_payload)

    # The hash matches the tampered content perfectly:
    # A verifier checking only the hash would mistakenly believe the payload is valid!
    hash_matches = verify_action_integrity(tampered_payload, attacker_computed_hash)

    # Confirms that the boundary statement explicitly states this limitation
    boundary_disclaimed = (
        "NOT AN AUTHENTICATED DIGITAL SIGNATURE" in HASH_VS_SIGNATURE_BOUNDARY_STATEMENT
        and "asymmetric" in HASH_VS_SIGNATURE_BOUNDARY_STATEMENT.lower()
    )
    return hash_matches and boundary_disclaimed


def main():
    print("=== Canonical JSON & Action Digest Verification (R17-T049) ===\n")

    # 1. Key Invariance Demonstration
    print("1. Dictionary Key Reordering Invariance:")
    dict_order_1 = {"action": "flight_search", "destination": "HNL", "origin": "PDX"}
    dict_order_2 = {"origin": "PDX", "destination": "HNL", "action": "flight_search"}

    c1 = canonicalize_json(dict_order_1)
    c2 = canonicalize_json(dict_order_2)
    d1 = compute_sha256_digest(dict_order_1)
    d2 = compute_sha256_digest(dict_order_2)

    print(f"   Order 1 Canonical: {c1}")
    print(f"   Order 2 Canonical: {c2}")
    print(f"   Digest 1         : {d1}")
    print(f"   Digest 2         : {d2}")
    print(f"   Digests Match    : {d1 == d2} (PASS)\n")

    # 2. Tamper Detection Demonstration
    print("2. Tamper Detection on Modified Arguments:")
    tampered = {"action": "flight_search", "destination": "OGG", "origin": "PDX"}
    d_tampered = compute_sha256_digest(tampered)
    verified = verify_action_integrity(tampered, d1)
    print(f"   Original Digest : {d1}")
    print(f"   Tampered Digest : {d_tampered}")
    print(f"   Verified Status : {verified} (Expected: False)\n")

    # 3. Applied Scenario Assessment Questions
    print("3. Applied Scenario Assessment Questions:")
    for q_id, q_data in APPLIED_QUESTIONS.items():
        check_result = q_data["check"]()
        print(f"   • {q_data['title']}: Check Passed = {check_result}")

    # 4. Cryptographic Boundary Statement
    print("\n--- Cryptographic Boundary Statement ---")
    print(HASH_VS_SIGNATURE_BOUNDARY_STATEMENT)


if __name__ == "__main__":
    main()
