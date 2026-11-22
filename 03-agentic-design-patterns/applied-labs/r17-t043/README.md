# Applied Lab: Routing Agent with Offline Service Adapter (R17-T043)

## Overview & Lesson Alignment

In **Lesson 03: Agentic Design Patterns**, routing is an essential structural pattern where incoming requests are dynamically evaluated and directed to specialized agent handlers. Rather than relying on a monolithic agent to perform every task, a **Routing Agent** classifies customer intent and routes the query to dedicated downstream agents (e.g., customer support, calculation engine, or fallback assistance).

This applied lab implements a robust, deterministic **Intent Router** with:
1. **Named Handler Dispatch**: Distinct routing for help/support, numerical calculation, and fallback queries.
2. **Deterministic Ambiguity Resolution**: Resolves queries matching multiple candidate intents using a documented priority hierarchy.
3. **Auditable Decision Logging**: Records structured, immutable audit traces for every routing event.
4. **Offline Service Adapter**: Decouples classification behind an abstract callable adapter protocol (`ClassifierAdapterProtocol`) with an in-memory mock adapter (`DeterministicMockClassifierAdapter`).
5. **Real-Service Simulation Boundary**: Explicitly documents behaviors present in production cloud LLMs that are not simulated by the offline mock.

> [!NOTE]
> **Simulation Disclaimer**: This applied lab is a zero-dependency educational module implemented exclusively with the Python 3 standard library (`dataclasses`, `typing`, `unittest`). The mock adapter operates in-memory using deterministic pattern matching. No external cloud credentials, API keys, GPUs, or trained model downloads are required.

---

## Core Routing Contract & Handlers

Incoming requests are classified and routed to three named handlers:

| Intent Category | Primary Keywords / Triggers | Target Handler | Handler Role |
| :--- | :--- | :--- | :--- |
| **`help` / `support`** | `help`, `support`, `assist`, `trouble`, `issue`, `human`, `agent` | `support` | Connects users to customer assistance and troubleshooting. |
| **`calculate` / `calculator`** | `calculate`, `calc`, `math`, `sum`, `multiply`, arithmetic expressions (`\d+ [\+\-\*\/] \d+`) | `calculator` | Evaluates arithmetic and numerical operations. |
| **`unknown`** | Unrecognized queries with no matching intent signals | `fallback` | Provides guidance on available agent capabilities and options. |

---

## Ambiguity Resolution & Priority Hierarchy

In real-world multi-agent systems, user inputs frequently trigger multiple intent signals (e.g., *"Help me calculate my monthly billing tier"*). 

### Documented Priority Rule
```text
support > calculator > fallback
```

When multiple candidate intents are detected:
1. The router evaluates candidate intents against `PRIORITY_ORDER = ["support", "calculator", "fallback"]`.
2. The candidate with the highest priority rank is selected.
3. The routing decision sets `priority_applied = True`.
4. The decision log explicitly documents the ambiguity and the applied priority ranking.

---

## Auditable Decision Log Schema

Every invocation of `router.route()` records an immutable audit record:

```python
@dataclass
class DecisionLogRecord:
    decision_id: int              # Incremental unique identifier
    timestamp_iso: str            # ISO-8601 UTC timestamp
    raw_query: str                # Original user input query
    detected_intents: List[str]   # All detected intent signals
    selected_handler: str         # Handler selected for dispatch
    priority_applied: bool        # True if ambiguity tie-breaking was applied
    decision_reason: str          # Human- and machine-readable explanation
    confidence: float             # Confidence score of the classification
    response_summary: str         # Summary of the handler response
```

---

## Offline Service Adapter Architecture

To decouple the router from specific LLM vendors (e.g., Microsoft Foundry, OpenAI, Anthropic), classification is abstracted behind an adapter protocol:

```python
@runtime_checkable
class ClassifierAdapterProtocol(Protocol):
    def __call__(self, query: str) -> ClassificationResult: ...
    def classify(self, query: str) -> ClassificationResult: ...
```

The router accepts any compliant callable or adapter object. Production systems can swap `DeterministicMockClassifierAdapter` with an Azure OpenAI / Microsoft Foundry hosted model adapter without modifying the core routing logic.

---

## Unsimulated Real-Service Behaviors

The local mock adapter intentionally does **not** simulate the following production cloud service characteristics:

| Unsimulated Behavior | Mock Adapter Characteristic | Real Cloud / LLM Behavior |
| :--- | :--- | :--- |
| **Network Latency & Jitter** | In-memory execution ($< 1$ ms) | Variable latency (200–2000 ms) due to network hops, TLS negotiation, and queueing. |
| **Token Rate Limits (TPM/RPM)** | Unlimited local executions | HTTP 429 errors when exceeding token-per-minute or request-per-minute quotas. |
| **Probabilistic LLM Drift** | Deterministic keyword/regex matching | Stochastic output variation with non-zero temperature, semantic drift, and phrasing sensitivity. |
| **Context Window Limits** | Arbitrary string lengths accepted | Fixed context windows (e.g., 8k/32k/128k tokens); payload truncation on excess size. |
| **Authentication & Token Expiry** | No authentication required | Entra ID / API key verification with token expiration, credential rotation, and IAM scopes. |
| **Service Outages & Failures** | Zero infrastructure failures | Transient HTTP 5xx errors, timeouts, connection drops, and service maintenance windows. |

---

## Quick Invocation & Testing

```bash
# Run demonstration script and view routing audit log
python3 03-agentic-design-patterns/applied-labs/r17-t043/example.py

# Run automated unit test suite
python3 -m unittest discover -s 03-agentic-design-patterns/applied-labs/r17-t043 -p "test_*.py" -v
```
