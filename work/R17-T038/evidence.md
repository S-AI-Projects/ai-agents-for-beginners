# R17-T038 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 12-context-engineering/applied-labs/r17-t038 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 6 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`if missing:` -> `if False:`) | nonzero exit | exit 1 |

## Example output

```
{'ok': False, 'error': 'missing variables: topic'}
{'ok': True, 'messages': [{'role': 'system', 'content': 'You are a concise study assistant.'}, {'role': 'user', 'content': 'Hello Asha, please summarize {weather} reports.'}]}
```

## Test output

```
......
----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `if missing:` to `if False:` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (errors=2)
```
