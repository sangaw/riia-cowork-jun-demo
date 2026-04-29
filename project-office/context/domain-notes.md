# Financial Domain Notes

Load this file when touching `core/`, pricing logic, lot size calculations, or data paths.

## Instrument

Nifty 50 index (NSE) — F&O portfolio manager.

## Lot Sizes (config-driven, never hardcoded)

| Instrument | Lot size | Note |
|---|---|---|
| NIFTY | 75 | Changed from 50 in 2024 |
| BANKNIFTY | 30 | |

These must come from config, not literals in code.

## Greeks

Delta, Gamma, Theta, Vega — always test against Black-Scholes reference values before and after any `core/` change.

## Data Paths

| Path | Access |
|---|---|
| `rita_input/` | Read-only source data — never write or delete |
| `rita_output/` | Written by the API |
| `*.zip` model files | stable-baselines3 format, stored alongside `rita_output/` |

All data is local CSV — no calls to external data providers.
