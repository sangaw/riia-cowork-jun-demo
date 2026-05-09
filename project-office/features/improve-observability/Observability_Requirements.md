# Observability Improvement Requirements
# Feature: Improve Logging, Monitoring & Alerting across RITA projects
# Scope: riia-jun-release (backend + dashboards), riia-ai-org (AgentOps), rita-build-portfolio (mobile PWA)
# Created: 2026-05-08

---

## Background — Two Root Problems

### Problem A: No functional metrics in logs
Current structlog output is structural only: `method`, `path`, `status_code`. There is no domain
signal — how many trades executed, what the backtest Sharpe was, how many signals fired, whether
the model produced a result or fell back. Logs confirm the HTTP plumbing worked; they say nothing
about whether RITA is doing its job.

### Problem B: Experience layer is a black box
`api/experience/` calls services, which call repositories, which hit SQLite. At any layer the chain
can return empty/null and the next layer silently accepts it. `api/experience/ds.py:44, 52` has bare
`except Exception: pass`. The `TraceIDMiddleware` logs that a request arrived and what HTTP status
left — it does not log what data actually came back. When a user sees a blank panel you cannot tell
if the DB query returned zero rows, the service returned `None`, or the experience layer serialised
an empty list.

---

## Section 1: Logging Improvements

### 1.1 Unified event schema

Every structured log event — backend, experience layer, background jobs — emits this shape.
All fields always present; domain fields are `null` when not applicable.

**`logs/app.jsonl` canonical event:**
```json
{
  "timestamp": "2026-05-08T09:14:00.123Z",
  "level": "info",
  "event": "trade.executed",
  "trace_id": "a1b2c3d4-...",
  "user_id": null,
  "endpoint": "/api/v1/trading/execute",
  "component": "trading_env",
  "status": "ok",
  "duration_ms": 42,
  "instrument": "NIFTY",
  "run_id": null,
  "intent": null,
  "low_confidence": false,
  "record_count": null,
  "freshness_days": null
}
```

`status` enum: `ok | empty | error | partial`

Implement as a thin wrapper in `src/rita/logging_config.py`:
```python
def log_event(logger, level: str, event: str, **kwargs):
    logger.bind(
        event=event,
        trace_id=get_trace_id(),
        timestamp=datetime.utcnow().isoformat() + "Z",
        **kwargs
    ).log(level, event)
```

### 1.2 Four rotating JSONL log files

Configure structlog to route output by component tag:

| File | Receives |
|---|---|
| `logs/app.jsonl` | All API, service, core events |
| `logs/experience.jsonl` | All `experience.*` provenance events |
| `logs/jobs.jsonl` | All `training.*`, `backtest.*`, `drift.*` background events |
| `logs/client-errors.jsonl` | Ingest from `/api/v1/client-error` endpoint |

Rotation: 10 MB max, keep 7 days. Use `logging.handlers.RotatingFileHandler` — no new dependencies.

### 1.3 Functional events

Add these at the service/core layer, not HTTP handlers. Goes to `logs/app.jsonl` or `logs/jobs.jsonl`.

```
training.submitted    component: workflow_service
training.running      component: workflow_service   fields: timestep, loss, ep_rew_mean
training.complete     component: workflow_service   fields: run_id, duration_ms, status
training.failed       component: workflow_service   fields: run_id, error

backtest.submitted    component: workflow_service
backtest.complete     component: workflow_service   fields: sharpe, max_drawdown, n_trades
backtest.failed       component: workflow_service   fields: run_id, error

chat.request          component: chat               fields: intent, low_confidence, duration_ms
chat.response         component: chat               fields: intent, confidence, response_ms

drift.check           component: drift_detector     fields: instrument, score, threshold, status

trade.executed        component: trading_env        fields: symbol, action, qty, price, portfolio_value
```

### 1.4 Experience provenance logging — directly solves Problem B

For every composed experience layer response, log which backend sources were queried and what
each returned. Goes to `logs/experience.jsonl`.

**Schema:**
```json
{
  "timestamp": "2026-05-08T09:14:00.123Z",
  "trace_id": "a1b2c3d4-...",
  "event": "experience.compose",
  "handler": "get_dashboard_state",
  "instrument": "NIFTY",
  "duration_ms": 87,
  "overall_status": "partial",
  "response_keys": ["portfolio", "signals", "performance"],
  "sources": {
    "training_runs":  { "status": "ok",    "record_count": 5,  "duration_ms": 12 },
    "backtest_runs":  { "status": "empty", "record_count": 0,  "duration_ms": 8  },
    "trade_journal":  { "status": "ok",    "record_count": 23, "duration_ms": 15 },
    "audit_log":      { "status": "error", "record_count": 0,  "duration_ms": 3,
                        "error": "query timeout" }
  }
}
```

