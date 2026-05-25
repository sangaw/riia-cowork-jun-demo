"""
Trading Strategies Performance Analysis — ASML 2025
Replicates the 7-panel Strategy Checks chart for ASML data.

Run from repo root:
    python project-office/scripts/strategy_checks_asml.py
Output: ~/Desktop/Strategy Checks - ASML.png
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

DATA_PATH = (
    Path(__file__).parent.parent.parent
    / "riia-jun-release/data/raw/ASML/asml_2001-2026.csv"
)
OUTPUT_PATH = Path.home() / "Desktop/Strategy Checks - ASML.png"
INITIAL_CAPITAL = 10_000.0
YEAR = 2025


# ── Load & prepare ────────────────────────────────────────────────────────────

df_all = pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
df_2025 = df_all[df_all["date"].dt.year == YEAR].copy().reset_index(drop=True)
idx_offset = df_all[df_all["date"] == df_2025["date"].iloc[0]].index[0]


# ── Indicators ────────────────────────────────────────────────────────────────

def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ── Metrics ───────────────────────────────────────────────────────────────────

def sharpe_ratio(equity: pd.Series) -> float:
    daily = equity.pct_change().dropna()
    return (daily.mean() / daily.std()) * np.sqrt(252) if daily.std() > 0 else 0.0


def max_drawdown_pct(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak * 100
    return abs(dd.min())


# ── Strategies ────────────────────────────────────────────────────────────────

def run_buy_hold(df: pd.DataFrame):
    entry = df["Close"].iloc[0]
    shares = INITIAL_CAPITAL / entry
    equity = shares * df["Close"]
    exit_price = df["Close"].iloc[-1]
    trades = [{"entry": entry, "exit": exit_price}]
    wins = sum(1 for t in trades if t["exit"] > t["entry"])
    return equity.reset_index(drop=True), len(trades), wins / len(trades) * 100


def run_value_investing(df: pd.DataFrame):
    # RSI-based: buy <30, sell >70.  Include 50-day warmup.
    warmup = df_all.iloc[max(0, idx_offset - 50): idx_offset + len(df)].copy()
    rsi_full = compute_rsi(warmup["Close"])
    rsi = rsi_full.iloc[-len(df):].reset_index(drop=True)

    cash, shares, in_trade = INITIAL_CAPITAL, 0.0, None
    equity, trades = [], []

    for i in range(len(df)):
        price = df["Close"].iloc[i]
        r = rsi.iloc[i]

        if shares == 0 and (np.isnan(r) or r < 30):
            shares = cash / price
            cash = 0.0
            in_trade = price
        elif shares > 0 and not np.isnan(r) and r > 70:
            cash = shares * price
            trades.append({"entry": in_trade, "exit": price})
            shares, in_trade = 0.0, None

        equity.append(cash + shares * price)

    if shares > 0:
        price = df["Close"].iloc[-1]
        trades.append({"entry": in_trade, "exit": price})
        equity[-1] = shares * price

    wins = sum(1 for t in trades if t["exit"] > t["entry"])
    return pd.Series(equity), len(trades), (wins / len(trades) * 100 if trades else 0.0)


def run_momentum(df: pd.DataFrame):
    # SMA-20 crossover: buy on cross-up, sell on cross-down.
    warmup = df_all.iloc[max(0, idx_offset - 25): idx_offset + len(df)].copy()
    sma_full = warmup["Close"].rolling(20).mean()
    sma = sma_full.iloc[-len(df):].reset_index(drop=True)

    cash, shares, in_trade = INITIAL_CAPITAL, 0.0, None
    equity, trades = [], []
    prev_above: bool | None = None

    for i in range(len(df)):
        price = df["Close"].iloc[i]
        s = sma.iloc[i]
        above = None if np.isnan(s) else (price > s)

        if above is not None and prev_above is not None:
            if above and not prev_above and shares == 0:
                shares = cash / price
                cash = 0.0
                in_trade = price
            elif not above and prev_above and shares > 0:
                cash = shares * price
                trades.append({"entry": in_trade, "exit": price})
                shares, in_trade = 0.0, None

        equity.append(cash + shares * price)
        if above is not None:
            prev_above = above

    if shares > 0:
        price = df["Close"].iloc[-1]
        trades.append({"entry": in_trade, "exit": price})
        equity[-1] = shares * price

    wins = sum(1 for t in trades if t["exit"] > t["entry"])
    return pd.Series(equity), len(trades), (wins / len(trades) * 100 if trades else 0.0)


def run_swing_trading(df: pd.DataFrame, window: int = 5):
    prices = df["Close"].values
    cash, shares, in_trade = INITIAL_CAPITAL, 0.0, None
    equity, trades = [], []

    for i in range(len(df)):
        price = prices[i]
        lo = prices[max(0, i - window): i + 1]
        hi = prices[max(0, i - window): i + 1]

        if i >= window:
            if price == lo.min() and shares == 0:
                shares = cash / price
                cash = 0.0
                in_trade = price
            elif price == hi.max() and shares > 0:
                cash = shares * price
                trades.append({"entry": in_trade, "exit": price})
                shares, in_trade = 0.0, None

        equity.append(cash + shares * price)

    if shares > 0:
        price = prices[-1]
        trades.append({"entry": in_trade, "exit": price})
        equity[-1] = shares * price

    wins = sum(1 for t in trades if t["exit"] > t["entry"])
    return pd.Series(equity), len(trades), (wins / len(trades) * 100 if trades else 0.0)


def run_support_resistance(df: pd.DataFrame, threshold: float = 0.05):
    # Buy near rolling 252-day low, sell near rolling 252-day high.
    cash, shares, in_trade = INITIAL_CAPITAL, 0.0, None
    equity, trades = [], []

    for i in range(len(df)):
        price = df["Close"].iloc[i]
        hist_start = max(0, idx_offset + i - 252)
        hist_prices = df_all["Close"].iloc[hist_start: idx_offset + i + 1]
        low52 = hist_prices.min()
        high52 = hist_prices.max()

        near_support = price <= low52 * (1 + threshold)
        near_resistance = price >= high52 * (1 - threshold)

        if near_support and shares == 0 and cash > 0:
            shares = cash / price
            cash = 0.0
            in_trade = price
        elif near_resistance and shares > 0:
            cash = shares * price
            trades.append({"entry": in_trade, "exit": price})
            shares, in_trade = 0.0, None

        equity.append(cash + shares * price)

    if shares > 0:
        price = df["Close"].iloc[-1]
        trades.append({"entry": in_trade, "exit": price})
        equity[-1] = shares * price

    wins = sum(1 for t in trades if t["exit"] > t["entry"])
    return pd.Series(equity), len(trades), (wins / len(trades) * 100 if trades else 0.0)


# ── Run ───────────────────────────────────────────────────────────────────────

STRATEGY_RUNNERS = {
    "Buy and Hold":                        run_buy_hold,
    "Value Investing":                     run_value_investing,
    "Momentum Investing":                  run_momentum,
    "Swing Trading":                       run_swing_trading,
    "Support-Resistance-52-Week-High-Low": run_support_resistance,
}

COLORS = {
    "Buy and Hold":                        "#1f77b4",
    "Value Investing":                     "#ff7f0e",
    "Momentum Investing":                  "#2ca02c",
    "Swing Trading":                       "#d62728",
    "Support-Resistance-52-Week-High-Low": "#9467bd",
}

results: dict[str, dict] = {}
for name, runner in STRATEGY_RUNNERS.items():
    equity, n_trades, win_rate = runner(df_2025)
    equity = pd.Series(equity).reset_index(drop=True)
    results[name] = {
        "equity":   equity,
        "returns":  (equity.iloc[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100,
        "sharpe":   sharpe_ratio(equity),
        "drawdown": max_drawdown_pct(equity),
        "n_trades": n_trades,
        "win_rate": win_rate,
        "final":    equity.iloc[-1],
    }


# ── Plot ──────────────────────────────────────────────────────────────────────

names = list(results.keys())
short_names = ["Buy and\nHold", "Value\nInvesting", "Momentum\nInvesting", "Swing\nTrading", "SR-52W\nHigh-Low"]

fig = plt.figure(figsize=(18, 14))
fig.suptitle("Trading Strategies Performance Analysis — ASML 2025", fontsize=16, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.48, wspace=0.38)

# ── Panel 1: Portfolio Growth (full width) ────────────────────────────────────
ax_g = fig.add_subplot(gs[0, :])
ax_g.plot(df_2025["date"], [INITIAL_CAPITAL] * len(df_2025), "k--", linewidth=1, label="Initial Capital", alpha=0.5)
for name, r in results.items():
    ax_g.plot(df_2025["date"], r["equity"], label=name, color=COLORS[name], linewidth=1.5)
ax_g.set_title("Portfolio Growth Comparison — ASML 2025", fontsize=13)
ax_g.set_xlabel("Date")
ax_g.set_ylabel("Portfolio Value ($)")
ax_g.legend(fontsize=8, loc="upper left")
ax_g.grid(True, alpha=0.3)

# ── Panel 2: Total Returns ────────────────────────────────────────────────────
ax_ret = fig.add_subplot(gs[1, 0])
ret_vals = [results[n]["returns"] for n in names]
bars = ax_ret.barh(short_names, ret_vals, color=[COLORS[n] for n in names])
ax_ret.set_title("Total Returns", fontsize=11)
ax_ret.set_xlabel("Total Return (%)")
ax_ret.axvline(0, color="black", linewidth=0.8)
for bar, val in zip(bars, ret_vals):
    offset = 0.3 if val >= 0 else -0.3
    ha = "left" if val >= 0 else "right"
    ax_ret.text(val + offset, bar.get_y() + bar.get_height() / 2, f"{val:.1f}%", va="center", ha=ha, fontsize=8)
ax_ret.grid(True, alpha=0.3, axis="x")

# ── Panel 3: Sharpe Ratio ─────────────────────────────────────────────────────
ax_sh = fig.add_subplot(gs[1, 1])
sh_vals = [results[n]["sharpe"] for n in names]
bars = ax_sh.barh(short_names, sh_vals, color=[COLORS[n] for n in names])
ax_sh.set_title("Risk/Returns with Sharpe Ratio", fontsize=11)
ax_sh.set_xlabel("Sharpe Ratio")
ax_sh.axvline(1.0, color="red", linewidth=1, linestyle="--", label="Target (1.0)")
for bar, val in zip(bars, sh_vals):
    ax_sh.text(val + 0.02, bar.get_y() + bar.get_height() / 2, f"{val:.2f}", va="center", fontsize=8)
ax_sh.legend(fontsize=8)
ax_sh.grid(True, alpha=0.3, axis="x")

# ── Panel 4: Max Drawdown ─────────────────────────────────────────────────────
ax_dd = fig.add_subplot(gs[1, 2])
dd_vals = [results[n]["drawdown"] for n in names]
bars = ax_dd.barh(short_names, dd_vals, color=[COLORS[n] for n in names])
ax_dd.set_title("Maximum Drawdown", fontsize=11)
ax_dd.set_xlabel("Maximum Drawdown (%)")
ax_dd.axvline(10, color="red", linewidth=1, linestyle="--", label="Limit (10%)")
for bar, val in zip(bars, dd_vals):
    ax_dd.text(val + 0.1, bar.get_y() + bar.get_height() / 2, f"{val:.1f}%", va="center", fontsize=8)
ax_dd.legend(fontsize=8)
ax_dd.grid(True, alpha=0.3, axis="x")

# ── Panel 5: Trading Frequency ────────────────────────────────────────────────
ax_fr = fig.add_subplot(gs[2, 0])
freq_vals = [results[n]["n_trades"] for n in names]
bars_f = ax_fr.bar(short_names, freq_vals, color=[COLORS[n] for n in names])
ax_fr.set_title("Trading Frequency", fontsize=11)
ax_fr.set_ylabel("Number of Trades")
for bar, val in zip(bars_f, freq_vals):
    ax_fr.text(bar.get_x() + bar.get_width() / 2, val + 0.05, str(val), ha="center", fontsize=8)
ax_fr.grid(True, alpha=0.3, axis="y")
ax_fr.tick_params(axis="x", labelsize=8)

# ── Panel 6: Trading Accuracy ─────────────────────────────────────────────────
ax_ac = fig.add_subplot(gs[2, 1])
wr_vals = [results[n]["win_rate"] for n in names]
bars_a = ax_ac.bar(short_names, wr_vals, color=[COLORS[n] for n in names])
ax_ac.set_title("Trading Accuracy", fontsize=11)
ax_ac.set_ylabel("Win Rate (%)")
ax_ac.set_ylim(0, 115)
for bar, val in zip(bars_a, wr_vals):
    ax_ac.text(bar.get_x() + bar.get_width() / 2, val + 1, f"{val:.1f}%", ha="center", fontsize=8)
ax_ac.grid(True, alpha=0.3, axis="y")
ax_ac.tick_params(axis="x", labelsize=8)

# ── Panel 7: Final Portfolio Value ────────────────────────────────────────────
ax_fv = fig.add_subplot(gs[2, 2])
final_vals = [results[n]["final"] for n in names]
bars_v = ax_fv.bar(short_names, final_vals, color=[COLORS[n] for n in names])
ax_fv.set_title("Final Portfolio Value", fontsize=11)
ax_fv.set_ylabel("Final Value ($)")
ax_fv.axhline(INITIAL_CAPITAL, color="black", linewidth=1, linestyle="--", label=f"Initial (${INITIAL_CAPITAL:,.0f})")
for bar, val in zip(bars_v, final_vals):
    ax_fv.text(bar.get_x() + bar.get_width() / 2, val + 30, f"${val:,.0f}", ha="center", fontsize=7, rotation=25)
ax_fv.legend(fontsize=8)
ax_fv.grid(True, alpha=0.3, axis="y")
ax_fv.tick_params(axis="x", labelsize=8)

plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
print(f"\nSaved: {OUTPUT_PATH}\n")
print(f"{'Strategy':<45}  {'Return':>8}  {'Sharpe':>7}  {'MDD':>6}  {'Trades':>7}  {'WinRate':>8}  {'Final':>10}")
print("-" * 100)
for name, r in results.items():
    print(
        f"{name:<45}  {r['returns']:>7.1f}%  {r['sharpe']:>7.2f}  {r['drawdown']:>5.1f}%  "
        f"{r['n_trades']:>7d}  {r['win_rate']:>7.1f}%  ${r['final']:>9,.0f}"
    )
