#!/usr/bin/env python3
"""Evaluates RITA alert rules and writes active-alerts.json + alert-history.jsonl.

Run from worktree root:
    python project-office/scripts/generate_alerts.py

Reads:
    riia-jun-release/ops/metrics/metrics-summary.json
    riia-jun-release/logs/jobs.jsonl

Writes:
    riia-jun-release/ops/alerts/active-alerts.json
    riia-jun-release/ops/alerts/alert-history.jsonl     (append)
    riia-jun-release/ops/alerts/daily-digest-YYYY-MM-DD.md
"""
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

WORKTREE_ROOT = Path(__file__).resolve().parents[2]  # up from project-office/scripts/
OPS_ALERTS_DIR = WORKTREE_ROOT / "riia-jun-release" / "ops" / "alerts"
OPS_METRICS_DIR = WORKTREE_ROOT / "riia-jun-release" / "ops" / "metrics"
LOG_DIR = WORKTREE_ROOT / "riia-jun-release" / "logs"

# ---------------------------------------------------------------------------
# Alert rule definitions
# ---------------------------------------------------------------------------

# Each rule: (rule_id, severity, component)
# Threshold-based rules are evaluated in evaluate_threshold_rules().
# Event-based rules (training_failed, backtest_failed, source_down) have
# their own evaluation functions.

THRESHOLD_RULES = [
    # (rule_id, metric_path, operator, threshold, severity, component, message_template)
    (
        "error_rate_high",
        ("operational", "error_rate_pct"),
        "gt",
        5.0,
        "critical",
        "api",
        "Error rate {value:.1f}% exceeds threshold {threshold}%",
    ),
    (
        "latency_high",
        ("operational", "p95_latency_ms"),
        "gt",
        1500.0,
        "warning",
        "api",
        "p95 latency {value}ms exceeds threshold {threshold}ms",
    ),
    (
        "chat_low_confidence",
        ("functional", "chat_low_confidence_pct"),
        "gt",
        25.0,
        "warning",
        "chat",
        "Chat low-confidence rate {value:.1f}% exceeds threshold {threshold}%",
    ),
    (
        "experience_partial",
        ("functional", "experience_partial_pct"),
        "gt",
        10.0,
        "warning",
        "experience",
        "Experience partial rate {value:.1f}% exceeds threshold {threshold}%",
    ),
    (
        "experience_error",
        ("functional", "experience_error_pct"),
        "gt",
        5.0,
        "critical",
        "experience",
        "Experience error rate {value:.1f}% exceeds threshold {threshold}%",
    ),
]

# data_stale rules are handled separately (two thresholds, same field)
DATA_FRESHNESS_PATH = ("functional", "data_freshness_days")


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def read_json(path: Path) -> dict | None:
    """Read a JSON file; return None if missing or unreadable."""
    if not path.exists():
        log.warning("File not found: %s", path)
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("Cannot read %s: %s", path, exc)
        return None


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


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    log.info("Wrote %s", path)


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Jobs.jsonl parsing helpers
# ---------------------------------------------------------------------------

