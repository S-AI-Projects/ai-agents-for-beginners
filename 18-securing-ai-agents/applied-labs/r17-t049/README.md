# Applied Lab: Canonical JSON and Action Digest Verification (R17-T049)

**Lesson Alignment**: [Lesson 18: Securing AI Agents with Cryptographic Receipts](../../README.md)

---

## Overview

When building autonomous AI agents that perform sensitive actions (booking travel, executing financial transactions, modifying system states), maintaining tamper-evident audit trails is critical. 

Standard JSON serializers introduce non-determinism across platforms, runtimes, and serialization passes (such as inconsistent key ordering and varying whitespace). Before any payload can be reliably hashed or signed, it must be canonicalized into a strictly deterministic byte sequence.

This applied lab implements:
1. **Deterministic JSON Canonicalization** based on **RFC 8785** (JSON Canonicalization Scheme - JCS).
2. **SHA-256 Digest Computation** over canonical UTF-8 bytes.
3. **Key Reordering Invariance**: Dictionaries with identical key-value pairs produce identical canonical strings and digests regardless of initial key ordering.
4. **Tamper Detection**: Any modification to action arguments or metadata immediately invalidates the digest.
5. **Cryptographic Boundary Specification**: Explicit documentation of the boundary between hash digests (integrity only) and asymmetric digital signatures (authenticity & non-repudiation).
6. **Scenario Assessment**: 3 executable scenario questions evaluating canonical output prediction, tamper detection, and signature boundaries.

---

## Core Specification & Guarantees

### 1. RFC 8785 Canonicalization Rules
- **Lexicographical Key Sorting**: Object keys are sorted lexicographically at all recursive dictionary nesting levels.
- **Compact Separators**: No insignificant whitespace between tokens (`separators=(',', ':')`).
- **UTF-8 Encoding**: Character data is encoded directly without unnecessary unicode escaping (`ensure_ascii=False`).

### 2. Hash vs. Digital Signature Boundary
> [!IMPORTANT]
> **A SHA-256 hash digest alone is NOT an authenticated digital signature.**
> A hash digest verifies **data integrity** (confirming that bits have not changed since the digest was computed). However, a bare hash does not provide **authenticity** or **non-repudiation**. Anyone with access to the data can tamper with arguments and recompute a valid SHA-256 hash over the forged payload.
> True non-repudiation requires **asymmetric cryptography** (such as Ed25519 or ECDSA), where the agent signs the canonical payload digest using a secure private key, allowing verifiers to authenticate the signer's identity using their public key.

---

## Applied Scenario Assessment

The lab includes three executable assessment questions in `APPLIED_QUESTIONS`:

| Question ID | Concept | Description |
| :--- | :--- | :--- |
| `question_1_output_prediction` | Canonical Output Prediction | Predicts the exact canonical JSON string `{"action":"flight_search","destination":"HNL","origin":"PDX"}` and its SHA-256 digest `6efb3c9615b1292c16f7c57dfc12507b3257105ae9393b9789bdde7723e536bd`. |
| `question_2_tamper_detection` | Tamper Detection | Demonstrates that modifying any argument (e.g. destination `HNL` -> `OGG`) produces a completely different digest and causes `verify_action_integrity` to fail. |
| `question_3_signature_boundary` | Signature Boundary | Verifies that a bare hash does not guarantee signer identity or resist forgery, confirming the need for asymmetric signatures for non-repudiation. |

---

## Lab Files

- `example.py`: Core implementation containing `canonicalize_json()`, `compute_sha256_digest()`, `verify_action_integrity()`, `ActionRecord`, `HASH_VS_SIGNATURE_BOUNDARY_STATEMENT`, and `APPLIED_QUESTIONS`.
- `test_example.py`: Comprehensive test suite verifying key reordering invariance, nested dictionary handling, compact formatting, tampering detection, dataclass helpers, and all 3 applied questions.

---

## Running the Lab and Tests

### 1. Run the Interactive Example
```bash
python3 18-securing-ai-agents/applied-labs/r17-t049/example.py
```

### 2. Run the Unit Test Suite
```bash
python3 -m unittest discover -s 18-securing-ai-agents/applied-labs/r17-t049 -p "test_*.py" -v
```
