# Confidence-Gated Escalation Assessment

Task R17-T040 for the lesson [Metacognition in AI Agents](../../README.md).

## How it relates to the lesson

Metacognition covers an agent checking its own work. This lab routes a result to `answer` or `review` from a confidence score and an evidence count, and ends with three applied questions, each with a rationale and an executable check.

## Fixture

Threshold: confidence >= 0.8 and at least 2 evidence items answer; anything else is reviewed; confidence outside 0..1 raises.

## Run

```bash
python3 09-metacognition/applied-labs/r17-t040/example.py
python3 -m unittest discover -s 09-metacognition/applied-labs/r17-t040 -p "test_*.py"
```

Expected output of the example:

```text
Q1. Predict the output of route(0.8, 2).
    answer: answer
    check passed: True
Q2. route(0.1 + 0.7, 3) returns review although the intended confidence is 0.8. Why?
    answer: 0.1 + 0.7 is 0.7999999999999999 in floating point, which is below 0.8.
    check passed: True
Q3. A scorer returns 1.2. Should route clamp it to 1 or reject it?
    answer: Reject it.
    check passed: True
```

## Where the simplification stops

The thresholds are fixed by hand and the confidence value is supplied, not produced by a model. Nothing here shows that these thresholds suit a real agent.