`overall_status` derivation:
- `ok` if all sources ok
- `partial` if at least one source ok and at least one empty/error
- `error` if all sources empty or error

Implementation pattern:
```python
sources = {}
t0 = time.monotonic()

try:
    runs = repo.get_training_runs(instrument)
    sources["training_runs"] = {
        "status": "ok" if runs else "empty",
        "record_count": len(runs),
        "duration_ms": int((time.monotonic() - t0) * 1000),
    }
except Exception as exc:
    sources["training_runs"] = {
        "status": "error", "record_count": 0,
        "duration_ms": int((time.monotonic() - t0) * 1000),
        "error": str(exc),
    }

# repeat for each source ...

statuses = [s["status"] for s in sources.values()]
if all(s == "ok" for s in statuses):
    overall = "ok"
elif any(s == "ok" for s in statuses):
    overall = "partial"
else:
    overall = "error"

log_event(log, "info", "experience.compose",
    handler="get_dashboard_state",
    instrument=instrument,
    overall_status=overall,
    sources=sources,
    response_keys=list(response.keys()),
    duration_ms=int((time.monotonic() - start) * 1000),
)
```

### 1.5 Client-to-API trace correlation

Add a shared fetch wrapper to every dashboard JS and the mobile PWA:

```javascript
const SESSION_TRACE_ID = crypto.randomUUID();

async function apiFetch(url, opts = {}) {
    try {
        const res = await fetch(url, {
            ...opts,
            headers: { ...opts.headers, 'X-Request-ID': SESSION_TRACE_ID }
        });
        if (!res.ok) console.error('[RITA] fetch error', url, res.status, SESSION_TRACE_ID);
        return res.ok ? res.json() : null;
    } catch (e) {
        console.error('[RITA] fetch failed', url, e, SESSION_TRACE_ID);
        return null;
    }
}
```

`TraceIDMiddleware` already reads `X-Request-ID` — this links UI and backend logs by the same ID.

### 1.6 Global JS error capture (mobile PWA)

Add to `android-mobile-app/index.html` `<head>` before all other scripts:

```javascript
window.addEventListener('unhandledrejection', e => {
    console.error('[RITA] Unhandled rejection', e.reason);
});
window.onerror = (msg, src, line, col, err) => {
    console.error('[RITA] JS error', { msg, src, line, stack: err?.stack });
};
```

### 1.7 Service worker error logging

Add `.catch()` to all promise chains in `sw.js`:

```javascript
self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE)
            .then(c => c.addAll(ASSETS))
            .catch(err => console.error('[SW] cache install failed', err))
    );
});

self.addEventListener('fetch', e => {
    e.respondWith(
        caches.match(e.request)
            .then(cached => cached || fetch(e.request))
            .catch(err => { console.error('[SW] fetch failed', e.request.url, err); })
    );
});
```

### 1.8 Wire config log level to structlog

**File:** `src/rita/logging_config.py:25` — currently hardcoded to `logging.INFO`.
`ServerSettings.log_level` is loaded from YAML but never applied.

Fix:
```python
def configure_logging(log_level: str = "info") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        ...
    )
```

Call from `main.py` startup: `configure_logging(settings.log_level)`.

### 1.9 Replace all silent except: pass with log.error

**Files and locations requiring fixes:**

| File | Lines | Fix |
|---|---|---|
| `api/v1/portfolio.py` | 173, 220, 264, 296, 312, 385, 404 | `log_event(log, "error", "portfolio.<name>.failed", exc_info=True)` |
| `api/experience/ds.py` | 44, 52 | `log_event(log, "error", "experience.ds.<name>.failed", exc_info=True)` |
| `api/v1/workflow/pipeline.py` | 44, 226 | `log_event(log, "error", "pipeline.<name>.failed", exc_info=True)` |
| `core/drift_detector.py` | 210, 223 | `log_event(log, "warning", "drift.check.failed", exc_info=True)` |
| `api/v1/system/training_runs.py` | 105, 118 | `log_event(log, "error", "training_runs.<name>.failed", exc_info=True)` |

### 1.10 riia-ai-org: Replace print() with logging module

**File:** `agent-ops/aggregate_metrics.py`

```python
import logging
log = logging.getLogger(__name__)

# Replace print("OK: metrics.json written..."):
log.info("metrics.aggregated", extra={"runs": len(runs), "output": str(output_path)})

# Replace silent git subprocess catch:
except Exception as exc:
    log.error("git.log.failed", extra={"skill_file": str(path), "error": str(exc)})
    commits = []
```

