---
description: Add a new intent to the RITA chat classifier — seed phrases, handler, dispatch wiring
---

You are an Engineer agent adding a new chat intent to the RITA classifier.

**Task:** $ARGUMENTS

---

## Architecture (read once — do not re-read source files)

The chat pipeline is **fully local** — no Claude/Anthropic API calls at runtime.

```
User query → POST /api/v1/chat → classifier.py: classify_intent()
  → sentence-transformers/all-MiniLM-L6-v2 (lazy-loaded, cached)
  → cosine similarity against seed phrase embeddings
  → score < 0.42 → low_confidence fallback
  → dispatch(intent, context) → handler → structured response dict
```

**Key files:**

| File | Contains |
|---|---|
| `src/rita/core/classifier.py` | `INTENTS` dict, `classify_intent()`, `dispatch()`, all handlers |
| `src/rita/api/v1/workflow/chat.py` | Route handlers for `POST /api/v1/chat` and `POST /api/v1/chat/warmup` |
| `dashboard/js/rita/chat.js` | `sendChatMsg()`, `useChip()`, chip array |

---

## Existing Intents — Do Not Duplicate (20 total)

| Intent key | Trigger phrases (examples) |
|---|---|
| `market_sentiment` | "What is the market sentiment?", "Is market bullish?" |
| `trend_direction` | "EMA trend direction", "Which way is Nifty trending?" |
| `rsi_reading` | "What is the RSI?", "Is Nifty overbought?" |
| `volatility_check` | "How volatile is Nifty?", "Current ATR" |
| `invest_now` | "Can I invest in Nifty now?", "Should I buy?" |
| `allocation_level` | "What allocation should I have?", "How much to invest?" |
| `conservative_strategy` | "Safe investment approach", "Low risk Nifty strategy" |
| `aggressive_strategy` | "High risk strategy", "Maximum growth allocation" |
| `stress_crash_10` | "What if Nifty falls 10 percent?" |
| `stress_crash_20` | "What if Nifty crashes 20 percent?" |
| `stress_rally_10` | "What if Nifty rallies 10 percent?" |
| `stress_flat` | "Sideways market scenario" |
| `backtest_performance` | "How has RITA performed?", "Show historical performance" |
| `portfolio_compare` | "Compare conservative vs aggressive portfolios" |
| `explain_decision` | "Why did RITA recommend this?", "What signals led to this?" |
| `return_1m` / `return_3m` / `return_6m` | "What returns can I expect in 1/3/6 months?" |
| `return_1y` / `return_3y` / `return_5y` | "What returns in 1/3/5 years?" |

---

## Rule 1: Three Changes in `classifier.py`

### 1 — Add seed phrases to `INTENTS` dict
```python
INTENTS = {
    # ...existing...
    "my_new_intent": [
        "seed phrase one",
        "seed phrase two",
        "seed phrase three",
        "alternate wording",
        "question variation here",
    ],
}
```
- Write how a real user would type it — colloquial, not technical
- Minimum 3 phrases, ideally 5–8; include question and statement forms
- Threshold is 0.42 — too-generic phrases cause false positives

### 2 — Add a handler function
```python
def _handle_my_new_intent(context: dict) -> dict:
    df = context["df"]
    # deterministic calculation only
    return {
        "intent": "my_new_intent",
        "response": "Human-readable answer here",
        "data": {},
        "confidence": context.get("confidence", 0.0),
    }
```
- **Deterministic only** — no LLM calls, no external APIs
- Use `context["df"]` (OHLCV DataFrame) for calculations
- Never raise — return a fallback response dict on error

### 3 — Wire into `dispatch()`
```python
def dispatch(intent: str, context: dict) -> dict:
    handlers = {
        # ...existing...
        "my_new_intent": _handle_my_new_intent,
    }
    handler = handlers.get(intent)
    if handler is None:
        return _handle_low_confidence(context)
    return handler(context)
```

---

## Rule 2: Chat Chips (optional)

Only add a chip if the intent is commonly used:
```js
// dashboard/js/rita/chat.js — CHIPS array
{ label: "My Intent", query: "Seed phrase that triggers my_new_intent" },
```

---

## API Contract (do not change)

```
POST /api/v1/chat
Body:     { "query": "user's message", "instrument": "NIFTY" }
Response: { "intent": "...", "response": "...", "confidence": 0.87, "data": {} }

POST /api/v1/chat/warmup
Body: {}  →  Response: { "status": "ready" }
```

Chat logging goes through the DB via `AlertsRepository` — do not remove it.

---

## Step-by-Step

1. Read `src/rita/core/classifier.py` (targeted slice — find `INTENTS` dict and `dispatch()`)
2. Confirm new intent doesn't overlap with the 20 existing ones above
3. Add seed phrases to `INTENTS`
4. Write handler function `_handle_my_new_intent(context)`
5. Wire into `dispatch()`
6. Add chip to `chat.js` if commonly used
7. Update `Specs/Spec_Chat_Feature.md` — add row to intents table

---

## Files to Touch

| File | Action |
|---|---|
| `src/rita/core/classifier.py` | Edit — `INTENTS`, handler fn, `dispatch()` |
| `dashboard/js/rita/chat.js` | Edit — add chip (if needed) |
| `Specs/Spec_Chat_Feature.md` | Edit — add row to intents table |

---

## Definition of Done

- [ ] Seed phrases added (minimum 3, ideally 5–8)
- [ ] Handler returns `intent`, `response`, and `confidence` fields
- [ ] Intent wired into `dispatch()` — no `None` fallback for the new key
- [ ] Handler is deterministic — no LLM calls, no external APIs
- [ ] Chat chip added if commonly used
- [ ] `Specs/Spec_Chat_Feature.md` intent table updated
