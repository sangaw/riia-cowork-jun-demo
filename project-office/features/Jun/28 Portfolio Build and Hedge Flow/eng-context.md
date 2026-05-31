# Feature 28 — Portfolio Build & Hedge Flow: Engineering Context

**Created by:** Engineer (design-review session)
**Last updated:** 2026-05-31

> Status legend for calcs: ✅ decided · 🟡 proposed, pending confirmation · 🔴 open

---

## Calculations (single source of truth)

All inputs come from the existing **daily-close price cache** (the same source `geography-overview` and `portfolio-performance` already read) unless noted. No live option chain is available.

### C1 — Risk score (1–5) 🟡
- Daily returns over trailing ~1Y: `r_t = close_t / close_{t-1} − 1`
- Annualized volatility: `σ = stdev(r_t) × √252`
- Bucket (absolute thresholds, proposed): `<15%→1 · 15–25→2 · 25–35→3 · 35–50→4 · >50→5`
- Optional later: blend with beta-to-index. v1 = vol only.
- Edge: <~60 trading days of history → risk `null`, UI shows "n/a".

### C2 — 1Y return % 🟡
- `(close_latest / close_~252d_ago − 1) × 100`
- Edge: insufficient history → `null` → UI "n/a" (never a misleading 0).

### C3 — Payoff curve (backend) ✅ source / 🔴 model params
For market move `m` (x-axis −20%…+10%):
- **Unhedged P&L(m)** = `Σ wᵢ · βᵢ · m`, with **βᵢ = 1 for v1** (D2) → simplifies to `m`
- **Hedged P&L(m)** = unhedged + per-holding option payoff:
  - Protective put @ `−k%`: keep move − premium for `m > −k`; floored at `−k − premium` for `m < −k`.
  - Put spread `−k₁/−k₂`: protection only between strikes.
  - No-F&O → index-proxy put; protection scaled by correlation/beta to proxy index (reuses Feature 27 `eligible`).

### C4 — Coverage slider → strike / cost / %protected ✅
- Coverage `c ∈ [0,100]%`, **continuous slider with tick increments shown**.
- Strike distance: `k = lerp(−15% OTM @ c=0 … ATM @ c=100)`
- % protected: rises with `c`; for proxy rows × correlation-to-index.
- Premium (cost %): **(b) Black–Scholes put** using **realized vol** (σ from C1) as IV proxy, spot, 1-month tenor. ✅ decided (D1)

### C5 — Aggregate readouts ✅
- **Max drawdown protected** = min point of hedged curve (e.g. −7%) vs unhedged (e.g. −22%).
- **Monthly cost** = `Σ wᵢ · premiumᵢ` as monthly premium drag.
- **Scenario table** = discrete samples of C3 at −20 / −10 / Flat / +10.

### Guardrail
- Index-put contract counts must read lot sizes from `settings.instruments.nifty.lot_size` (75) / `settings.instruments.banknifty.lot_size` (30) — never hardcode (rita-project §2). Bites once we show contract counts (not % figures).

---

## Decisions

| # | Decision | Status |
|---|---|---|
| — | Payoff curve computed in backend (real calc) | ✅ |
| — | Coverage = continuous slider with increments shown | ✅ |
| — | Keep both RITA + FnO builders; consolidate later | ✅ |
| D1 | Premium model: **(b) Black–Scholes put on realized vol** (σ from C1, 1-month tenor) | ✅ |
| D2 | Payoff beta: **β = 1 for v1** (per-holding betas = follow-up) | ✅ |
| C1 | Risk score = annualized-vol bucketed, absolute thresholds | 🟡 confirm |

---

## API Contract (draft — to finalize in Phase 0)

| Endpoint | Method | Tier | Notes |
|---|---|---|---|
| builder-universe (extend `geography-overview` or new) | GET | Experience | + `return_1y_pct`, `risk_score` (1–5), `sector` per instrument |
| `…/fno/portfolio-hedge?coverage=` | GET | Experience | + per-row `strike`, `protected_pct`; aggregate `max_dd_protected_pct`, `monthly_cost_pct` |
| payoff/scenario (new) | GET | Experience | hedged vs unhedged curve points + scenario rows for a given `coverage` |

---

## Open Engineering Questions

| # | Question | Status |
|---|---|---|
| D1 | Premium model | Resolved: (b) BS on realized vol |
| D2 | Payoff beta | Resolved: β = 1 for v1 |
| Q1 | Does instruments table already store `sector`? | Open |
</content>
