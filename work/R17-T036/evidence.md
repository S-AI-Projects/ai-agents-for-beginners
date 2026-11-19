# R17-T036 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 13-agent-memory/applied-labs/r17-t036 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 4 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`self._records.pop(0)` -> `self._records.pop()`) | nonzero exit | exit 1 |

## Example output

```
capacity  kept             correct  recall_newest
1         F                True     0.33
3         DEF              True     1.0
5         BCDEF            True     1.0
```

## Test output

```
....
----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `self._records.pop(0)` to `self._records.pop()` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=5)
```
