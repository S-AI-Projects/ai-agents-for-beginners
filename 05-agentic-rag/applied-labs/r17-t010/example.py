"""R17-T010: Lexical retriever scenario assessment."""
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

def assess_q1_predict(r): return r.retrieve("green")
def assess_q2_diagnose(r): return r.retrieve("RED APPLE")
def assess_q3_boundary(r): return r.retrieve("")
