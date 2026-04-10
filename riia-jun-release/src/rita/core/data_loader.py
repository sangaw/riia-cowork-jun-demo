"""
RITA Core — Data Loader
Loads OHLCV data from the local CSV store.

Folder layout (all paths relative to the project root):
    data/raw/{INSTRUMENT}/       — source CSVs as downloaded (read-only)
    data/input/{INSTRUMENT}/     — processed/merged CSVs ready for the model
    data/output/{INSTRUMENT}/    — backtest results, risk timeline, trade events
    models/{INSTRUMENT}/         — trained model ZIPs

Expected CSV columns: date, open, high, low, close, shares traded, turnover (₹ cr)
Date format: "1999-07-01 00:00:00+05:30" (timezone-aware IST)
"""

from pathlib import Path

import pandas as pd

from rita.config import settings


# ---------------------------------------------------------------------------
# Path helpers — resolve instrument-scoped directories from config
# ---------------------------------------------------------------------------

def raw_dir(instrument: str) -> Path:
    """Return the raw data directory for *instrument*, creating it if needed."""
    p = Path(settings.data.raw_dir) / instrument.upper()
    p.mkdir(parents=True, exist_ok=True)
    return p


def input_dir(instrument: str) -> Path:
    """Return the processed input directory for *instrument*, creating it if needed."""
    p = Path(settings.data.input_dir) / instrument.upper()
    p.mkdir(parents=True, exist_ok=True)
    return p


def output_dir(instrument: str) -> Path:
    """Return the output directory for *instrument*, creating it if needed."""
    p = Path(settings.data.output_dir) / instrument.upper()
    p.mkdir(parents=True, exist_ok=True)
    return p


def model_dir(instrument: str) -> Path:
    """Return the model directory for *instrument*, creating it if needed."""
    p = Path(settings.model.path) / instrument.upper()
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# CSV loader
# ---------------------------------------------------------------------------

def load_nifty_csv(csv_path: str) -> pd.DataFrame:
    """
    Load Nifty 50 data from the merged CSV file.

    Returns a DataFrame with DatetimeIndex and columns:
    Open, High, Low, Close, Volume
    """
    df = pd.read_csv(csv_path)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Parse and normalize the date column (strip timezone if present)
    sample = str(df["date"].iloc[0])
    if "+" in sample or len(sample) > 12:
        # Timezone-aware format (e.g. Nifty: "1999-07-01 00:00:00+05:30")
        df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    else:
        # Plain ISO date (e.g. ASML: "2001-03-09")
        df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df.index.name = "Date"

    # Rename to standard OHLCV names
    rename_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "shares traded": "Volume",  # Nifty NSE column name
        "volume": "Volume",         # Generic / international column name
    }
    df = df.rename(columns=rename_map)

    # Drop unused columns
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[keep]

    # Sort and validate
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    df = df.dropna(subset=["Close"])

    if len(df) == 0:
        raise ValueError(f"No valid data found in {csv_path}")

    return df
