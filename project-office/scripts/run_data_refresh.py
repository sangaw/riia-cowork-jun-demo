#!/usr/bin/env python3
"""Standalone script to refresh all instruments' price data via the RITA API."""
import json
import os
import sys
import requests


RITA_API_BASE = os.environ.get("RITA_API_BASE", "http://localhost:8000")


def main():
    # Health check
    try:
        r = requests.get(f"{RITA_API_BASE}/health", timeout=5)
        r.raise_for_status()
    except Exception as e:
        print(f"ERROR: RITA server not reachable at {RITA_API_BASE}: {e}")
        sys.exit(1)

    print(f"Calling POST {RITA_API_BASE}/api/v1/instrument/refresh-all ...")
    try:
        r = requests.post(f"{RITA_API_BASE}/api/v1/instrument/refresh-all", timeout=300)
        r.raise_for_status()
    except Exception as e:
        print(f"ERROR: refresh endpoint failed: {e}")
        sys.exit(1)

    data = r.json()
    print(f"\n=== Data Refresh Results ===")
    print(f"Refreshed:       {data['refreshed']}")
    print(f"Already current: {data['already_current']}")
    print()
    print(f"{'Instrument':<12} {'Gap Days':>9} {'Raw Added':>10} {'DB Inserted':>12} {'Status':<10}")
    print("-" * 60)
    for res in data["results"]:
        print(f"{res['instrument']:<12} {res['gap_days']:>9} {res['raw_rows_added']:>10} {res['db_rows_inserted']:>12} {res['status']:<10}")
        if res.get("error"):
            print(f"  ERROR: {res['error']}")
    print()


if __name__ == "__main__":
    main()
