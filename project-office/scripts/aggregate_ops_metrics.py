#!/usr/bin/env python3
"""Reads RITA JSONL logs and writes ops/metrics/*.json summaries.

Run from worktree root:
    python project-office/scripts/aggregate_ops_metrics.py

Output files:
    riia-jun-release/ops/metrics/metrics-summary.json
    riia-jun-release/ops/metrics/functional-kpis.json
    riia-jun-release/ops/metrics/source-availability.json
    riia-jun-release/ops/alerts/active-alerts.json
    riia-jun-release/ops/alerts/alert-history.jsonl
"""
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import quantiles

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

WORKTREE_ROOT = Path(__file__).resolve().parents[2]  # up from project-office/scripts/
LOG_DIR = WORKTREE_ROOT / "riia-jun-release" / "logs"
OPS_METRICS_DIR = WORKTREE_ROOT / "riia-jun-release" / "ops" / "metrics"
OPS_ALERTS_DIR = WORKTREE_ROOT / "riia-jun-release" / "ops" / "alerts"


# ---------------------------------------------------------------------------
# JSONL reader
# ---------------------------------------------------------------------------

def read_jsonl(path: Path) -> list[dict]:
    """Read all JSON lines from a JSONL file.

    Returns empty list if the file is missing or unreadable.
    Malformed lines are skipped with a warning.
    """
    if not path.exists():
        log.warning("Log file not found: %s — returning empty list", path)
        return []
    records = []
    try:
        with path.open(encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    records.append(json.loads(raw))
                except json.JSONDecodeError as exc:
                    log.warning("Skipping malformed line %d in %s: %s", lineno, path.name, exc)
    except OSError as exc:
        log.warning("Cannot read %s: %s — returning empty list", path, exc)
    return records


# ---------------------------------------------------------------------------
# Log parsing helpers
# ---------------------------------------------------------------------------

def _parse_timestamp(record: dict) -> datetime | None:
    """Extract a UTC datetime from a log record.

    The outer wrapper has a "time" key (asctime string) but structlog also
    embeds a "timestamp" field inside the inner message JSON.  We prefer the
    inner timestamp (already ISO-8601 with timezone), falling back to the
    outer "time" string.
    """
    # Try inner message JSON first
    msg = record.get("message")
    if isinstance(msg, dict):
        ts_str = msg.get("timestamp")
    elif isinstance(msg, str):
        try:
            msg_parsed = json.loads(msg)
            ts_str = msg_parsed.get("timestamp") if isinstance(msg_parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            ts_str = None
    else:
        ts_str = None

    if ts_str:
        try:
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass

    # Fall back to outer "time" field
    outer = record.get("time")
    if outer:
        for fmt in (
            "%Y-%m-%d %H:%M:%S,%f",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                dt = datetime.strptime(outer, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
    return None


def _get_message_dict(record: dict) -> dict:
    """Return the inner message as a dict (structlog renders it as JSON)."""
    msg = record.get("message")
    if isinstance(msg, dict):
        return msg
    if isinstance(msg, str):
        try:
            parsed = json.loads(msg)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _filter_window(records: list[dict], since: datetime, until: datetime) -> list[dict]:
    """Return only records whose timestamp falls within [since, until)."""
    out = []
    for r in records:
        dt = _parse_timestamp(r)
        if dt is None:
            continue
        if since <= dt < until:
            out.append(r)
    return out


def _get_event(record: dict) -> str:
    """Return the event name from a log record."""
    msg = _get_message_dict(record)
    return msg.get("event", record.get("message", ""))


def _get_level(record: dict) -> str:
    """Return the level string (lowercase) from a log record."""
    return str(record.get("level", "")).lower()


# ---------------------------------------------------------------------------
# Metric computation helpers
# ---------------------------------------------------------------------------

def _compute_error_rate(app_records: list[dict]) -> float:
    if not app_records:
        return 0.0
    errors = sum(1 for r in app_records if _get_level(r) in ("error", "critical"))
    return round(errors / len(app_records) * 100, 2)


def _compute_p95_latency(app_records: list[dict]) -> float:
    latencies = []
    for r in app_records:
        msg = _get_message_dict(r)
        dur = msg.get("duration_ms")
        if dur is not None:
            try:
                latencies.append(float(dur))
            except (TypeError, ValueError):
                pass
    if not latencies:
        return 0.0
    if len(latencies) == 1:
        return latencies[0]
    # quantiles needs at least 2 data points and n>=1
    try:
        return round(quantiles(latencies, n=100)[94], 2)  # index 94 = p95
    except Exception:
        return round(sorted(latencies)[int(len(latencies) * 0.95)], 2)


def _compute_top_failing_endpoints(app_records: list[dict], top_n: int = 3) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for r in app_records:
        if _get_level(r) not in ("error", "critical"):
            continue
        msg = _get_message_dict(r)
        endpoint = msg.get("endpoint") or msg.get("event") or "unknown"
        counts[endpoint] += 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"endpoint": ep, "error_count": cnt} for ep, cnt in ranked]


def _compute_job_failures(job_records: list[dict]) -> int:
    return sum(
        1 for r in job_records
        if _get_event(r) in ("training.failed", "backtest.failed")
    )


def _compute_success_rate(job_records: list[dict], prefix: str) -> float:
    """Compute success rate for training or backtest events."""
    complete_event = f"{prefix}.complete"
    failed_event = f"{prefix}.failed"
    complete = sum(1 for r in job_records if _get_event(r) == complete_event)
    failed = sum(1 for r in job_records if _get_event(r) == failed_event)
    total = complete + failed
    if total == 0:
        return 0.0
    return round(complete / total * 100, 2)


def _compute_chat_low_confidence(app_records: list[dict]) -> float:
    """Pct of chat.response events where confidence < 0.6."""
    chat_events = [
        r for r in app_records if _get_event(r) == "chat.response"
    ]
    if not chat_events:
        return 0.0
    low = 0
    for r in chat_events:
        msg = _get_message_dict(r)
        conf = msg.get("confidence")
        try:
            if conf is not None and float(conf) < 0.6:
                low += 1
        except (TypeError, ValueError):
            pass
    return round(low / len(chat_events) * 100, 2)


def _compute_drift_counts(job_records: list[dict]) -> tuple[int, int]:
    """Return (warn_count, alert_count) for drift events."""
    warn = 0
    alert = 0
    for r in job_records:
        if not _get_event(r).startswith("drift"):
            continue
        msg = _get_message_dict(r)
        sev = str(msg.get("severity", "")).lower()
        if sev == "warn":
            warn += 1
        elif sev == "alert":
            alert += 1
    return warn, alert


def _compute_experience_pcts(exp_records: list[dict]) -> tuple[float, float, float]:
    """Return (all_ok_pct, partial_pct, error_pct) from experience.compose events."""
    compose_events = [r for r in exp_records if _get_event(r) == "experience.compose"]
    if not compose_events:
        return 0.0, 0.0, 0.0
    total = len(compose_events)
    all_ok = 0
    partial = 0
    error = 0
    for r in compose_events:
        msg = _get_message_dict(r)
        status = str(msg.get("overall_status", "")).lower()
        if status == "ok":
            all_ok += 1
        elif status == "partial":
            partial += 1
        elif status == "error":
            error += 1
    return (
        round(all_ok / total * 100, 2),
        round(partial / total * 100, 2),
        round(error / total * 100, 2),
    )


def _compute_source_availability(exp_records: list[dict]) -> dict[str, dict]:
    """Tally ok/empty/error counts per source key from experience.compose events."""
    tally: dict[str, dict[str, int]] = defaultdict(lambda: {"ok": 0, "empty": 0, "error": 0})
    for r in exp_records:
        if _get_event(r) != "experience.compose":
            continue
        msg = _get_message_dict(r)
        sources = msg.get("sources")
        if not isinstance(sources, dict):
            continue
        for src_name, src_data in sources.items():
            if not isinstance(src_data, dict):
                continue
            status = str(src_data.get("status", "error")).lower()
            if status not in ("ok", "empty", "error"):
                status = "error"
            tally[src_name][status] += 1
    return {name: dict(counts) for name, counts in tally.items()}


# ---------------------------------------------------------------------------
# Per-hour bucket computation
# ---------------------------------------------------------------------------

def _compute_bucket_metrics(
    app_records: list[dict],
    job_records: list[dict],
    exp_records: list[dict],
    bucket_start: datetime,
) -> dict[str, float]:
    """Compute all 5 KPI values for a single 1-hour bucket."""
    bucket_end = bucket_start + timedelta(hours=1)

    app_win = _filter_window(app_records, bucket_start, bucket_end)
    job_win = _filter_window(job_records, bucket_start, bucket_end)
    exp_win = _filter_window(exp_records, bucket_start, bucket_end)

    training_rate = _compute_success_rate(job_win, "training")
    chat_low = _compute_chat_low_confidence(app_win)
    _, _, exp_err_pct = _compute_experience_pcts(exp_win)
    err_rate = _compute_error_rate(app_win)
    p95 = _compute_p95_latency(app_win)

    return {
        "training_success_rate_pct": training_rate,
        "chat_low_confidence_pct": chat_low,
        "experience_error_pct": exp_err_pct,
        "error_rate_pct": err_rate,
        "p95_latency_ms": p95,
    }


# ---------------------------------------------------------------------------
# Main aggregation
# ---------------------------------------------------------------------------

def main() -> None:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    log.info("Aggregating ops metrics | period: %s → %s", since.isoformat(), now.isoformat())

    # Ensure output directories exist
    OPS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    OPS_ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    # Read all 4 log files
    app_all = read_jsonl(LOG_DIR / "app.jsonl")
    exp_all = read_jsonl(LOG_DIR / "experience.jsonl")
    job_all = read_jsonl(LOG_DIR / "jobs.jsonl")
    # client_errors_all = read_jsonl(LOG_DIR / "client-errors.jsonl")  # reserved for future use

    # Filter to 24-hour window
    app_win = _filter_window(app_all, since, now)
    exp_win = _filter_window(exp_all, since, now)
    job_win = _filter_window(job_all, since, now)

    log.info(
        "Records in window — app:%d experience:%d jobs:%d",
        len(app_win), len(exp_win), len(job_win),
    )

    # ── metrics-summary.json ──────────────────────────────────────────────
    drift_warn, drift_alert = _compute_drift_counts(job_win)
    exp_ok_pct, exp_partial_pct, exp_err_pct = _compute_experience_pcts(exp_win)
    src_avail = _compute_source_availability(exp_win)
    data_freshness = 0.0 if (app_win or exp_win or job_win) else 99.0

    summary = {
        "generated_at": now.isoformat(),
        "period": {"from": since.isoformat(), "to": now.isoformat()},
        "operational": {
            "request_count": len(app_win),
            "error_rate_pct": _compute_error_rate(app_win),
            "p95_latency_ms": _compute_p95_latency(app_win),
            "top_failing_endpoints": _compute_top_failing_endpoints(app_win),
            "background_job_failures": _compute_job_failures(job_win),
        },
        "functional": {
            "training_success_rate_pct": _compute_success_rate(job_win, "training"),
            "backtest_success_rate_pct": _compute_success_rate(job_win, "backtest"),
            "chat_low_confidence_pct": _compute_chat_low_confidence(app_win),
            "drift_warn_count": drift_warn,
            "drift_alert_count": drift_alert,
            "data_freshness_days": data_freshness,
            "experience_all_ok_pct": exp_ok_pct,
            "experience_partial_pct": exp_partial_pct,
            "experience_error_pct": exp_err_pct,
        },
        "source_availability": {
            name: {"ok": counts["ok"], "empty": counts["empty"], "error": counts["error"]}
            for name, counts in src_avail.items()
        },
    }

    _write_json(OPS_METRICS_DIR / "metrics-summary.json", summary)

    # ── functional-kpis.json (24 hourly buckets) ──────────────────────────
    buckets = [since + timedelta(hours=i) for i in range(24)]
    series: dict[str, list[float]] = {
        "training_success_rate_pct": [],
        "chat_low_confidence_pct": [],
        "experience_error_pct": [],
        "error_rate_pct": [],
        "p95_latency_ms": [],
    }

    for bucket_start in buckets:
        bucket_metrics = _compute_bucket_metrics(app_all, job_all, exp_all, bucket_start)
        for key in series:
            series[key].append(bucket_metrics[key])

    functional_kpis = {
        "generated_at": now.isoformat(),
        "buckets": [b.isoformat() for b in buckets],
        "series": series,
    }

    _write_json(OPS_METRICS_DIR / "functional-kpis.json", functional_kpis)

    # ── source-availability.json ──────────────────────────────────────────
    source_avail_out: dict[str, dict] = {}
    for name, counts in src_avail.items():
        total = counts["ok"] + counts["empty"] + counts["error"]
        ok_pct = round(counts["ok"] / total * 100, 2) if total > 0 else 0.0
        source_avail_out[name] = {
            "ok": counts["ok"],
            "empty": counts["empty"],
            "error": counts["error"],
            "total": total,
            "ok_pct": ok_pct,
        }

    source_availability = {
        "generated_at": now.isoformat(),
        "period": {"from": since.isoformat(), "to": now.isoformat()},
        "sources": source_avail_out,
    }

    _write_json(OPS_METRICS_DIR / "source-availability.json", source_availability)

    # ── active-alerts.json (seed / reset) ────────────────────────────────
    active_alerts_path = OPS_ALERTS_DIR / "active-alerts.json"
    if not active_alerts_path.exists():
        _write_json(active_alerts_path, {"generated_at": now.isoformat(), "alerts": []})

    # ── alert-history.jsonl (touch if absent) ────────────────────────────
    alert_history_path = OPS_ALERTS_DIR / "alert-history.jsonl"
    if not alert_history_path.exists():
        alert_history_path.touch()
        log.info("Created empty %s", alert_history_path)

    log.info("Done — wrote metrics-summary.json, functional-kpis.json, source-availability.json")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    log.info("Wrote %s", path)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Aggregator failed: %s", exc)
        sys.exit(1)
