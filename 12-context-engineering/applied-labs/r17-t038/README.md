# Prompt Template Failure and Recovery

Task R17-T038 for the lesson [Context Engineering for AI Agents](../../README.md).

## How it relates to the lesson

Context engineering controls what goes into the model context. This lab renders a template from declared variables, rejects missing or unknown keys, keeps user data out of the fixed instruction message, and shows the next valid input rendering normally after a failure.

## Fixture

Template `Hello {name}, please summarize {topic}.` with `{"name": "Asha"}` (missing `topic`), then `{"name": "Asha", "topic": "{weather} reports"}`.

## Run

```bash
python3 12-context-engineering/applied-labs/r17-t038/example.py
python3 -m unittest discover -s 12-context-engineering/applied-labs/r17-t038 -p "test_*.py"
```

Expected output of the example:

```text
{'ok': False, 'error': 'missing variables: topic'}
{'ok': True, 'messages': [{'role': 'system', 'content': 'You are a concise study assistant.'}, {'role': 'user', 'content': 'Hello Asha, please summarize {weather} reports.'}]}
```

## Where the simplification stops

Templating alone does not prevent prompt injection: user text is still passed to the model and can contain instructions. This lab only guarantees that braces in user data are not re-expanded.
