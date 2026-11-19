DOCS = {"A": "red apple", "B": "green apple", "C": "blue sky"}


def lexical_adapter(docs):
    def search(query):
        terms = set(query.lower().split())
        scored = [(doc_id, len(terms & set(text.lower().split()))) for doc_id, text in docs.items()]
        hits = [(doc_id, score) for doc_id, score in scored if score > 0]
        return [doc_id for doc_id, _ in sorted(hits, key=lambda hit: (-hit[1], hit[0]))]

    return search


def answer_with_sources(query, search):
    try:
        sources = search(query)
    except Exception:
        return {"query": query, "status": "unavailable", "sources": []}
    return {"query": query, "status": "found" if sources else "no_match", "sources": sources}


if __name__ == "__main__":
    search = lexical_adapter(DOCS)
    for query in ("red apple", "ocean"):
        print(answer_with_sources(query, search))
