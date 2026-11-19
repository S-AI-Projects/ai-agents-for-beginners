# R17-T032 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 14-microsoft-agent-framework/applied-labs/r17-t032 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 4 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`step > max_steps` -> `step > max_steps + 1`) | nonzero exit | exit 1 |

## Example output

```
normal: completed ['inspect', 'answer', 'stop']
endless: budget_exceeded ['inspect', 'inspect', 'inspect']
stop first: completed ['stop']
stop at step 4: budget_exceeded ['inspect', 'inspect', 'inspect']
```

## Test output

```
....
----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `step > max_steps` to `step > max_steps + 1` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (failures=5)
```
