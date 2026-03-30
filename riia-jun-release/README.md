# RITA Production Release (riia-jun-release)

This is the production application code for RITA (Risk Informed Trading Approach).
Built by Claude Cowork engineer agents, sprint by sprint.

## Structure

```
riia-jun-release/
├── src/rita/
│   ├── api/
│   │   ├── v1/system/      # Pure CRUD routers (positions, orders, snapshots)
│   │   ├── v1/workflow/    # Business process routers (train, backtest, evaluate)
│   │   └── bff/            # BFF aggregation routers (dashboard, fno, ops)
│   ├── services/           # Business logic (WorkflowService, ManoeuvreService, etc.)
│   ├── repositories/       # CSV access layer (one class per table, file locking)
│   ├── schemas/            # Pydantic models for all data contracts
│   ├── core/               # Pure calculation/ML logic (ported from POC)
│   ├── interfaces/         # Streamlit app, MCP server
│   └── config.py           # Pydantic Settings (validated at startup)
├── config/
│   ├── base.yaml
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── tests/
│   ├── unit/               # Unit tests (target: 200+ tests)
│   ├── integration/        # Integration tests (target: 30 tests)
│   └── e2e/                # End-to-end Playwright tests (target: 5 tests)
├── dashboard/
│   ├── js/rita/            # ES modules decomposed from rita.html
│   ├── js/fno/             # ES modules decomposed from fno.html
│   ├── js/ops/             # ES modules decomposed from ops.html
│   └── css/responsive.css  # Responsive breakpoints: 480/768/1100px
├── k8s/                    # Kubernetes manifests
└── docs/                   # Architecture Decision Records (ADRs)
```

## Source (POC)
`../poc/rita-cowork-demo` (local — not in this repo)

## Status
Built sprint-by-sprint — see `../PLAN_STATUS.md` and Confluence Sprint Boards for current progress.
