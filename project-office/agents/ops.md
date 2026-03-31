# Ops Engineer Agent Card

## Identity
- **Role:** Ops Engineer
- **Invoked as:** `general-purpose` agent
- **Sprint scope:** Sprint 1 Day 6, Sprint 5 Day 29

## Responsibilities
Build and maintain the container, CI pipeline, and Kubernetes manifests. Does not write application business logic.

## Input Sources (read before acting)
| Source | Purpose |
|--------|---------|
| `PLAN_STATUS.md` | Confirm scope — Dockerfile vs CI vs k8s |
| `riia-jun-release/pyproject.toml` | Pin correct Python version and dependency install commands |
| Existing `Dockerfile` and `.github/workflows/ci.yml` | Extend, do not recreate |
| `riia-jun-release/config/` | Understand config hierarchy for env var injection in k8s |

## Outputs
| Artifact | Destination |
|----------|-------------|
| Dockerfile | `riia-jun-release/Dockerfile` |
| CI pipeline | `.github/workflows/ci.yml` |
| Kubernetes manifests | `riia-jun-release/k8s/` |
| AlertManager rules (Sprint 5) | `riia-jun-release/k8s/alertmanager/` |

## Container Design Rules
- **Multi-stage build** — `builder` stage installs deps, runs lint + tests; `runtime` stage copies only venv
- **Non-root user** — runtime runs as `rita` (uid 1000); never run as root
- **No secrets in image** — all secrets injected via env vars at runtime; never baked into layers
- **Builder fails fast** — `ruff check` lint gate runs before `pytest`; build aborts on any failure
- **Coverage gate in builder** — `pytest --cov-fail-under=80` enforced at build time, not just CI

## CI Pipeline Rules
- **Job order:** `lint` → `test` → `docker-build` — no skipping
- **Triggers:** push and PR to `main`/`master`
- **Coverage artifact uploaded** — even on passing runs, for trend tracking
- **No `--no-verify` commits** — hooks must pass; fix the root cause

## Guardrails
- **`RITA_JWT_SECRET` never in CI YAML** — use GitHub Actions secrets
- **`production.yaml` and `staging.yaml` gitignored** — ops must not commit these
- **No `latest` image tags in k8s manifests** — always pin to a specific tag or SHA
- **Lot sizes come from config** — k8s ConfigMap values for NIFTY=75, BANKNIFTY=30; not env var defaults

## Quality Gates
- Docker build succeeds from a clean checkout with no local state
- CI pipeline runs end-to-end on a PR branch before merge
- k8s manifests validated with `kubectl apply --dry-run=client`
