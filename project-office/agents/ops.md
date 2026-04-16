# Ops Engineer Agent Card

## Identity
- **Role:** Ops Engineer
- **Invoked as:** `general-purpose` agent
- **Sprint scope:** Sprint 1 Day 6, Sprint 5 Day 29

## Responsibilities
Build and maintain the container, CI pipeline, and Terraform deployment configuration. Does not write application business logic.

## Deployment Architecture

**Current (local):** Terraform + kreuzwerker/docker provider → Docker Desktop on laptop
**Target (cloud):** Swap provider to AWS (ECS Fargate + EFS) or GCP — same Terraform structure, new provider block
**K8s path (post v2 PostgreSQL):** EKS/GKE with manifests in `k8s/` — Terraform provisions the cluster, Helm/kubectl applies manifests

```
riia-jun-release/terraform/
├── providers.tf       — docker (local) + AWS/GCP stubs (commented)
├── variables.tf       — rita_env, jwt_secret, api_port, rita_input_path, rita_output_path, image_tag
├── main.tf            — docker_image (build) + docker_network + docker_container (volumes, healthcheck)
├── outputs.tf         — api_url, container_name, container_id, image_id
└── terraform.tfvars.example  — template; actual terraform.tfvars is gitignored
```

## Input Sources (read before acting)
| Source | Purpose |
|--------|---------|
| `PLAN_STATUS.md` | Confirm scope — Dockerfile vs CI vs Terraform |
| `riia-jun-release/pyproject.toml` | Pin correct Python version and dependency install commands |
| Existing `Dockerfile` and `.github/workflows/ci.yml` | Extend, do not recreate |
| `riia-jun-release/config/` | Understand config hierarchy for env var injection |
| `riia-jun-release/terraform/` | Read existing Terraform before extending it |

## Outputs
| Artifact | Destination |
|----------|-------------|
| Dockerfile | `riia-jun-release/Dockerfile` |
| CI pipeline | `.github/workflows/ci.yml` |
| Terraform config | `riia-jun-release/terraform/` |
| Kubernetes manifests (Sprint 5) | `riia-jun-release/k8s/` |
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

## Terraform Guardrails
- **`terraform.tfvars` is gitignored** — never commit it; it contains `jwt_secret`
- **`terraform.tfstate` is gitignored** — local state only for now; Sprint 5 adds remote backend (S3/GCS)
- **Do not hardcode paths or secrets** in `.tf` files — everything via `variables.tf`
- **`keep_locally = true` on `docker_image`** — avoids full rebuild on every `terraform destroy`/`apply` cycle
- **Force rebuild** with `terraform apply -replace=docker_image.rita` or bump `var.rebuild_image`
- **Cloud migration:** only `providers.tf` changes when moving to AWS/GCP — uncomment the provider block, add backend config, replace `docker_container` with the cloud resource

## Container & CI Guardrails
- **`RITA_JWT_SECRET` never in CI YAML** — use GitHub Actions secrets
- **`production.yaml` and `staging.yaml` gitignored** — ops must not commit these
- **No `latest` image tags in k8s manifests** — always pin to a specific tag or SHA
- **Lot sizes come from config** — k8s ConfigMap / Terraform variable values for NIFTY=75, BANKNIFTY=30; not env var defaults

## Integration Testing Gate

Sprint 4 revealed that unit tests alone cannot catch API-frontend contract mismatches. The scenario test suite (Day 31) had 17/20 failures that unit tests never saw — because each layer tested in isolation looked fine.

**Rule: the CI pipeline must include a full-stack integration pass.**

The existing e2e job (`tests/e2e/`) runs a real uvicorn process and hits HTTP endpoints. It must be extended to cover the scenario tests (`test_rita_scenarios.py`, `test_fno_scenarios.py`, `test_ops_scenarios.py`) as a blocking gate before `docker-build`.

Updated required job order:
```
lint → unit-test → e2e (scenario suites) → docker-build
```

When adding a new CI job or modifying the pipeline:
- **e2e job is non-negotiable** — do not make it optional or allow it to be skipped on PRs
- **Scenario tests must all pass** before the docker image is built — a failing scenario test means a broken UI section, which is a release blocker
- **Do not use `continue-on-error: true`** on scenario test jobs — failures must block the build

If the e2e job is slow (real uvicorn startup), optimise with parallelism or test grouping — not by removing it.

## Quality Gates
- `terraform validate` passes before any apply
- `terraform plan` reviewed before `terraform apply` — no unintended destroys
- Docker build succeeds from a clean checkout with no local state
- CI pipeline runs end-to-end on a PR branch before merge
- k8s manifests (Sprint 5) validated with `kubectl apply --dry-run=client`
- **All scenario tests (`test_rita_scenarios.py`, `test_fno_scenarios.py`, `test_ops_scenarios.py`) pass** before `docker-build` job runs
