"""
RITA Workflow — Chat Router

POST /api/v1/chat/warmup   Pre-warms the local SentenceTransformer classifier.
POST /api/v1/chat          Classify query + dispatch deterministic OHLCV handler.
GET  /api/v1/chat/monitor  Chat KPIs and recent query log.

Fully local — no Claude/Anthropic API call at runtime.
Model path is read from settings.chat.embed_model_path.
"""
from __future__ import annotations

import os
import time as _time
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rita.config import get_settings

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

# ── Market signals cache (df + indicators; recomputed only when CSV mtime changes) ──
_market_signals_cache: dict[str, Any] = {"df": None, "csv_mtime": -1.0}


def _get_active_csv() -> str:
    """Return path to the best available Nifty 50 OHLCV CSV."""
    settings = get_settings()
    primary = Path(settings.data.raw_dir) / "NIFTY" / "merged.csv"
    if primary.exists():
        return str(primary)
    manual = Path(settings.data.input_dir) / "DAILY-DATA" / "nifty_manual.csv"
    if manual.exists():
        return str(manual)
    raise FileNotFoundError(
        f"No Nifty 50 CSV found at {primary} or {manual}. "
        "Place the OHLCV data file before using chat."
    )


def _get_df():
    """
    Load and cache the indicators DataFrame.

    Merges the historical merged.csv (ends Dec-2025) with the manual daily
    extension file (2026 data) so chat always has up-to-date OHLCV.
    Recomputes only when either file's mtime changes.
    """
    import pandas as pd
    from rita.core.data_loader import load_nifty_csv
    from rita.core.technical_analyzer import calculate_indicators

    settings = get_settings()
    primary_path = _get_active_csv()
    manual_path  = Path(settings.data.input_dir) / "DAILY-DATA" / "nifty_manual.csv"

    mtime_primary = os.path.getmtime(primary_path)
    mtime_manual  = os.path.getmtime(str(manual_path)) if manual_path.exists() else 0.0
    cache_key = (mtime_primary, mtime_manual)

    if _market_signals_cache["df"] is not None and _market_signals_cache["csv_mtime"] == cache_key:
        return _market_signals_cache["df"]

    raw = load_nifty_csv(primary_path)
    if manual_path.exists():
        manual = load_nifty_csv(str(manual_path))
        raw = pd.concat([raw, manual])
        raw = raw[~raw.index.duplicated(keep="last")].sort_index()

    _market_signals_cache["df"]       = calculate_indicators(raw)
    _market_signals_cache["csv_mtime"] = cache_key
    log.info("chat.csv_reloaded", primary=primary_path, rows=len(_market_signals_cache["df"]),
             latest=str(_market_signals_cache["df"].index[-1].date()))
    return _market_signals_cache["df"]


# ── Request schema ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    portfolio_inr: float = 1_000_000
    target_return_pct: float | None = None
    time_horizon_days: int | None = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

def _build_alerts(summary: dict, scored: dict) -> list[dict]:
    """
    Return up to 2 proactive market alerts for extreme conditions.
    Each alert has a severity ('warn'|'danger') and a message string.
    """
    alerts: list[dict] = []
    rsi     = summary["rsi_14"]
    atr_pct = summary["atr_percentile"]
    trend   = summary["trend"]
    total   = scored["total_score"]
    bb_pos  = summary["bb_position"]

    if rsi > 78:
        alerts.append({"severity": "danger", "message": f"RSI is {rsi:.0f} — strongly overbought. Momentum reversal risk is elevated."})
    elif rsi < 22:
        alerts.append({"severity": "warn", "message": f"RSI is {rsi:.0f} — deeply oversold. Potential bounce, but trend may persist."})

    if atr_pct > 0.90:
        alerts.append({"severity": "danger", "message": f"Volatility at {atr_pct*100:.0f}th percentile — unusually large daily swings. Stress-test your portfolio."})
    elif atr_pct < 0.08:
        alerts.append({"severity": "warn", "message": "Volatility is near historic lows. Low ATR periods often precede sharp moves — stay alert."})

    if not alerts and trend == "downtrend" and total <= -3:
        alerts.append({"severity": "danger", "message": f"Bearish consensus — score {total:+d}/6 with confirmed downtrend. RITA may recommend HOLD."})

    if not alerts and rsi > 65 and bb_pos == "near_upper_band":
        alerts.append({"severity": "warn", "message": "Overbought RSI with price at upper Bollinger Band — reversal signal. Ask RITA to explain its recommendation."})

    return alerts[:2]


