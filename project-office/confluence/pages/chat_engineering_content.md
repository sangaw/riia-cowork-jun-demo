# RITA Chat Feature — Engineering Reference

**Parent section:** Engineering  

| | |
|---|---|
| **Router** | `src/rita/api/v1/workflow/chat.py` |
| **Classifier** | `src/rita/core/classifier.py` |
| **Monitor** | `src/rita/core/chat_monitor.py` |
| **Frontend** | `dashboard/js/rita/chat.js` |
| **API prefix** | `/api/v1/chat` |
| **Auth** | JWT required on all endpoints |

---

## API Endpoints

### POST /api/v1/chat/warmup

Pre-warms the SentenceTransformer classifier and computes market-driven chip suggestions for the current instrument. Called by the dashboard when the user opens the chat panel. Idempotent — safe to call multiple times.

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `instrument` | string (optional) | active instrument | Override the instrument for chip generation |

**Response:**

```json
{
  "status":     "ready",
  "instrument": "NIFTY",
  "chips": [
    { "label": "RSI at 58 — what does it mean?", "query": "What is the RSI reading today?" },
    ...
  ],
  "alerts": [
    { "severity": "warn", "message": "Volatility near historic lows..." }
  ]
}
```

If chip generation fails (e.g. no CSV data), `chips` is `null` and `status` is still `"ready"` — the warmup never blocks the UI.

---

### POST /api/v1/chat

Classify a free-text query and return a deterministic, data-driven response.

**Request body:**

```json
{
  "query":              "Is the market overbought?",
  "instrument":         "NIFTY",
  "portfolio_inr":      1000000,
  "target_return_pct":  15.0,
  "time_horizon_days":  365
}
```

**Response:**

```json
{
  "instrument":     "NIFTY",
  "intent":         "market_overbought_oversold",
  "handler":        "market_sentiment",
  "confidence":     0.7231,
  "low_confidence": false,
  "response":       "RSI is currently 58.4, which sits in neutral territory ...",
  "latency_ms":     42.3
}
```

**Error responses:**

| HTTP | Condition |
|---|---|
| 503 | CSV data not found for the requested instrument |
| 500 | Classification or dispatch error |

**low_confidence behaviour:** When `confidence < 0.42`, the response still returns HTTP 200 with `low_confidence: true`. The response text acknowledges the ambiguity and suggests a rephrased question. The frontend renders a muted style for low-confidence replies.

---

### GET /api/v1/chat/monitor

Returns KPIs and the recent query log from the chat monitor CSV. Used by the Ops dashboard chat monitoring panel.

**Response shape:**

```json
{
  "summary": {
    "total_queries":        142,
    "success_rate_pct":     94.4,
    "avg_latency_ms":       38.1,
    "low_confidence_pct":   5.6
  },
  "recent": [
    {
      "timestamp":    "2026-04-26T10:14:03",
      "query":        "Is the market overbought?",
      "intent":       "market_overbought_oversold",
      "confidence":   0.72,
      "latency_ms":   41.0,
      "status":       "success"
    }
  ],
  "intents": {
    "market_overbought_oversold": 38,
    "strategy_recommendation":    24
  }
}
```

---

## Classifier — Implementation Details

### Model loading

```python
# classifier.py
_model: SentenceTransformer | None = None

def _build_seed_index() -> None:
    global _model
    if _model is not None:
        return                        # already loaded — no-op
    _model = SentenceTransformer(settings.chat.embed_model_path)
    # embed all 20 x N seed phrases once; stored as numpy arrays
```

The model path is read from `settings.chat.embed_model_path` (config YAML). Default: `data/models/all-MiniLM-L6-v2`.

### Intent matching

```python
def classify(query: str) -> ClassifyResult:
    query_vec = _model.encode([query])                 # 384-dim embedding
    scores = cosine_similarity(query_vec, seed_vecs)   # shape: (1, N)
    best_idx = scores.argmax()
    confidence = scores[0, best_idx]
    intent = INTENTS[seed_intent_map[best_idx]]
    return ClassifyResult(
        intent=intent,
        confidence=float(confidence),
        low_confidence=confidence < 0.42,
    )
```

---

## Data Cache — _market_signals_cache

```python
# chat.py
_market_signals_cache: dict[str, dict[str, Any]] = {}
# key = instrument id ("NIFTY", "NVIDIA", ...)
# value = { "df": DataFrame, "mtime_key": (mtime_primary, mtime_manual) }

def _get_df(instrument: str) -> DataFrame:
    mtime_key = (os.path.getmtime(primary_path), mtime_manual)
    if cached and cached["mtime_key"] == mtime_key:
        return cached["df"]           # cache hit
    df = calculate_indicators(load_nifty_csv(primary_path))
    _market_signals_cache[instrument] = {"df": df, "mtime_key": mtime_key}
    return df
```

The cache is process-scoped (in-memory). A server restart clears it. The first request after restart reloads the CSV.

---

## Chat Monitor — Logging

File: `src/rita/core/chat_monitor.py`

Every query is appended to a CSV log. Fields written per row:

| Field | Type | Description |
|---|---|---|
| `timestamp` | ISO datetime | UTC time of the request |
| `query_text` | string | Raw user query (truncated to 500 chars) |
| `intent_name` | string | Matched intent identifier |
| `handler` | string | Handler function dispatched |
| `confidence` | float | Cosine similarity score (0–1) |
| `low_confidence` | bool | True if confidence < 0.42 |
| `latency_ms` | float | End-to-end response time |
| `response_preview` | string | First 200 chars of the response |
| `status` | string | `success` or `low_confidence` |

---

## Frontend Integration — chat.js

File: `dashboard/js/rita/chat.js`

| Function | Triggered by | Description |
|---|---|---|
| `sendChatMsg()` | Enter key / Send button | Reads `#chat-input`, calls `POST /api/v1/chat`, appends message to thread |
| `useChip(query)` | Chip button click | Pre-fills `#chat-input` and submits via `sendChatMsg()` |
| `clearChat()` | Clear button | Empties the chat thread DOM |

Warmup is called automatically when the chat section is first navigated to (registered in `main.js` section loader). Chips and alerts returned by warmup are rendered into the chip strip and alert banner above the input box.

**Low-confidence rendering:** Responses with `low_confidence: true` are rendered with a muted text style and a "Low confidence" label to inform the user that the query did not match a known intent clearly.

---

## Configuration

| Config key | Default | Description |
|---|---|---|
| `chat.embed_model_path` | `data/models/all-MiniLM-L6-v2` | Local path to the SentenceTransformer model directory |
| `chat.confidence_threshold` | `0.42` | Minimum cosine similarity to trust the top intent |

---

## Adding a New Intent

1. Add an entry to the `INTENTS` list in `classifier.py` with a name, handler, and seed phrases
2. If the handler is new, implement it in `classifier.py` under `dispatch()`
3. Rebuild the seed index by calling `_build_seed_index()` (happens automatically on next warmup)
4. Add a unit test in `tests/unit/test_classifier.py` verifying the new intent is matched by at least 3 representative queries
5. Update `Specs/Spec_Chat_Feature.md` to reflect the new intent count and handler mapping