---

## Section 2: Monitoring

### 2.1 Local aggregator script

**New file:** `project-office/scripts/aggregate_ops_metrics.py`

Reads all four JSONL files and writes three JSON summary files. Run on a schedule (Windows Task
Scheduler, every 5 minutes) or triggered post-deployment.

Outputs:
```
riia-jun-release/ops/metrics/metrics-summary.json      ← hourly/daily rollups
riia-jun-release/ops/metrics/functional-kpis.json      ← domain KPI time series
riia-jun-release/ops/metrics/source-availability.json  ← per-source experience breakdown
```

### 2.2 metrics-summary.json schema

```json
{
  "generated_at": "2026-05-08T10:00:00Z",
  "period": {
    "from": "2026-05-08T09:00:00Z",
    "to":   "2026-05-08T10:00:00Z"
  },
  "operational": {
    "request_count": 450,
    "error_rate_pct": 2.1,
    "p95_latency_ms": 340,
    "top_failing_endpoints": [
      { "endpoint": "/api/v1/portfolio/summary", "error_count": 7 },
      { "endpoint": "/api/v1/backtest/run",      "error_count": 3 }
    ],
    "background_job_failures": 1
  },
  "functional": {
    "training_success_rate_pct": 100,
    "backtest_success_rate_pct": 80,
    "chat_low_confidence_pct": 8.3,
    "drift_warn_count": 0,
    "drift_alert_count": 0,
    "data_freshness_days": 0.5,
    "experience_all_ok_pct": 87,
    "experience_partial_pct": 11,
    "experience_error_pct": 2
  },
  "source_availability": {
    "training_runs":  { "ok": 92, "empty": 6, "error": 2 },
    "backtest_runs":  { "ok": 78, "empty": 20, "error": 2 },
    "trade_journal":  { "ok": 98, "empty": 2,  "error": 0 },
    "audit_log":      { "ok": 95, "empty": 4,  "error": 1 }
  }
}
```

### 2.3 functional-kpis.json schema

24 hourly data points per metric, feeds line charts in Ops dashboard:

```json
{
  "generated_at": "2026-05-08T10:00:00Z",
  "series": {
    "chat_low_confidence_pct":  [{ "t": "2026-05-08T09:00:00Z", "v": 8.3 }, ...],
    "experience_partial_pct":   [{ "t": "...", "v": 11 }, ...],
    "backtest_sharpe_last":     [{ "t": "...", "v": 1.42 }, ...],
    "data_freshness_days":      [{ "t": "...", "v": 0.5 }, ...],
    "error_rate_pct":           [{ "t": "...", "v": 2.1 }, ...]
  }
}
```

### 2.4 /health endpoint enrichment

Extend existing `/health` response (`main.py:347–449`) with:

```json
{
  "experience_layer": {
    "empty_response_rate_1h_pct": 11,
    "last_functional_event": "2026-05-08T09:58:00Z"
  },
  "log_level_active": "info"
}
```

### 2.5 Ops dashboard additions

Two new panels in the existing Ops dashboard:

1. **Experience Source Availability** — stacked bar per source (training_runs, backtest_runs,
   trade_journal, audit_log) showing ok/empty/error breakdown. Reads `source-availability.json`.
2. **Functional KPI Trends** — 24h sparklines for 5 key metrics. Reads `functional-kpis.json`.

### 2.6 riia-ai-org: Data freshness indicator

**File:** `riia-ai-org/agent-ops/shared/agentops.js`

Compute `(now - metrics.generated_at)` in minutes and display in dashboard header. Show warning
banner if staleness > 24 hours. The `generated_at` field already exists in `metrics.json`.

### 2.7 /api/v1/client-error ingest endpoint

New endpoint receives JS errors from all three frontends:

```
POST /api/v1/client-error
Body: {
  "type": "js_error | fetch_failure | sw_error | unhandled_rejection",
  "message": "string",
  "stack": "string | null",
  "url": "string",
  "trace_id": "string"
}
```

Writes to `logs/client-errors.jsonl` via `log_event(log, "error", "client.error", ...)`.
Client-side crashes appear in the same log stream as backend errors, correlated by `trace_id`.

---

## Section 3: Alerting

### 3.1 Alert generator script

**New file:** `project-office/scripts/generate_alerts.py`

Reads `metrics-summary.json` and checks rules below. Writes:
```
riia-jun-release/ops/alerts/active-alerts.json    ← current active alerts
riia-jun-release/ops/alerts/alert-history.jsonl   ← append-only fire/resolve log
```

