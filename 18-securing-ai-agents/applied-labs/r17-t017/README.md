# Applied Lab: Tamper-Evident Action Receipt — Worked Example with Checks (R17-T017)

## Overview & Lesson Alignment

In **Lesson 18: Securing AI Agents with Cryptographic Receipts**, agents perform sensitive operations (e.g. database updates, financial disbursements, cloud provisioning) requiring verifiable audit trails:
1. **Canonical JSON Serialization**: JSON keys can arrive in arbitrary order and with varying whitespace. RFC 8785 canonicalization ensures byte-level determinism by lexicographically sorting keys and removing extraneous whitespace.
2. **Tamper Evidence**: Computing a SHA-256 digest over canonical JSON allows relying parties to detect any post-execution tampering.
3. **Key Order Independence**: Reordering keys produces identical canonical bytes and matching SHA-256 digests.
4. **Parameter Integrity**: Any modification to an argument or action field invalidates the receipt digest.
5. **Security Boundary & Notice**: A cryptographic hash alone is **NOT** an authenticated signature. A hash proves integrity (the payload did not change relative to that digest), but does not prove origin authenticity or non-repudiation because anyone can re-hash tampered data. True authentication requires private key signatures (such as Ed25519) as taught in Lesson 18.

---

## Worked Example & Test Vectors

### Input Record
```json
{
  "actor": "agent_copilot_01",
  "action": "execute_transfer",
  "args": {
    "recipient": "vendor_account_992",
    "amount": 2500,
    "currency": "USD"
  },
  "timestamp": "2026-11-23T12:00:00Z"
}
```

### Canonical JSON Representation
```
{"action":"execute_transfer","actor":"agent_copilot_01","args":{"amount":2500,"currency":"USD","recipient":"vendor_account_992"},"timestamp":"2026-11-23T12:00:00Z"}
```

### Expected SHA-256 Hex Digest
`d1cc660bde4a87a9de04ae2f72226ee5af7b8366c15a5a1c2df0dca0459e7819`

---

## Running the Lab

### Run Demonstration
```bash
python3 18-securing-ai-agents/applied-labs/r17-t017/example.py
```

### Run Unit Tests
```bash
python3 -m unittest discover -s 18-securing-ai-agents/applied-labs/r17-t017 -p "test_*.py" -v
```

---

## Prerequisites
- Python 3.12+ (standard library only: `json`, `hashlib`, `dataclasses`, `unittest`).
- Zero external package dependencies.
