import re

PLACEHOLDER = re.compile(r"\{(\w+)\}")
INSTRUCTION = "You are a concise study assistant."
TEMPLATE = "Hello {name}, please summarize {topic}."


def render(template, values):
    declared = set(PLACEHOLDER.findall(template))
    missing = declared - values.keys()
    unknown = values.keys() - declared
    if missing:
        raise ValueError("missing variables: " + ", ".join(sorted(missing)))
    if unknown:
        raise ValueError("unknown variables: " + ", ".join(sorted(unknown)))
    return PLACEHOLDER.sub(lambda match: str(values[match.group(1)]), template)


def build_messages(values, instruction=INSTRUCTION, template=TEMPLATE):
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": render(template, values)},
    ]


def try_build(values):
    try:
        return {"ok": True, "messages": build_messages(values)}
    except ValueError as error:
        return {"ok": False, "error": str(error)}


if __name__ == "__main__":
    print(try_build({"name": "Asha"}))
    print(try_build({"name": "Asha", "topic": "{weather} reports"}))