def _build_dynamic_chips(summary: dict, scored: dict) -> list[dict]:
    """
    Return up to 10 suggested chat questions tailored to the current market state.
    Each chip has a short display label and the full query string to send.
    """
    chips: list[dict] = []
    rsi      = summary["rsi_14"]
    trend    = summary["trend"]
    atr_pct  = summary["atr_percentile"]
    sentiment = scored["overall_sentiment"]
    bb_pos   = summary["bb_position"]

    # ── RSI signal ────────────────────────────────────────────────────────────
    if rsi > 70:
        chips.append({"label": f"Nifty overbought? (RSI {rsi:.0f})", "query": "Is the market overbought or oversold?"})
    elif rsi < 30:
        chips.append({"label": f"Nifty oversold? (RSI {rsi:.0f})", "query": "Is the market overbought or oversold?"})
    else:
        chips.append({"label": f"RSI at {rsi:.0f} — what does it mean?", "query": "What is the RSI reading today?"})

    # ── Volatility signal ─────────────────────────────────────────────────────
    if atr_pct > 0.85:
        chips.append({"label": "Volatility is very high — stress test my portfolio", "query": "How volatile is Nifty right now?"})
    elif atr_pct < 0.20:
        chips.append({"label": "Volatility is very low — good time to enter?", "query": "What is Nifty volatility today?"})
    else:
        chips.append({"label": "Current volatility level?", "query": "What is Nifty volatility today?"})

    # ── Trend signal ──────────────────────────────────────────────────────────
    if trend == "downtrend":
        chips.append({"label": "Nifty in downtrend — what if it falls 20%?", "query": "What if market crashes 20 percent?"})
        chips.append({"label": "Safe strategy in a downtrend?", "query": "Safe investment approach for Nifty"})
    elif trend == "uptrend":
        chips.append({"label": "Uptrend in play — can I go aggressive?", "query": "Aggressive nifty investment strategy"})
        chips.append({"label": "What if Nifty rallies another 10%?", "query": "What if Nifty rises 10 percent?"})
    else:
        chips.append({"label": "Market is sideways — what happens to my portfolio?", "query": "Sideways market scenario Nifty"})

    # ── Sentiment / Bollinger ─────────────────────────────────────────────────
    if sentiment in ("BEARISH", "CAUTIOUSLY_BEARISH"):
        chips.append({"label": "Should I reduce my Nifty allocation?", "query": "What allocation should I have in Nifty?"})
        chips.append({"label": "Protect capital — conservative strategy?", "query": "Conservative allocation for Nifty"})
    elif sentiment in ("BULLISH", "CAUTIOUSLY_BULLISH"):
        chips.append({"label": "Can I invest in Nifty now?", "query": "Can I invest in Nifty now?"})
        chips.append({"label": "What returns can I expect this year?", "query": "Annual return from Nifty"})
    else:
        chips.append({"label": "Can I invest in Nifty now?", "query": "Can I invest in Nifty now?"})

    if bb_pos == "near_upper_band":
        chips.append({"label": "Price at upper Bollinger Band — reversal risk?", "query": "Is the market overbought or oversold?"})
    elif bb_pos == "near_lower_band":
        chips.append({"label": "Price at lower Bollinger Band — buying opportunity?", "query": "Is this a good entry point for Nifty?"})

    # ── Always-useful staples ─────────────────────────────────────────────────
    chips.append({"label": "Overall market sentiment today?", "query": "What is the current market sentiment?"})
    chips.append({"label": "3-year return outlook?", "query": "3 year Nifty return estimate"})
    chips.append({"label": "How has RITA performed historically?", "query": "How has RITA model performed historically?"})

    return chips[:10]


@router.post("/warmup", status_code=202)
def chat_warmup() -> dict:
    """
    Pre-warm the intent classifier (loads local SentenceTransformer + builds seed index).
    Also computes market-driven suggested chips from live OHLCV data.
    Called by the dashboard when the user first opens the Market Analysis section.
    Idempotent — safe to call multiple times (chips are always recomputed).
    """
    from rita.core.classifier import _build_seed_index
    from rita.core.technical_analyzer import get_market_summary, get_sentiment_score

    _build_seed_index()

    chips = None
    try:
        df = _get_df()
        summary = get_market_summary(df)
        scored  = get_sentiment_score(summary)
        chips   = _build_dynamic_chips(summary, scored)
        alerts  = _build_alerts(summary, scored)
        log.info("chat.warmed_up", sentiment=scored["overall_sentiment"], chips=len(chips), alerts=len(alerts))
    except Exception as exc:
        log.warning("chat.warmup_chips_failed", error=str(exc))

    return {"status": "ready", "chips": chips, "alerts": alerts}


@router.post("")
def chat(req: ChatRequest) -> dict:
    """
    Classify a free-text investment query and return a deterministic OHLCV-driven response.

    Uses all-MiniLM-L6-v2 (local, offline) cosine similarity to route to one of
    20 fixed investment scenarios, then runs the matching core handler against
    live Nifty 50 data.
    """
    from rita.core.classifier import classify, dispatch
    from rita.core.chat_monitor import log_query as _log_query

    settings = get_settings()
    t0 = _time.perf_counter()

    try:
        df = _get_df()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load market data: {exc}") from exc

    try:
        result = classify(req.query)
        response_text = dispatch(
            result, df,
            portfolio_inr=req.portfolio_inr,
            output_dir=settings.data.output_dir,
            target_return_pct=req.target_return_pct,
            time_horizon_days=req.time_horizon_days,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification error: {exc}") from exc

    latency_ms = (_time.perf_counter() - t0) * 1000
    status = "low_confidence" if result.low_confidence else "success"

    _log_query(
        query_text=req.query,
        intent_name=result.intent.name,
        handler=result.intent.handler,
        confidence=result.confidence,
        low_confidence=result.low_confidence,
        latency_ms=latency_ms,
        response_preview=response_text[:200],
        status=status,
    )

    log.info(
        "chat.query",
        intent=result.intent.name,
        confidence=round(result.confidence, 3),
        low_confidence=result.low_confidence,
        latency_ms=round(latency_ms, 1),
    )

    return {
        "intent":         result.intent.name,
        "handler":        result.intent.handler,
        "confidence":     round(result.confidence, 4),
        "low_confidence": result.low_confidence,
        "response":       response_text,
        "latency_ms":     round(latency_ms, 1),
    }


@router.get("/monitor")
def chat_monitor_summary() -> dict:
    """KPIs and recent queries from the chat monitor CSV."""
    from rita.core.chat_monitor import get_summary, get_recent_queries, get_intent_distribution
    return {
        "summary": get_summary(),
        "recent":  get_recent_queries(20),
        "intents": get_intent_distribution(),
    }
