# Evidence Dossier: R17-T049 (GitHub Issue #50)

**Branch**: `NirmalAdhau/e26b07f2790/R17-T049`  
**Lesson Directory**: `18-securing-ai-agents`  
**Lab Directory**: `18-securing-ai-agents/applied-labs/r17-t049`

---

## 1. Compliance Matrix

| Requirement | Implementation Details | Test Coverage | Status |
| :--- | :--- | :--- | :--- |
| **RFC 8785 JSON Canonicalization** | `canonicalize_json()` sorts all dictionary keys lexicographically at recursive depths, strips insignificant whitespace (`(',', ':')`), and preserves UTF-8. | `test_canonical_json_compactness_no_whitespace`, `test_nested_reordered_keys_preserve_digest` | **PASS** |
| **Deterministic SHA-256 Digest** | `compute_sha256_digest()` returns lowercase hexadecimal digest over canonical UTF-8 bytes. | `test_applied_question_1_output_prediction` | **PASS** |
| **Key Invariance** | Reordered dictionary keys produce identical canonical representations and identical SHA-256 digests. | `test_reordered_dictionary_keys_preserve_digest`, `test_nested_reordered_keys_preserve_digest` | **PASS** |
| **Tamper Invalidation** | Modifying any payload field or argument invalidates the digest and fails `verify_action_integrity()`. | `test_modifying_argument_invalidates_digest`, `test_applied_question_2_tamper_detection` | **PASS** |
| **Explicit Cryptographic Boundary Statement** | Formally documents that a hash digest provides data integrity but NOT digital signatures or non-repudiation. | `test_signature_boundary_statement_explicitly_stated`, `test_applied_question_3_signature_boundary` | **PASS** |
| **Applied Scenario Assessment** | 3 scenario questions with executable check lambdas covering output prediction, tampering, and signature boundaries. | `test_applied_question_1_output_prediction`, `test_applied_question_2_tamper_detection`, `test_applied_question_3_signature_boundary`, `test_all_applied_questions_pass` | **PASS** |
| **Zero External Dependencies** | Uses only Python 3 standard library (`dataclasses`, `hashlib`, `json`, `typing`, `unittest`). | Environment verification | **PASS** |

---

## 2. Test Execution Summary

Command:
```bash
python3 -m unittest discover -s 18-securing-ai-agents/applied-labs/r17-t049 -p "test_*.py" -v
```

Output:
```
Ran 10 tests in 0.000s

OK
```

See [test_results.txt](./test_results.txt) and [example_run.txt](./example_run.txt) for full output logs.
