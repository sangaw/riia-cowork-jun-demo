"""
Seed 7 new instruments into RITA — Ather, Reliance, ASR NL, Atos, AEX, DJI, Nasdaq.

Downloads historical OHLCV from Yahoo Finance, writes CSVs, inserts DB records,
and seeds the market_data_cache for 2025+ rows.

Usage (run from project root — riia-cowork-jun/):
    python project-office/scripts/seed_new_instruments.py

Usage on EC2 (inside the container):
    RITA_DB_PATH=/app/rita_output/rita.db \\
    RITA_DATA_RAW=/app/data/raw \\
    RITA_DATA_INPUT=/app/data/input \\
    python project-office/scripts/seed_new_instruments.py

Safe to re-run — skips instruments and cache rows that already exist.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Path wiring ───────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parents[2]          # riia-cowork-jun/
sys.path.insert(0, str(REPO_ROOT / "riia-jun-release" / "src"))

import pandas as pd

DB_PATH        = Path(os.environ.get("RITA_DB_PATH",   str(REPO_ROOT / "riia-jun-release" / "rita_output" / "rita.db")))
DATA_RAW_ROOT  = Path(os.environ.get("RITA_DATA_RAW",  str(REPO_ROOT / "riia-jun-release" / "data" / "raw")))
DATA_INPUT_ROOT= Path(os.environ.get("RITA_DATA_INPUT",str(REPO_ROOT / "riia-jun-release" / "data" / "input")))

# ── Instrument definitions ────────────────────────────────────────────────────
# instrument_id  — used for DB primary key, CSV directory, and UI display
# yf_ticker      — Yahoo Finance symbol (may differ for indices / .NS stocks)

INSTRUMENTS: list[dict] = [
    # Core indices (yf_ticker backfill — may already be in DB; upsert_instrument
    # will set yf_ticker if not already set)
    {
        "instrument_id": "NIFTY",
        "yf_ticker":     "^NSEI",
        "name":          "Nifty 50",
        "exchange":      "NSE",
        "country_code":  "IN",
        "currency":      "INR",
        "lot_size":      75,
    },
    {
        "instrument_id": "BANKNIFTY",
        "yf_ticker":     "^NSEBANK",
        "name":          "Nifty Bank",
        "exchange":      "NSE",
        "country_code":  "IN",
        "currency":      "INR",
        "lot_size":      30,
    },
    {
        "instrument_id": "NVIDIA",
        "yf_ticker":     "NVDA",
        "name":          "NVIDIA Corporation",
        "exchange":      "NASDAQ",
        "country_code":  "US",
        "currency":      "USD",
        "lot_size":      None,
    },
    # India
    {
        "instrument_id": "ATHER",
        "yf_ticker":     "ATHER.NS",
        "name":          "Ather Energy",
        "exchange":      "NSE",
        "country_code":  "IN",
        "currency":      "INR",
        "lot_size":      None,
    },
    {
        "instrument_id": "SBIN",
        "yf_ticker":     "SBIN.NS",
        "name":          "State Bank of India",
        "exchange":      "NSE",
        "country_code":  "IN",
        "currency":      "INR",
        "lot_size":      None,
    },
    {
        "instrument_id": "RELIANCE",
        "yf_ticker":     "RELIANCE.NS",
        "name":          "Reliance Industries",
        "exchange":      "NSE",
        "country_code":  "IN",
        "currency":      "INR",
        "lot_size":      None,
    },
    # EU
    {
        "instrument_id": "ASRNL",
        "yf_ticker":     "ASRNL.AS",
        "name":          "ASR Nederland",
        "exchange":      "AMS",
        "country_code":  "NL",
        "currency":      "EUR",
        "lot_size":      None,
    },
    {
        "instrument_id": "ATO",
        "yf_ticker":     "ATO.PA",
        "name":          "Atos SE",
        "exchange":      "PAR",
        "country_code":  "FR",
        "currency":      "EUR",
        "lot_size":      None,
    },
    {
        "instrument_id": "AEX",
        "yf_ticker":     "^AEX",
        "name":          "AEX Index",
        "exchange":      "AMS",
        "country_code":  "NL",
        "currency":      "EUR",
        "lot_size":      None,
    },
    # US
    {
        "instrument_id": "DJI",
        "yf_ticker":     "^DJI",
        "name":          "Dow Jones Industrial Average",
        "exchange":      "DJI",
        "country_code":  "US",
        "currency":      "USD",
        "lot_size":      None,
    },
    {
        "instrument_id": "IXIC",
        "yf_ticker":     "^IXIC",
        "name":          "Nasdaq Composite",
        "exchange":      "NASDAQ",
        "country_code":  "US",
        "currency":      "USD",
        "lot_size":      None,
    },
]


# ── Step 1: Download raw CSV via yfinance ─────────────────────────────────────

def download_raw(inst: dict) -> Path | None:
    """Download OHLCV from yfinance; save to data/raw/{instrument_id}/."""
    import yfinance as yf

    yf_ticker     = inst["yf_ticker"]
    instrument_id = inst["instrument_id"]

    print(f"  [1] Download {yf_ticker} ...", end=" ", flush=True)
    try:
        df: pd.DataFrame = yf.download(
            yf_ticker,
            start="2009-09-01",
            interval="1d",
            auto_adjust=True,
            progress=False,
        )
    except Exception as exc:
        print(f"FAILED -- {exc}")
        return None

    if df is None or len(df) < 100:
        print(f"FAILED -- only {len(df) if df is not None else 0} rows (need >= 100)")
        return None

    # Flatten multi-level columns (yfinance >= 0.2.x may return MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    raw_dir = DATA_RAW_ROOT / instrument_id.upper()
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{instrument_id.lower()}_daily.csv"
    df.to_csv(raw_path)
    print(f"OK -- {len(df)} rows -> {raw_path.relative_to(REPO_ROOT)}")
    return raw_path


# ── Step 2: Normalize to input CSV ───────────────────────────────────────────

def process_to_input(instrument_id: str, raw_path: Path) -> Path | None:
    """Normalize raw CSV (drop tz, filter ≥ 2010) and write to data/input/{instrument_id}/."""
    from rita.core.data_loader import load_ohlcv_csv

    print(f"  [2] Normalize ...", end=" ", flush=True)
    try:
        df = load_ohlcv_csv(str(raw_path))
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df = df[df.index.year >= 2010].sort_index()

        input_dir = DATA_INPUT_ROOT / instrument_id.upper()
        input_dir.mkdir(parents=True, exist_ok=True)
        input_path = input_dir / f"{instrument_id.lower()}_daily.csv"
        df.to_csv(input_path)
        print(f"OK -- {len(df)} rows -> {input_path.relative_to(REPO_ROOT)}")
        return input_path
    except Exception as exc:
        print(f"FAILED — {exc}")
        return None


# ── Step 3: Upsert instrument record ─────────────────────────────────────────

def upsert_instrument(engine, inst: dict) -> None:
    from sqlalchemy.orm import Session
    from rita.models.instrument import InstrumentModel

    print(f"  [3] DB record ...", end=" ", flush=True)
    with Session(engine) as db:
        existing = db.query(InstrumentModel).filter(
            InstrumentModel.instrument_id == inst["instrument_id"]
        ).first()
        if existing:
            # Update is_available and yf_ticker if needed
            updated = False
            if not existing.is_available:
                existing.is_available = True
                updated = True
            if inst.get("yf_ticker") and not existing.yf_ticker:
                existing.yf_ticker = inst["yf_ticker"]
                updated = True
            if updated:
                db.commit()
                print(f"UPDATED (set is_available=True and/or yf_ticker)")
            else:
                print(f"SKIP (already exists, is_available=True)")
            return

        record = InstrumentModel(
            instrument_id=inst["instrument_id"],
            name=inst["name"],
            exchange=inst["exchange"],
            country_code=inst["country_code"],
            currency=inst.get("currency"),
            lot_size=inst.get("lot_size"),
            is_available=True,
            yf_ticker=inst.get("yf_ticker"),
            created_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
    print(f"OK -- inserted (is_available=True)")


# ── Step 4: Seed market_data_cache (2025+ rows) ───────────────────────────────

def seed_market_cache(engine, instrument_id: str) -> int:
    from sqlalchemy.orm import Session
    from rita.models.market_data import MarketDataCacheModel
    from rita.repositories.market_data import MarketDataCacheRepository
    from rita.core.data_loader import load_ohlcv_csv

    print(f"  [4] Market cache ...", end=" ", flush=True)
    with Session(engine) as db:
        already = {r.underlying for r in MarketDataCacheRepository(db).read_all()}
        if instrument_id.upper() in already:
            print(f"SKIP (already seeded)")
            return 0

        input_path = DATA_INPUT_ROOT / instrument_id.upper() / f"{instrument_id.lower()}_daily.csv"
        if not input_path.exists():
            print(f"SKIP (input CSV not found)")
            return 0

        try:
            df = load_ohlcv_csv(str(input_path))
            df = df[df.index.year >= 2025]
            if df.empty:
                print(f"SKIP (no 2025+ rows)")
                return 0

            now = datetime.now(timezone.utc)
            records = [
                MarketDataCacheModel(
                    cache_id=str(uuid.uuid4()),
                    date=ts.date(),
                    underlying=instrument_id.upper(),
                    open=float(row["Open"]) if "Open" in row else 0.0,
                    high=float(row["High"]) if "High" in row else 0.0,
                    low=float(row["Low"]) if "Low" in row else 0.0,
                    close=float(row["Close"]),
                    shares_traded=(
                        int(row["Volume"])
                        if "Volume" in row and pd.notna(row["Volume"])
                        else None
                    ),
                    turnover_cr=None,
                    recorded_at=now,
                )
                for ts, row in df.iterrows()
            ]
            db.add_all(records)
            db.commit()
            print(f"OK -- {len(records)} rows (2025+)")
            return len(records)
        except Exception as exc:
            print(f"FAILED — {exc}")
            return 0


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    from sqlalchemy import create_engine
    from rita.database import Base

    print(f"RITA Instrument Seeder")
    print(f"  DB:    {DB_PATH}")
    print(f"  Raw:   {DATA_RAW_ROOT}")
    print(f"  Input: {DATA_INPUT_ROOT}")
    print()

    if not DB_PATH.exists():
        print("ERROR: rita.db not found. Start the RITA server once to create it, then re-run.")
        sys.exit(1)

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)  # no-op if tables already exist

    results: list[tuple[str, str, str]] = []

    for inst in INSTRUMENTS:
        iid = inst["instrument_id"]
        print(f"-- {iid}  ({inst['name']})  [{inst['yf_ticker']}] ------------------")

        raw_path = download_raw(inst)
        if raw_path is None:
            results.append((iid, "FAILED", "download"))
            print()
            continue

        input_path = process_to_input(iid, raw_path)
        if input_path is None:
            results.append((iid, "FAILED", "normalize"))
            print()
            continue

        upsert_instrument(engine, inst)
        cache_rows = seed_market_cache(engine, iid)

        results.append((iid, "OK", f"{cache_rows} cache rows seeded"))
        print()

    # Summary
    print("-- Summary " + "-" * 50)
    for iid, status, detail in results:
        marker = "OK" if status == "OK" else "!!"
        print(f"  [{marker}] {iid:<12}  {status:<8}  {detail}")

    ok  = sum(1 for _, s, _ in results if s == "OK")
    fail= len(results) - ok
    print()
    print(f"{ok}/{len(results)} instruments seeded.  {'Restart the RITA server to see them in the dashboard.' if ok else ''}")
    if fail:
        print(f"{fail} failed -- check output above. Re-run after fixing.")


if __name__ == "__main__":
    main()
