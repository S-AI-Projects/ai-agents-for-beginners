# R17-T040 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 09-metacognition/applied-labs/r17-t040 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 7 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`confidence >= CONFIDENCE_THRESHOLD` -> `confidence > CONFIDENCE_THRESHOLD`) | nonzero exit | exit 1 |

## Example output

```
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

## Test output

```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `confidence >= CONFIDENCE_THRESHOLD` to `confidence > CONFIDENCE_THRESHOLD` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=3)
```