### 3.2 active-alerts.json schema

```json
{
  "generated_at": "2026-05-08T10:00:00Z",
  "alerts": [
    {
      "id": "ALT-20260508-001",
      "severity": "warning",
      "rule": "experience_partial_rate_high",
      "message": "Experience partial-response rate 11% exceeds threshold 10%",
      "component": "experience_layer",
      "started_at": "2026-05-08T09:45:00Z",
      "value": 11,
      "threshold": 10,
      "status": "active"
    }
  ]
}
```

`severity` enum: `warning | critical`
`status` enum: `active | resolved`

### 3.3 Alert rules

| Rule | Condition | Severity | Source field |
|---|---|---|---|
| `error_rate_high` | `error_rate_pct > 5` over 15 min | critical | operational.error_rate_pct |
| `latency_high` | `p95_latency_ms > 1500` for 15 min | warning | operational.p95_latency_ms |
| `training_failed` | any `training.failed` event in last hour | critical | jobs.jsonl |
| `backtest_failed` | any `backtest.failed` event in last hour | warning | jobs.jsonl |
| `chat_low_confidence` | `chat_low_confidence_pct > 25` rolling 30 min | warning | functional.chat_low_confidence_pct |
| `data_stale_warn` | `data_freshness_days > 1` | warning | functional.data_freshness_days |
| `data_stale_critical` | `data_freshness_days > 3` | critical | functional.data_freshness_days |
| `experience_partial` | `experience_partial_pct > 10` | warning | functional.experience_partial_pct |
| `experience_error` | `experience_error_pct > 5` | critical | functional.experience_error_pct |
| `source_down` | any single source `error > 20%` | warning | source_availability.* |

### 3.4 Daily digest

**File:** `riia-jun-release/ops/alerts/daily-digest-YYYY-MM-DD.md`

Generated nightly. Fixed sections:
```
# RITA Daily Digest — YYYY-MM-DD

## Summary
- Requests: N | Errors: X% | p95: Xms
- Training runs: N complete, N failed
- Backtests: N complete, N failed (run IDs listed)
- Chat low-confidence: X% (within/exceeds threshold)
- Data freshness: X days (ok/warn/critical)

## Experience Layer
- All-sources-ok: X% of responses
- Partial responses: X% — <most frequent empty source> empty most frequently
- Errors: X%

## Alerts Fired
- List with start/resolve times

## What Changed vs Yesterday
- KPIs that moved > 20% vs previous digest
```

### 3.5 Ops dashboard alert panel

Add to existing Ops dashboard:
- Alert badge in header: count of active critical/warning alerts
- Alert panel: reads `active-alerts.json`; shows severity badge, rule, message, duration

---

## Rollout Sequence

### Week 1 — Schema + provenance logging (stop the guesswork)
1. Implement `log_event()` wrapper + unified schema in `logging_config.py`
2. Wire `settings.log_level` to structlog filter
3. Configure 4 rotating JSONL output files
4. Add `experience.compose` provenance log to all experience handlers
5. Replace all silent `except: pass` in `portfolio.py`, `ds.py`, `pipeline.py`
6. Add functional events: `training.*`, `backtest.*`, `chat.*`, `drift.*`

### Week 2 — Local aggregator + monitoring
7. Write `aggregate_ops_metrics.py` → 3 JSON outputs
8. Add two new Ops dashboard panels (source availability + functional KPI trends)
9. Schedule aggregator (Windows Task Scheduler, every 5 min)
10. Enrich `/health` with experience layer fields

### Week 3 — Alerting + client fixes
11. Write `generate_alerts.py` → `active-alerts.json` + `alert-history.jsonl`
12. Wire Ops dashboard to read `active-alerts.json` (badge + panel)
13. Add daily digest generator
14. Add `X-Request-ID` to JS fetch wrapper (all 3 dashboards + mobile PWA)
15. Add `window.onerror` + `unhandledrejection` to mobile PWA
16. Add `/api/v1/client-error` endpoint → `logs/client-errors.jsonl`
17. Fix service worker (`sw.js`) error handlers
18. Replace `print()` with `logging` in `riia-ai-org/agent-ops/aggregate_metrics.py`
19. Add run-failure webhook to `aggregate_metrics.py` post-aggregation check

---

## Out of Scope

- External monitoring services (Prometheus Alertmanager, Sentry, Datadog, Grafana)
- Authentication/user session tracking (no user IDs in logs unless added later)
- Mobile PWA analytics / event tracking
- riia-ai-org run log schema changes (schema.md stays as-is)
- Log ingestion pipeline (ELK, Loki, etc.)
