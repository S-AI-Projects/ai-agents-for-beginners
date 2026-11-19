# R17-T039 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 13-agent-memory/applied-labs/r17-t039 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 7 tests in 0.001s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`self._records.pop(0)` -> `self._records.pop()`) | nonzero exit | exit 1 |

## Example output

```
empty: []
one record: ['A']
exactly full: ['A', 'B', 'C']
one over: ['B', 'C', 'D']
smallest capacity: ['B']
capacity 0: capacity must be a positive integer
capacity -1: capacity must be a positive integer
capacity '3': capacity must be a positive integer
capacity True: capacity must be a positive integer
```

## Test output

```
.......
----------------------------------------------------------------------
Ran 7 tests in 0.001s

OK
```

## Deliberate wrong result

Changed `self._records.pop(0)` to `self._records.pop()` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=3)
```
