# RITA Chat Feature — Architecture & Design

**Parent section:** Architecture and Design  
**Status:** Production | **Date:** 2026-04-26 | **Component:** Chat Pipeline (Workflow Layer)  
**Key constraint:** Fully local — zero external API calls at runtime

---

## Overview

The RITA Chat feature allows users to query the system in natural language and receive deterministic, data-driven responses about market conditions, portfolio performance, and investment scenarios. It is **fully local** — no Claude, OpenAI, or any other LLM API is called at runtime. Every response is computed from live OHLCV data and pre-calculated technical indicators.

---

## Three-Layer Pipeline

### Layer 1 — Intent Classification

File: `src/rita/core/classifier.py`

- Uses **sentence-transformers/all-MiniLM-L6-v2** — a 22MB local embedding model that runs entirely offline
- 20 fixed investment intents, each pre-seeded with representative phrases
- On startup, seed phrases are embedded once and cached in memory (`_model` global)
- Each user query is embedded and matched against all seeds via **cosine similarity**
- Confidence threshold: **0.42** — queries below this score route to a low-confidence fallback response
- Warmup endpoint (`POST /api/v1/chat/warmup`) pre-loads the model before the user types their first query

### Layer 2 — Deterministic Data Dispatch

File: `src/rita/core/classifier.py` — `dispatch()`

- Once an intent is classified, a matching handler runs against **live OHLCV data** (loaded from CSV, cached by mtime)
- Handlers cover six data domains:

| Handler | What it computes |
|---|---|
| `market_sentiment` | RSI, MACD, Bollinger, EMA trend — composite market score |
| `strategy_recommendation` | Allocation advice based on regime + feasibility |
| `return_estimates` | 1yr / 3yr / 5yr projections from historical CAGR |
| `stress_scenarios` | Portfolio impact of -10%, -20%, -30%, +20% market moves |
| `performance_feedback` | RITA vs benchmark — Sharpe, MDD, CAGR from latest backtest |
| `portfolio_comparison` | RITA vs buy-and-hold normalised return comparison |

All handlers are **deterministic** — the same market state always produces the same response. No stochastic generation.

### Layer 3 — Response Caching

File: `src/rita/api/v1/workflow/chat.py` — `_market_signals_cache`

- The market signals DataFrame is cached per instrument, keyed by the CSV file's `mtime`
- Cache is invalidated automatically when the source CSV is updated
- A manual supplement file (`data/input/DAILY-DATA/{instrument}_manual.csv`) is appended when present, allowing intraday updates without a full CSV rebuild
- This is **data caching**, not LLM response caching — the handler always runs fresh calculations

---

## Data Flow

```
User types query
      |
      v
POST /api/v1/chat/warmup  (called once when chat panel opens)
  -> _build_seed_index()  loads all-MiniLM-L6-v2, embeds 20 seed phrases
  -> get_market_summary() computes current indicators
  -> returns dynamic chip suggestions + proactive alerts

User submits query
      |
      v
POST /api/v1/chat
  -> classify(query)     cosine similarity -> best intent (confidence score)
  -> dispatch(intent)    runs deterministic handler against cached OHLCV df
  -> log_query()         appends to chat_monitor.csv (query, intent, latency)
  -> returns { intent, confidence, response, latency_ms }
```

---

## Intent Taxonomy — 20 Fixed Intents

| Domain | Intent examples | Handler |
|---|---|---|
| Market conditions | Is the market overbought? What is the RSI today? Market sentiment? | `market_sentiment` |
| Volatility | How volatile is the market? Current ATR? High volatility warning? | `market_sentiment` |
| Trend analysis | Is there an uptrend? EMA crossover signal? Market direction? | `market_sentiment` |
| Investment strategy | What allocation should I have? Safe investment approach? Aggressive strategy? | `strategy_recommendation` |
| Return estimates | 3-year return estimate? Annual return? What returns can I expect? | `return_estimates` |
| Stress scenarios | What if market crashes 20%? What if it rallies 10%? Downside risk? | `stress_scenarios` |
| RITA performance | How has RITA performed? Sharpe ratio? Historical backtest results? | `performance_feedback` |
| Portfolio comparison | RITA vs buy-and-hold? How does RITA compare to the index? | `portfolio_comparison` |

---

## Dynamic Chat Chips & Proactive Alerts

On warmup, the server computes the current market state and returns:

- **Up to 10 dynamic chips** — suggested questions tailored to RSI, trend, volatility, and sentiment conditions. E.g. if RSI > 70, the chip reads "Market overbought? (RSI 74)"
- **Up to 2 proactive alerts** — extreme condition warnings (RSI > 78, ATR percentile > 90th, confirmed downtrend). Shown as inline alert banners in the chat UI.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Local embedding model (all-MiniLM-L6-v2) instead of an LLM API | Zero latency, zero token cost, fully offline. Adequate for intent classification with 20 fixed intents. |
| 20 fixed intents rather than open-ended generation | Deterministic, testable, auditable. Every response is traceable to a specific calculation. No hallucination risk. |
| Confidence threshold 0.42 for low-confidence fallback | Tuned empirically. Below this the cosine similarity is too low to trust the top intent. Fallback response guides user to a supported question. |
| Instrument-scoped OHLCV cache keyed by mtime | Avoids re-loading a large CSV on every request. Invalidates automatically when the file changes — no TTL needed. |
| Warmup endpoint called by the dashboard, not on API startup | The embedding model takes ~2s to load. Calling it on first chat open (not on server start) keeps startup fast and avoids loading it if chat is never used. |

---

## Instrument Support

The chat feature supports all instruments in the RITA universe: **NIFTY, BANKNIFTY, ASML, NVIDIA**. The active instrument is resolved from:

1. `req.instrument` field in the POST body (explicit override)
2. `_get_active_instrument_id(db)` — reads the `active_instrument_id` config override from the database (set via the instrument selector in the dashboard)
3. Default: **NIFTY**
