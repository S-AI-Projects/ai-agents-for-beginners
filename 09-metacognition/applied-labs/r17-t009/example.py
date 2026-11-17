"""R17-T009: Confidence-gated routing."""
class MetacognitiveRouter:
    def route(self, confidence, evidence_count):
        if not (0.0 <= confidence <= 1.0) or evidence_count < 0:
            raise ValueError("Confidence must be in 0..1 and evidence >= 0")
        if confidence >= 0.8 and evidence_count >= 2:
            return "answer"
        return "review"
