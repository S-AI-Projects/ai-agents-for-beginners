DOCS = {"A": "red apple", "B": "green apple", "C": "blue sky"}


def normalize(text):
    return set(text.lower().split())


def retrieve(query, docs=DOCS):
    trace = []
    terms = normalize(query)
    trace.append(("normalize", sorted(terms)))
    scores = {doc_id: len(terms & normalize(text)) for doc_id, text in docs.items()}
    trace.append(("score", dict(scores)))
    ranked = sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))
    trace.append(("rank", list(ranked)))
    hits = [(doc_id, scores[doc_id]) for doc_id in ranked if scores[doc_id] > 0]
    trace.append(("filter", [doc_id for doc_id, _ in hits]))
    return hits, trace


if __name__ == "__main__":
    for query in ("red apple", "ocean"):
        hits, trace = retrieve(query)
        print(query, "->", hits)
        for step, state in trace:
            print("  ", step, state)
