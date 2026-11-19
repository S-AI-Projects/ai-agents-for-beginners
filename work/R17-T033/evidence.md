# R17-T033 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 05-agentic-rag/applied-labs/r17-t033 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 6 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`if scores[doc_id] > 0` -> `if scores[doc_id] >= 0`) | nonzero exit | exit 1 |

## Example output

```
red apple -> [('A', 2), ('B', 1)]
   normalize ['apple', 'red']
   score {'A': 2, 'B': 1, 'C': 0}
   rank ['A', 'B', 'C']
   filter ['A', 'B']
ocean -> []
   normalize ['ocean']
   score {'A': 0, 'B': 0, 'C': 0}
   rank ['A', 'B', 'C']
   filter []
```

## Test output

```
......
----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `if scores[doc_id] > 0` to `if scores[doc_id] >= 0` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=9)
```
