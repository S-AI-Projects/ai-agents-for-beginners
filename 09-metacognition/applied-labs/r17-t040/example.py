CONFIDENCE_THRESHOLD = 0.8
EVIDENCE_THRESHOLD = 2


def route(confidence, evidence_count):
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if evidence_count < 0:
        raise ValueError("evidence_count cannot be negative")
    if confidence >= CONFIDENCE_THRESHOLD and evidence_count >= EVIDENCE_THRESHOLD:
        return "answer"
    return "review"


def rejects(confidence, evidence_count):
    try:
        route(confidence, evidence_count)
    except ValueError:
        return True
    return False


QUESTIONS = [
    {
        "prompt": "Predict the output of route(0.8, 2).",
        "answer": "answer",
        "rationale": "0.8 meets the >= 0.8 confidence threshold and 2 meets the >= 2 evidence threshold.",
        "check": lambda: route(0.8, 2) == "answer",
    },
    {
        "prompt": "route(0.1 + 0.7, 3) returns review although the intended confidence is 0.8. Why?",
        "answer": "0.1 + 0.7 is 0.7999999999999999 in floating point, which is below 0.8.",
        "rationale": "The comparison is exact, so rounding error pushes the score under the threshold. Rounding the score first restores answer.",
        "check": lambda: 0.1 + 0.7 < 0.8
        and route(0.1 + 0.7, 3) == "review"
        and route(round(0.1 + 0.7, 2), 3) == "answer",
    },
    {
        "prompt": "A scorer returns 1.2. Should route clamp it to 1 or reject it?",
        "answer": "Reject it.",
        "rationale": "A value outside 0..1 means the scorer is broken; clamping would turn corrupt output into a top-confidence answer.",
        "check": lambda: rejects(1.2, 3) and rejects(-0.1, 3) and route(1, 2) == "answer" and route(0, 2) == "review",
    },
]


if __name__ == "__main__":
    for number, question in enumerate(QUESTIONS, start=1):
        print(f"Q{number}. {question['prompt']}")
        print(f"    answer: {question['answer']}")
        print(f"    check passed: {question['check']()}")
