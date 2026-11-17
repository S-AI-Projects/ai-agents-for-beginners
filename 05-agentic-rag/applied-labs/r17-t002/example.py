"""R17-T002: Retrieval with source attribution."""
import re
DEFAULT_DOCS = {"A": "red apple", "B": "green apple", "C": "blue sky"}

class LexicalRetriever:
    def __init__(self, documents=None):
        self.docs = documents or DEFAULT_DOCS

    def _tokens(self, text):
        return set(re.findall(r'\w+', text.lower()))

    def retrieve(self, query):
        q = self._tokens(query)
        if not q:
            return []
        matches = []
        for doc_id, text in self.docs.items():
            overlap = len(q & self._tokens(text))
            if overlap > 0:
                matches.append({"doc_id": doc_id, "score": overlap, "content": text})
        matches.sort(key=lambda x: (-x["score"], x["doc_id"]))
        return matches
