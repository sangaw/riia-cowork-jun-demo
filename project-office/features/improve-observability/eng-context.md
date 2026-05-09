# Improve Observability — Engineering Context Reference
# Pre-compiled from Observability_Requirements.md + survey findings
# Agents: read this instead of the full requirements doc.

## What this feature is

Add structured logging, local-file monitoring, and rule-based alerting across three projects:
- `riia-jun-release` — Python backend + JS dashboards (primary target)
- `riia-ai-org` — AgentOps pipeline (secondary)
- `rita-build-portfolio` — Mobile PWA (client-side only)

Two root problems being fixed:
1. **No functional metrics in logs** — logs are HTTP-structural only; no domain events
2. **Experience layer black box** — cannot tell if a blank panel is a DB miss, empty result, or an error

---

## New Files to Create

| File | Project | Purpose |
|---|---|---|
| `project-office/scripts/aggregate_ops_metrics.py` | riia-ai-org | Reads logs/*.jsonl, writes 3 JSON summary feeds |
| `project-office/scripts/generate_alerts.py` | riia-ai-org | Reads metrics-summary.json, writes active-alerts.json |
| `riia-jun-release/ops/metrics/metrics-summary.json` | riia-jun-release | Hourly/daily operational + functional rollups |
| `riia-jun-release/ops/metrics/functional-kpis.json` | riia-jun-release | 24h time-series for 5 KPIs |
| `riia-jun-release/ops/metrics/source-availability.json` | riia-jun-release | Per-source experience layer breakdown |
| `riia-jun-release/ops/alerts/active-alerts.json` | riia-jun-release | Active alert list (UI-readable) |
| `riia-jun-release/ops/alerts/alert-history.jsonl` | riia-jun-release | Append-only alert fire/resolve log |
| `riia-jun-release/ops/alerts/daily-digest-YYYY-MM-DD.md` | riia-jun-release | Nightly digest (generated, not checked in) |

---

## Files to Modify

### riia-jun-release Python

| File | Lines | Change |
|---|---|---|
| `src/rita/logging_config.py` | 25 | Add `configure_logging(log_level)` function; wire to structlog filter; add 4 JSONL RotatingFileHandler outputs |
| `src/rita/main.py` | startup | Call `configure_logging(settings.log_level)` |
| `src/rita/api/experience/rita.py` | all handlers | Add `experience.compose` provenance log per handler |
| `src/rita/api/experience/ds.py` | all handlers, 44, 52 | Add provenance log; replace bare `except: pass` |
| `src/rita/api/experience/ops.py` | all handlers | Add provenance log per handler |
| `src/rita/api/v1/portfolio.py` | 173, 220, 264, 296, 312, 385, 404 | Replace `except: pass` with `log_event(..., exc_info=True)` |
| `src/rita/api/v1/workflow/pipeline.py` | 44, 226 | Replace `except: pass` with `log_event(...)` |
| `src/rita/api/v1/system/training_runs.py` | 105, 118 | Replace `except: pass` with `log_event(...)` |
| `src/rita/core/drift_detector.py` | 210, 223 | Replace `except: pass` with `log_event(...)` |
| `src/rita/services/workflow_service.py` | after training/backtest resolve | Add `training.*` and `backtest.*` functional events |
| `src/rita/core/trading_env.py` | after trade execute | Add `trade.executed` functional event |
| `src/rita/api/v1/workflow/chat.py` | after classify | Add `chat.request` / `chat.response` events |
| `src/rita/main.py` | route registration | Add `POST /api/v1/client-error` endpoint |

### riia-jun-release JavaScript

| File | Change |
|---|---|
| `dashboard/js/rita/main.js` | Replace `.catch(() => {})` with shared `apiFetch()` wrapper; add `X-Request-ID` header |
| `dashboard/js/fno/main.js` | Same |
| `dashboard/js/ops/main.js` | Add `active-alerts.json` reader; add alert badge + panel; add source-availability chart; add functional-kpis chart |

### riia-ai-org

| File | Lines | Change |
|---|---|---|
| `agent-ops/aggregate_metrics.py` | 161, 178-179 | Replace `print()` with `logging.getLogger(__name__)` |
| `agent-ops/aggregate_metrics.py` | 140-141 | Replace silent `except Exception: commits = []` with `log.error(...)` |
| `agent-ops/aggregate_metrics.py` | 127-131 | Remove `stderr=subprocess.DEVNULL`; capture stderr on failure |
| `agent-ops/aggregate_metrics.py` | after aggregation | Add post-aggregation failure check → webhook/email if `overall_status == "fail"` |
| `agent-ops/shared/agentops.js` | header render | Add data freshness indicator (staleness > 24h → warning banner) |

### rita-build-portfolio

| File | Lines | Change |
|---|---|---|
| `android-mobile-app/index.html` | `<head>` | Add `window.onerror` + `unhandledrejection` global handlers |
| `android-mobile-app/index.html` | all fetch calls | Replace `.catch(() => {})` with shared `apiFetch()` wrapper |
| `android-mobile-app/sw.js` | install/activate/fetch | Add `.catch(err => console.error(...))` to all promise chains |

---

## Key Schemas

### log_event() wrapper (add to logging_config.py)
```python
from datetime import datetime
from rita.middleware import get_trace_id  # already exists

def log_event(logger, level: str, event: str, **kwargs):
    logger.bind(
        event=event,
        trace_id=get_trace_id(),
        timestamp=datetime.utcnow().isoformat() + "Z",
        **kwargs
    ).log(level, event)
```

### experience.compose event (logs/experience.jsonl)
```json
{
  "timestamp": "ISO8601",
  "trace_id": "uuid4",
  "event": "experience.compose",
  "handler": "get_dashboard_state",
  "instrument": "NIFTY",
  "duration_ms": 87,
  "overall_status": "ok | partial | error",
  "response_keys": ["portfolio", "signals"],
  "sources": {
    "<source_name>": {
      "status": "ok | empty | error",
      "record_count": 5,
      "duration_ms": 12,
      "error": "optional string"
    }
  }
}
```

### metrics-summary.json (ops/metrics/)
```json
{
  "generated_at": "ISO8601",
  "period": { "from": "ISO8601", "to": "ISO8601" },
  "operational": {
    "request_count": 0, "error_rate_pct": 0.0, "p95_latency_ms": 0,
    "top_failing_endpoints": [{ "endpoint": "", "error_count": 0 }],
    "background_job_failures": 0
  },
  "functional": {
    "training_success_rate_pct": 0.0, "backtest_success_rate_pct": 0.0,
    "chat_low_confidence_pct": 0.0, "drift_warn_count": 0, "drift_alert_count": 0,
    "data_freshness_days": 0.0,
    "experience_all_ok_pct": 0.0, "experience_partial_pct": 0.0, "experience_error_pct": 0.0
  },
  "source_availability": {
    "<source_name>": { "ok": 0, "empty": 0, "error": 0 }
  }
}
```

### active-alerts.json (ops/alerts/)
```json
{
  "generated_at": "ISO8601",
  "alerts": [{
    "id": "ALT-YYYYMMDD-NNN",
    "severity": "warning | critical",
    "rule": "string",
    "message": "string",
    "component": "string",
    "started_at": "ISO8601",
    "value": 0,
    "threshold": 0,
    "status": "active | resolved"
  }]
}
```

### apiFetch() wrapper (add to each dashboard JS)
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

---

## Alert Rules (generate_alerts.py)

| Rule constant | Check | Severity |
|---|---|---|
| `error_rate_high` | `error_rate_pct > 5` | critical |
| `latency_high` | `p95_latency_ms > 1500` | warning |
| `training_failed` | any training.failed in jobs.jsonl last 1h | critical |
| `backtest_failed` | any backtest.failed in jobs.jsonl last 1h | warning |
| `chat_low_confidence` | `chat_low_confidence_pct > 25` | warning |
| `data_stale_warn` | `data_freshness_days > 1` | warning |
| `data_stale_critical` | `data_freshness_days > 3` | critical |
| `experience_partial` | `experience_partial_pct > 10` | warning |
| `experience_error` | `experience_error_pct > 5` | critical |
| `source_down` | any source error count/total > 20% | warning |

---

## JSONL Log File Locations

```
riia-jun-release/logs/app.jsonl            ← API, service, core events
riia-jun-release/logs/experience.jsonl     ← experience.compose provenance events
riia-jun-release/logs/jobs.jsonl           ← training.*, backtest.*, drift.* events
riia-jun-release/logs/client-errors.jsonl  ← ingest from /api/v1/client-error
```

Rotation: 10 MB max, 7-day retention, `logging.handlers.RotatingFileHandler`.

---

## Rollout Sequence (for agent planning)

| Week | Steps | Focus |
|---|---|---|
| Week 1 | 1–6 | log_event wrapper, log level wiring, 4 JSONL files, provenance logs, silent-failure fixes, functional events |
| Week 2 | 7–10 | Aggregator script, Ops dashboard panels, Task Scheduler, /health enrichment |
| Week 3 | 11–19 | Alert generator, dashboard alert panel, daily digest, JS fetch wrapper, mobile PWA, client-error endpoint, riia-ai-org fixes |

---

## Out of Scope

- External services: Prometheus Alertmanager, Sentry, Datadog, Grafana, ELK, Loki
- User session / authentication tracking in logs
- Mobile PWA analytics or event tracking
- Changes to riia-ai-org `runs/` JSON schema or `schema.md`
- Log ingestion pipeline