def _parse_timestamp(record: dict) -> datetime | None:
    """Extract a UTC datetime from a log record.

    Structlog embeds a "timestamp" field inside the inner message JSON.
    Falls back to the outer "time" key.
    """
    msg = record.get("message")
    ts_str = None
    if isinstance(msg, dict):
        ts_str = msg.get("timestamp")
    elif isinstance(msg, str):
        try:
            msg_parsed = json.loads(msg)
            ts_str = msg_parsed.get("timestamp") if isinstance(msg_parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            pass

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


def _get_event(record: dict) -> str:
    msg = _get_message_dict(record)
    return msg.get("event", record.get("message", ""))


def _has_event_in_last_hour(records: list[dict], event_name: str, now: datetime) -> bool:
    """Return True if any record with the given event name occurred in the last hour."""
    cutoff = now - timedelta(hours=1)
    for r in records:
        if _get_event(r) != event_name:
            continue
        dt = _parse_timestamp(r)
        if dt is not None and dt >= cutoff:
            return True
    return False


# ---------------------------------------------------------------------------
# Alert ID management
# ---------------------------------------------------------------------------

def _next_alert_id(history_path: Path, today_str: str) -> str:
    """Return next sequential alert ID for today: ALT-YYYYMMDD-NNN."""
    max_seq = 0
    if history_path.exists():
        try:
            with history_path.open(encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    alert_id = rec.get("alert_id", "")
                    prefix = f"ALT-{today_str}-"
                    if alert_id.startswith(prefix):
                        try:
                            seq = int(alert_id[len(prefix):])
                            if seq > max_seq:
                                max_seq = seq
                        except ValueError:
                            pass
        except OSError:
            pass

    # Also check active-alerts.json for today's IDs
    active_path = OPS_ALERTS_DIR / "active-alerts.json"
    if active_path.exists():
        data = read_json(active_path)
        if data:
            for alert in data.get("alerts", []):
                alert_id = alert.get("id", "")
                prefix = f"ALT-{today_str}-"
                if alert_id.startswith(prefix):
                    try:
                        seq = int(alert_id[len(prefix):])
                        if seq > max_seq:
                            max_seq = seq
                    except ValueError:
                        pass

    next_seq = max_seq + 1
    return f"ALT-{today_str}-{next_seq:03d}"


# ---------------------------------------------------------------------------
# Alert evaluation
# ---------------------------------------------------------------------------

def _get_nested(data: dict, path: tuple) -> float | None:
    """Traverse nested dict by path tuple; return float value or None."""
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current is None:
        return None
    try:
        return float(current)
    except (TypeError, ValueError):
        return None


def evaluate_all_rules(
    summary: dict,
    job_records: list[dict],
    now: datetime,
) -> list[dict]:
    """Evaluate all 10 alert rules; return list of firing alert dicts (no id/started_at yet)."""
    firing = []
    today_str = now.strftime("%Y%m%d")

    # ── Threshold-based rules ─────────────────────────────────────────────
    for rule_id, metric_path, operator, threshold, severity, component, template in THRESHOLD_RULES:
        value = _get_nested(summary, metric_path)
        if value is None:
            log.warning("Rule %s: metric %s not found in summary — skipping", rule_id, metric_path)
            continue
        fires = (operator == "gt" and value > threshold) or (operator == "lt" and value < threshold)
        if fires:
            message = template.format(value=value, threshold=threshold)
            firing.append({
                "rule": rule_id,
                "severity": severity,
                "component": component,
                "message": message,
                "value": value,
                "threshold": threshold,
                "_source_key": None,  # used for source_down grouping
            })

    # ── data_stale_warn: freshness > 1 and <= 3 ──────────────────────────
    freshness = _get_nested(summary, DATA_FRESHNESS_PATH)
    if freshness is not None:
        if freshness > 3:
            firing.append({
                "rule": "data_stale_critical",
                "severity": "critical",
                "component": "data",
                "message": f"Data freshness {freshness:.1f} days — critically stale",
                "value": freshness,
                "threshold": 3.0,
                "_source_key": None,
            })
        elif freshness > 1:
            firing.append({
                "rule": "data_stale_warn",
                "severity": "warning",
                "component": "data",
                "message": f"Data freshness {freshness:.1f} days — stale",
                "value": freshness,
                "threshold": 1.0,
                "_source_key": None,
            })

    # ── training_failed: any training.failed event in last 1h ────────────
    if _has_event_in_last_hour(job_records, "training.failed", now):
        firing.append({
            "rule": "training_failed",
            "severity": "critical",
            "component": "training",
            "message": "Training job failed in the last hour",
            "value": 1.0,
            "threshold": 0.0,
            "_source_key": None,
        })

    # ── backtest_failed: any backtest.failed event in last 1h ────────────
    if _has_event_in_last_hour(job_records, "backtest.failed", now):
        firing.append({
            "rule": "backtest_failed",
            "severity": "warning",
            "component": "backtest",
            "message": "Backtest failed in the last hour",
            "value": 1.0,
            "threshold": 0.0,
            "_source_key": None,
        })

    # ── source_down: per-source error rate > 20% ─────────────────────────
    source_avail = summary.get("source_availability", {})
    if isinstance(source_avail, dict):
        for src_name, counts in source_avail.items():
            if not isinstance(counts, dict):
                continue
            ok = counts.get("ok", 0)
            empty = counts.get("empty", 0)
            error = counts.get("error", 0)
            total = ok + empty + error
            if total == 0:
                continue
            error_rate = error / total
            if error_rate > 0.2:
                pct = round(error_rate * 100, 1)
                firing.append({
                    "rule": "source_down",
                    "severity": "warning",
                    "component": "experience",
                    "message": f"Source '{src_name}' error rate {pct:.1f}% exceeds 20% threshold",
                    "value": pct,
                    "threshold": 20.0,
                    "_source_key": src_name,
                })

    return firing


# ---------------------------------------------------------------------------
# Merge logic: existing alerts + newly fired rules
# ---------------------------------------------------------------------------

def merge_alerts(
    existing_alerts: list[dict],
    firing: list[dict],
    history_path: Path,
    now: datetime,
) -> list[dict]:
    """Merge firing rules with existing alerts; append history on state changes."""
    today_str = now.strftime("%Y%m%d")
    now_iso = now.isoformat()

    # Build lookup: (rule, source_key) → existing active alert
    existing_active: dict[tuple, dict] = {}
    for alert in existing_alerts:
        if alert.get("status") == "active":
            key = (alert["rule"], alert.get("_source_key"))
            existing_active[key] = alert

    # Build set of currently firing keys
    firing_keys: set[tuple] = set()
    for f in firing:
        key = (f["rule"], f["_source_key"])
        firing_keys.add(key)

    merged: list[dict] = []

    # Process currently firing rules
    # Keep a counter for new alert IDs — we need a shared incrementing counter
    # across this run so multiple new alerts get unique IDs
    _id_counter = [0]  # mutable container for closure

    def _next_id() -> str:
        _id_counter[0] += 1
        # Start from current max and offset by counter
        # Re-read from existing alerts + history each time would be expensive;
        # instead, compute base once and add counter
        return f"ALT-{today_str}-{base_seq + _id_counter[0]:03d}"

    # Compute base sequence number once before loop
    base_seq = _compute_base_seq(history_path, OPS_ALERTS_DIR / "active-alerts.json", today_str)

    for f in firing:
        key = (f["rule"], f["_source_key"])
        if key in existing_active:
            # Already active — update value, keep id/started_at unchanged
            existing = dict(existing_active[key])
            existing["value"] = f["value"]
            existing["message"] = f["message"]
            existing["status"] = "active"
            # Remove internal key before writing
            existing.pop("_source_key", None)
            merged.append(existing)
        else:
            # New alert — assign id and started_at
            new_id = _next_id()
            alert = {
                "id": new_id,
                "severity": f["severity"],
                "rule": f["rule"],
                "message": f["message"],
                "component": f["component"],
                "started_at": now_iso,
                "value": f["value"],
                "threshold": f["threshold"],
                "status": "active",
            }
            merged.append(alert)
            # Append fire event to history
            history_rec = {
                "ts": now_iso,
                "event": "alert.fired",
                "alert_id": new_id,
                "rule": f["rule"],
                "severity": f["severity"],
                "message": f["message"],
            }
            append_jsonl(history_path, history_rec)
            log.info("Alert FIRED: %s [%s] %s", new_id, f["severity"], f["message"])

    # Process previously active alerts that are no longer firing → resolve
    for key, existing in existing_active.items():
        if key not in firing_keys:
            resolved = dict(existing)
            resolved["status"] = "resolved"
            resolved.pop("_source_key", None)
            merged.append(resolved)
            # Append resolve event to history
            history_rec = {
                "ts": now_iso,
                "event": "alert.resolved",
                "alert_id": existing.get("id", ""),
                "rule": existing["rule"],
            }
            append_jsonl(history_path, history_rec)
            log.info("Alert RESOLVED: %s %s", existing.get("id", ""), existing["rule"])

    # Also carry forward any previously resolved alerts (keep them in the list)
    resolved_existing = [a for a in existing_alerts if a.get("status") == "resolved"]
    for alert in resolved_existing:
        # Only include if not already in merged (i.e., not re-fired or re-resolved this run)
        key = (alert["rule"], alert.get("_source_key"))
        already_in_merged = any(
            m["rule"] == alert["rule"] and m.get("id") == alert.get("id")
            for m in merged
        )
        if not already_in_merged:
            a = dict(alert)
            a.pop("_source_key", None)
            merged.append(a)

    return merged


def _compute_base_seq(history_path: Path, active_path: Path, today_str: str) -> int:
    """Find the highest existing sequence number for today across history + active alerts."""
    max_seq = 0
    prefix = f"ALT-{today_str}-"

    if history_path.exists():
        try:
            with history_path.open(encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    alert_id = rec.get("alert_id", "")
                    if alert_id.startswith(prefix):
                        try:
                            seq = int(alert_id[len(prefix):])
                            if seq > max_seq:
                                max_seq = seq
                        except ValueError:
                            pass
        except OSError:
            pass

    if active_path.exists():
        data = read_json(active_path)
        if data:
            for alert in data.get("alerts", []):
                alert_id = alert.get("id", "")
                if alert_id.startswith(prefix):
                    try:
                        seq = int(alert_id[len(prefix):])
                        if seq > max_seq:
                            max_seq = seq
                    except ValueError:
                        pass

    return max_seq


# ---------------------------------------------------------------------------
# Daily digest writer
# ---------------------------------------------------------------------------

def write_daily_digest(merged_alerts: list[dict], now: datetime) -> None:
    date_str = now.strftime("%Y-%m-%d")
    digest_path = OPS_ALERTS_DIR / f"daily-digest-{date_str}.md"

    active = [a for a in merged_alerts if a.get("status") == "active"]
    resolved = [a for a in merged_alerts if a.get("status") == "resolved"]
    critical = [a for a in active if a.get("severity") == "critical"]
    warnings = [a for a in active if a.get("severity") == "warning"]

    lines = [
        f"# RITA Daily Alert Digest — {date_str}",
        "",
        f"Generated: {now.isoformat()}",
        "",
        "## Summary",
        f"- Active alerts: {len(active)}",
        f"- Critical: {len(critical)}",
        f"- Warnings: {len(warnings)}",
        f"- Resolved: {len(resolved)}",
        "",
    ]

    if active:
        lines.append("## Active Alerts")
        lines.append("")
        lines.append("| Rule | Severity | Component | Message | Since |")
        lines.append("|---|---|---|---|---|")
        for a in active:
            rule = a.get("rule", "")
            severity = a.get("severity", "")
            component = a.get("component", "")
            message = a.get("message", "").replace("|", "\\|")
            started_at = a.get("started_at", "")
            lines.append(f"| {rule} | {severity} | {component} | {message} | {started_at} |")
        lines.append("")

    if resolved:
        lines.append("## Resolved Alerts")
        lines.append("")
        lines.append("| Rule | Component | Message |")
        lines.append("|---|---|---|")
        for a in resolved:
            rule = a.get("rule", "")
            component = a.get("component", "")
            message = a.get("message", "").replace("|", "\\|")
            lines.append(f"| {rule} | {component} | {message} |")
        lines.append("")

    if not active and not resolved:
        lines.append("## No issues")
        lines.append("")
        lines.append("All systems nominal.")
        lines.append("")

    digest_path.parent.mkdir(parents=True, exist_ok=True)
    with digest_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    log.info("Wrote %s", digest_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    now = datetime.now(timezone.utc)

    log.info("Generating RITA alerts | %s", now.isoformat())

    # Ensure output directory exists
    OPS_ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Read metrics-summary.json ─────────────────────────────────────────
    summary_path = OPS_METRICS_DIR / "metrics-summary.json"
    summary = read_json(summary_path)
    if summary is None:
        log.warning("metrics-summary.json not found at %s — nothing to evaluate, exiting", summary_path)
        sys.exit(0)

    # ── Read jobs.jsonl ───────────────────────────────────────────────────
    jobs_path = LOG_DIR / "jobs.jsonl"
    job_records = read_jsonl(jobs_path)
    log.info("Loaded %d job records from %s", len(job_records), jobs_path)

    # ── Evaluate all 10 alert rules ───────────────────────────────────────
    firing = evaluate_all_rules(summary, job_records, now)
    log.info("Rules evaluated — %d firing", len(firing))

    # ── Load existing active-alerts.json ──────────────────────────────────
    active_alerts_path = OPS_ALERTS_DIR / "active-alerts.json"
    existing_data = read_json(active_alerts_path)
    existing_alerts: list[dict] = existing_data.get("alerts", []) if existing_data else []

    # Attach internal _source_key to existing alerts so merge logic can match source_down alerts
    for alert in existing_alerts:
        if alert.get("rule") == "source_down":
            # Extract source name from message: "Source 'X' error rate..."
            msg = alert.get("message", "")
            try:
                src = msg.split("'")[1]
            except IndexError:
                src = None
            alert["_source_key"] = src
        else:
            alert["_source_key"] = None

    # ── Merge alerts ──────────────────────────────────────────────────────
    history_path = OPS_ALERTS_DIR / "alert-history.jsonl"
    merged = merge_alerts(existing_alerts, firing, history_path, now)

    # ── Write active-alerts.json ──────────────────────────────────────────
    # Strip internal _source_key before writing
    clean_merged = []
    for a in merged:
        a_copy = dict(a)
        a_copy.pop("_source_key", None)
        clean_merged.append(a_copy)

    active_alerts_out = {
        "generated_at": now.isoformat(),
        "alerts": clean_merged,
    }
    write_json(active_alerts_path, active_alerts_out)

    # ── Write daily digest ────────────────────────────────────────────────
    write_daily_digest(clean_merged, now)

    active_count = sum(1 for a in clean_merged if a.get("status") == "active")
    resolved_count = sum(1 for a in clean_merged if a.get("status") == "resolved")
    log.info(
        "Done — %d active alerts, %d resolved, digest written",
        active_count,
        resolved_count,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Alert generator failed: %s", exc)
        sys.exit(1)
