# R17-T035 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 11-agentic-protocols/applied-labs/r17-t035 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 5 tests in 0.001s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`records[-limit:]` -> `records[:limit]`) | nonzero exit | exit 1 |

## Example output

```
BaselineMemory ['B', 'C', 'D']
Memory ['B', 'C', 'D']
```

## Test output

```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
```

## Deliberate wrong result

Changed `records[-limit:]` to `records[:limit]` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=20)
```
