# R17-T034 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 05-agentic-rag/applied-labs/r17-t034 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 5 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`if score > 0` -> `if score >= 0`) | nonzero exit | exit 1 |

## Example output

```
{'query': 'red apple', 'status': 'found', 'sources': ['A', 'B']}
{'query': 'ocean', 'status': 'no_match', 'sources': []}
```

## Test output

```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `if score > 0` to `if score >= 0` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=3)
```
