"""RITA Core — Technical Analyzer

Calculates technical indicators (RSI, MACD, Bollinger Bands, ATR, EMA)
using the `ta` library on an OHLCV DataFrame.

Ported from: poc/rita-cowork-demo/src/rita/core/technical_analyzer.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import ta


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicator columns to an OHLCV DataFrame.

    Expects columns: Open, High, Low, Close, Volume (standard RITA names).

    Adds:
        rsi_14        — RSI (14-period)
        macd          — MACD line
        macd_signal   — MACD signal line
        macd_hist     — MACD histogram
        bb_upper      — Bollinger upper band
        bb_mid        — Bollinger middle band
        bb_lower      — Bollinger lower band
        bb_pct_b      — %B position (0=lower band, 1=upper band)
        atr_14        — ATR (14-period)
        ema_5         — 5-day EMA
        ema_13        — 13-day EMA
        ema_26        — 26-day EMA
        ema_50        — 50-day EMA
        ema_200       — 200-day EMA
        trend_score   — normalized slope of ema_50, clipped to [-1, +1]
        ema_ratio     — ema_26 / ema_50 clipped to [0.5, 1.5] (regime signal)
        daily_return  — daily close-to-close return
    """
    out = df.copy()

    # RSI
    out["rsi_14"] = ta.momentum.RSIIndicator(close=out["Close"], window=14).rsi()

    # MACD
    macd_ind = ta.trend.MACD(close=out["Close"], window_fast=12, window_slow=26, window_sign=9)
    out["macd"]       = macd_ind.macd()
    out["macd_signal"] = macd_ind.macd_signal()
    out["macd_hist"]  = macd_ind.macd_diff()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=out["Close"], window=20, window_dev=2)
    out["bb_upper"] = bb.bollinger_hband()
    out["bb_mid"]   = bb.bollinger_mavg()
    out["bb_lower"] = bb.bollinger_lband()
    out["bb_pct_b"] = bb.bollinger_pband()

    # ATR
    out["atr_14"] = ta.volatility.AverageTrueRange(
        high=out["High"], low=out["Low"], close=out["Close"], window=14
    ).average_true_range()

    # EMAs
    out["ema_5"]   = ta.trend.EMAIndicator(close=out["Close"], window=5).ema_indicator()
    out["ema_13"]  = ta.trend.EMAIndicator(close=out["Close"], window=13).ema_indicator()
    out["ema_26"]  = ta.trend.EMAIndicator(close=out["Close"], window=26).ema_indicator()
    out["ema_50"]  = ta.trend.EMAIndicator(close=out["Close"], window=50).ema_indicator()
    out["ema_200"] = ta.trend.EMAIndicator(close=out["Close"], window=200).ema_indicator()

    # Trend score: normalized slope of ema_50 over 20-day rolling window
    def _rolling_trend_score(series: pd.Series, window: int = 20) -> pd.Series:
        slopes = []
        for i in range(len(series)):
            if i < window - 1:
                slopes.append(np.nan)
            else:
                segment = series.iloc[i - window + 1: i + 1].values
                x = np.arange(window, dtype=float)
                slope = np.polyfit(x, segment, 1)[0]
                slopes.append(slope / series.iloc[i])
        return pd.Series(slopes, index=series.index)

    raw_trend = _rolling_trend_score(out["ema_50"].dropna())
    out["trend_score"] = raw_trend.reindex(out.index)
    out["trend_score"] = out["trend_score"].clip(-0.01, 0.01) / 0.01

    # EMA ratio — regime context feature (EMA-26 / EMA-50)
    out["ema_ratio"] = (out["ema_26"] / out["ema_50"]).clip(0.5, 1.5)

    # Daily return
    out["daily_return"] = out["Close"].pct_change()

    return out
