"""R17-T003: Intent routing."""
class IntentRouter:
    def route(self, text):
        t = text.lower()
        has_help = "help" in t
        has_calc = "calculate" in t
        if has_help and has_calc:
            return {"handler": "support", "rule": "priority:help_over_calculate", "request": text}
        elif has_help:
            return {"handler": "support", "rule": "direct:help", "request": text}
        elif has_calc:
            return {"handler": "calculator", "rule": "direct:calculate", "request": text}
        return {"handler": "fallback", "rule": "default:fallback", "request": text}
