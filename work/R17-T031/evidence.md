# R17-T031 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 16-deploying-scalable-agents/applied-labs/r17-t031 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 5 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`["tool_calls"] += 1` -> `["tool_calls"] += 2`) | nonzero exit | exit 1 |

## Example output

```
{
  "A": {
    "duration_ms": 12,
    "tool_calls": 2,
    "status": "success"
  },
  "B": {
    "duration_ms": 7,
    "tool_calls": 0,
    "status": "failure"
  },
  "C": {
    "duration_ms": null,
    "tool_calls": 1,
    "status": "incomplete"
  }
}
```

## Test output

```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `["tool_calls"] += 1` to `["tool_calls"] += 2` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=2)
```
