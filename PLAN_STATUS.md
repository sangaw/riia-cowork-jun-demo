# RITA Production Refactor — Daily Status
**Last updated:** 2026-05-30 (EOD) — Feature 26 Phase 3 My Portfolio CSS fix + auth redirect fix deployed (c95eb81). GitHub Actions triggered — verify green at next session start.

**Session work (2026-05-30) — Feature 26 User Portfolio Store:**
- **Phase 1 — Backend data layer COMPLETE.** `UserPortfolioKeyModel`, `UserPortfolioModel`, `UserPortfolioKeyRepo`, `UserPortfolioRepo`, `UserPortfolioService` (save/get, soft-replace), Alembic migration `20260530_add_user_portfolio_tables`, schemas (`HoldingItem`, `UserPortfolioCreate`, `UserPortfolioOut`). Merged dev `bc0074f` (merge `f963914`).
- **Phase 2 — API endpoints + auth state param COMPLETE.** `POST /api/v1/user-portfolio` (201, JWT), `GET /api/v1/user-portfolio`, `GET /api/v1/experience/user-portfolio` (read-only). Auth: `state` param on Google login/callback — `state=fno` → `fno.html`, else → `index.html`. 22 QA tests pass. Merged dev `4bd0dc9` (merge `0fbae57`).
- **Phase 3 — RITA frontend My Portfolio builder COMPLETE.** `dashboard/js/rita/my-portfolio.js` (allocation builder, 100% enforcer, save/pre-populate). Token ingestion `?token=` → `sessionStorage` + `history.replaceState()` in `main.js`. `localStorage` → `sessionStorage` migration: `shared/api.js`, `index.html`, `users/main.js`, `ds.html`. "My Portfolio" nav + `sec-my-portfolio` in `rita.html`. Disclaimer updated. Code Review CONDITIONAL (advisory: `portfolio_id` unused in JS). Merged dev `3dd19a5` (merge `1bfb333`).
- **Prod deploy pushed:** `9700171` → `san-work-ravionics/riia-jun-release-prod`. **⚠ Actions status: pending.** At next session start: (1) confirm GitHub Actions green, (2) run `docker exec rita python -m alembic upgrade head` on EC2 if migration not auto-applied, (3) verify `https://riia.ravionics.nl/health`, (4) test My Portfolio section on RITA dashboard.
- **My Portfolio bug fixes deployed:** `c95eb81` — CSS (mp-* block) + auth redirect fix (raw fetch on load, gate on Save only). GitHub Actions pending — verify green at next session start.
- **Phase 4 pending:** FnO auth gate (entire app behind Google Sign-in) + FnO "My Portfolio" nav item. Start next session with `/enhance fno "Feature 26 Phase 4"`.

**Next session checklist:**
1. Verify GitHub Actions green — https://github.com/san-work-ravionics/riia-jun-release-prod/actions (commit `c95eb81`)
2. Health check — https://riia.ravionics.nl/health → `{"status": "ok"}`
3. Test My Portfolio on RITA dashboard — confirm CSS renders + no Google auth redirect on load
4. Log deploy `c95eb81` in `project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md` (Phase 7)
5. Run `docker exec rita python -m alembic upgrade head` on EC2 if not already applied (for Feature 26 Phase 1 migration)
6. Start Phase 4: `/enhance fno "Feature 26 Phase 4"`
- **data_refresh fixes (earlier today):** NIFTY/BANKNIFTY incremental CSV append + SKIP_INSTRUMENTS constant + ATHER skip guard. Deployed `b48d25e`. All 11 instruments refreshed.

**Session work (2026-05-24):**
- **Functional KPIs panel fixed:** `functional-kpis.js` was fetching from a stale static JSON file (`/ops/metrics/functional-kpis.json`, last generated 2026-05-08). Replaced with live `GET /api/experience/ops/functional-kpis` endpoint that computes training success rate, error rates, and p95 latency from `api_call_log` and `training_runs` tables per hourly bucket. New `FunctionalKPIsResponse`/`FunctionalKPIsSeries` Pydantic schemas added (`src/rita/schemas/functional_kpis.py`).
- **API Metrics panel fixed (3 bugs):** (1) `api-metrics` missing from `SECTIONS` array in `nav.js` — section was never shown on nav click; (2) `sec-api-metrics` had inline `style="display:none"` overriding `.sec.on { display:block }` CSS rule due to specificity; (3) HTML used non-existent CSS classes (`kpi-row`, `kpi-card`, `data-table`) — replaced with ops design system classes (`kpi-strip`, `kpi`, `kpi-ey`, `kpi-val`, `tbl-wrap`).
- **29 unit tests added** in `tests/unit/test_functional_kpis.py` — 3 test classes covering schema validation, endpoint happy path + edge cases, and JS contract verification.
- **Deployed to production** — commit `7b30b73`, GitHub Actions green, health check passed at `https://riia.ravionics.nl/health`.
- **Feedback saved:** Engineer agents generate invalid CSS class names in `ops.html`; Architect prompts must specify exact ops design system classes going forward.

**Previous session (2026-05-23):**
- **SSH key mismatch fixed:** `SSH_PRIVATE_KEY` GitHub secret was stale; updated via GitHub API (PyNaCl) to match `terraform/generated-key.pem`
- **Swap added:** EC2 t3.micro now has 2GB swap — prevents OOM kills during `docker pull`
- **Chat monitor write path:** `chat_monitor.py` was writing to read-only `/app/data` volume; `chat.monitor_dir` config key added pointing to writable `rita_output/`
- **Instrument seeding bug fixed:** SQLite `IN :ids` tuple binding raised `OperationalError` on every startup — entire seed block skipped, instruments table empty, geography panel blank. Fixed with per-id UPDATE loop
- **Deploy pipeline refactored:** single long SSH heredoc replaced with 3 short calls (pull / `docker run -d` / HTTP health poll from runner) — no session lives long enough to be OOM-killed
- **CloudWatch Logs + alarms:** `awslogs` Docker log driver → `/rita/app` log group; 2 alarms (CPU >80%, status check fail) + SNS email to contact@ravionics.nl; IAM role `rita-ec2-role` attached to EC2; Terraform IaC added
- **Docker image 9.4 GB → ~2 GB:** `sentence-transformers` was pulling full NVIDIA CUDA stack via PyTorch; pre-install CPU-only torch with `--extra-index-url https://download.pytorch.org/whl/cpu`
- **SPEC_Prod_Deploy.md updated:** 6 new failure rows, Observability section, EC2 setup checklist, disk cleanup procedure
- Geography panel verified live: India 5 / US 4 / EU 4 instruments

**Previous session (2026-05-21 session 3) — Production outage — accidental `terraform destroy`** ran from inside `terraform/` directory; entire EC2 infrastructure destroyed mid-day
- Recovery: `terraform state rm` for gone resources → `terraform destroy` (VPC cleanup) → `terraform apply` → data re-upload via SCP → GitHub Actions deploy → nginx manual setup → site restored (~45 min)
- **Infra fix:** nginx reverse-proxy config baked into `terraform/main.tf` `user_data` — future rebuilds include nginx automatically (commit `8ea39ce`)
- **Instrument seed fix:** original 4 instruments (NIFTY, BANKNIFTY, NVIDIA, ASML) were seeded with `is_available=False`; TRU missing from seed entirely → production showed only 7/8 instruments instead of 13. Fixed: all set to `True`, TRU added, startup SQL UPDATE corrects existing DBs on next restart (commit `1113c2e`)
- **Feature 17 COMPLETE:** Cloudflare DNS migration done; `riia.ravionics.nl` A record added (Proxied/orange cloud); SSL/TLS mode set to Flexible → `https://riia.ravionics.nl` live with Cloudflare-managed SSL. No certbot needed.
- Cloudflare lesson: `ravionics.nl` and `www` records must stay DNS only (grey cloud) — proxying them broke the Strato-hosted main site

**Previous session (2026-05-21 session 1):**
- Bug fix: applied Alembic migration `20260520_add_yf_ticker` — column was missing, causing all instrument queries to fail silently
- main.py seed: all 12 `_SEED_INSTRUMENTS` entries now include `yf_ticker=` values; one-time startup backfill
- Geography panel redesign: tiles replace instrument tab selector; region labels India / United States / Europe; ATHER excluded (no yfinance data)
- Pushed to prod: `e920177..bf59163` (7 commits)

**Session work (2026-05-25) — continued:**
- **Bug fix: users.html nav** — Chat Analytics and FnO Daily Ops items were missing from the left sidebar when navigating to User Traffic page (`dashboard/users.html`). Root cause: `users.html` is a separate page with its own nav that omitted those two items. Fix: added both items with `href="ops.html#chat"` and `href="ops.html#dailyops"` links. Commits: `16fa9a2`, `70c5008`.
- **Bug fix: Agent Builds run gap** — Strategy Comparison `/enhance` run `20260525-1559` was in `riia-ai-org/agent-ops/runs/` (gitignored) but not in `riia-jun-release/data/agent-ops/runs/` — deploy pipeline never seeded it to production DB. Copied run JSON into prod repo; production Agent Builds page now shows the run.
- **Production deploy** — `0e0f032` pushed to `san-work-ravionics/riia-jun-release-prod`; GitHub Actions green; health check passed at `https://riia.ravionics.nl/health`.

**Session work (2026-05-25):**
- **Strategy Comparison analysis (ASML 2025):** Standalone script `project-office/scripts/strategy_checks_asml.py` written and validated against ASML 2025 data (255 trading days). Results: B&H +34.8% (MDD 26.3%), Value Investing +18.5% (best risk-adjusted: Sharpe 1.25, MDD 7.3%), Swing Trading +29.2%, SR-52W +25.0%, Momentum +12.3% (worst — choppy Jan–Apr whipsawed SMA crossover). Value Investing only strategy within both risk targets (Sharpe > 1.0, MDD < 10%).
- **Feature 16 (May) — Strategy Comparison COMPLETE.** Spec: `project-office/features/May/16 Strategy Comparison/REQUIREMENTS.md`. Delivered: experience endpoint `GET /api/v1/experience/rita/strategy-comparison`, commentary handler `("rita","strategy-comparison")`, `strategy-comparison.js` with 7 Chart.js panels (portfolio growth full-width, 3 horizontal + 3 vertical metric bars), instrument pills with active highlight, year toggle (2025/2026), summary metrics table, 39 unit tests (contract verified 14/14 fields). Deployed to production at `https://riia.ravionics.nl`.

**Session work (2026-05-26) — bug fixes (EOD):**
- **MCP calls timestamp format fixed (DS app):** Raw Python datetime string `2026-05-26 19:05:39.300802` was rendered verbatim in the Recent MCP Calls table. Added `fmtDT()` EU formatter to `dashboard/js/ds/utils.js`; added `fmt` column callback support to `mkTbl()`; applied to Time column in `mcp.js`. Output: `26-May-2026 07:05:39 PM`. Commits `a50dd05` (prod deployed).
- **Investor onboarding flow v2 fixed:** (1) Selecting 1yr (short) in Step 1 now auto-selects "Next Purchase" tile in Step 2; selecting 5yr auto-selects Education; selecting 10y+ auto-selects Retirement. (2) `SLIDER_STOPS.short` labels changed from Q1/Q2/Q3/Q4 to 3m/6m/9m/12m. (3) `SLIDER_STOPS.long` changed from 4 stops [5y,10y,15y,20y] to 5 stops [3y,6y,9y,12y,15y]. Added `INVESTOR_TO_GOAL` map + `selectGoal()` to Card 1 click handler. Commit `2b2be01` (prod deployed).
- **Production deploy:** Both fixes pushed to `san-work-ravionics/riia-jun-release-prod`; GitHub Actions triggered.

**Session work (2026-05-26) — ops deploy:**
- **Production deploy unblocked:** GitHub Actions runner queue frozen (stuck re-run in pre-queue limbo for 1+ hr — PATTERN-011). EC2 disk at 95% (9 stale ~2.89 GB images). Manual fix: SSH → `docker image prune -af` → disk 95% → 26%. Deployed Feature 17 via EC2 local build (~28 min): torch install → venv COPY → layer export → container swap. Health check passed `{"status":"ok"}`. Mobile UA → `/` → HTTP 302 → `/mobile` verified.
- **deploy.yaml hardened:** New "Free EC2 disk space" step (stop → rm → prune) runs BEFORE `docker pull` on every future deploy. `workflow_dispatch` trigger added for manual runs.
- **Ops skill + SPEC updated:** EC2 Local Build emergency procedure + GitHub Actions frozen queue recovery added to `skill-ops-engineer.md`, `SPEC_Prod_Deploy.md`, and `DEPLOYMENT_KNOWLEDGE.md` (PATTERN-011).
- **Commits pushed to prod:** `d043def` (Feature 17 + disk fix), `c749f75` (webhook nudge), `1a0f65b` (workflow_dispatch).

**Session work (2026-05-27):**
- **Feature 25 ASML Equity Hedge Scenarios — continuation COMPLETE.** QA + documentation completion pass: 14 unit tests written and confirmed passing (`tests/unit/test_equity_hedge.py` — happy path + edge cases for < 5 trading days + zero-vol fallback). API-frontend contract verified (26 response fields, 0 mismatches). Feature 25 PLAN_STATUS.md updated to `[x] Complete`. Confluence Engineering page v34→v35. Merged at `405d7cf`. 2 aggregate_metrics alerts flagged (FC-HTML-CSS from prior ops run; CSAT 2.67/5 recent — run `/agent-performance-improvements`).
- **Feature 14 i18n Phase 2 Run A COMPLETE.** t() wired into all 12 remaining RITA+FnO section loaders: agent-panel.js, ai-compliance.js, technical-analysis.js, learnings.js (RITA) and positions.js, margin.js, greeks.js, hedge.js, manoeuvre.js, payoff.js, rr.js, stress.js (FnO). ~180 new locale keys added across en/nl/fr (411 total keys per file, parity confirmed). Locale key parity verified by 93 QA tests (test_i18n_locale_parity.py). Code Review: CONDITIONAL — 6 advisory call-site fixes (status/kpi keys already in locale files; deferred to follow-up commit). Confluence Engineering page v32→v33. Merged at 6460d9d (feat commit ba69cc3).

**Session work (2026-05-26) — continued:**
- **Feature 17 (May) — Mobile Device UI COMPLETE (code).** Phase 0: gateway hub page at `riia-jun-release/mobileapp/gateway.html`, `GET /mobile` route in `main.py` (commit `966d21f`). Phase 1: UA detection added to `root()` (`_MOBILE_UA_RE` regex, `re.IGNORECASE`), inline IIFE mobile-detect `<script>` inserted into `<head>` of all 5 desktop dashboards (`rita.html`, `fno.html`, `ops.html`, `ds.html`, `investgame.html`) with correct APPNAME tokens and `?desktop=1`/`sessionStorage.mobileBypass` bypass (commits `3c92cda`, `e954899`, merge `8a481ef`). 6 unit tests in `tests/unit/test_mobile_detection.py` — all passing. `Spec_Mobile_App.md` Section 8 added. `Spec_RITA_App.md` `GET /` entry updated. Deployed to production 2026-05-27; browser test on real mobile device complete.

**Session work (2026-05-26):**
- **Feature 18 (May) — Skill-Based Approach Revision COMPLETE.** Full implementation in single session: (1) Three-tier guardrail hierarchy — 8 files in `project-office/guardrails/` (org + project + 6 roles); (2) CLAUDE.md refactored to pure navigation map — "What NOT to Do" and API routing table removed, references guardrail files; (3) 12 skill files stamped with guardrail refs + last-validated date; 8 slash commands converted to thin wrappers (15 lines each, load guardrails → load skill); `codebase-constraints.md` deprecated; (4) Review agent upgraded — Design Review gate (post-Architect) + Code Review gate (post-Engineer) wired into `/enhance`; task brief template updated with both reviewer sections; (5) Feature folder template created (`TEMPLATE/REQUIREMENTS.md`, `PLAN_STATUS.md`, `eng-context.md`); skill drift detection added to `skill-end-of-day.md` (Step 4); `/enhance` Step 1 auto-creates feature folder. (6) Ops drift widget API tier gap closed — new `GET /api/experience/ops/drift` experience endpoint; `observability.js` updated from `/api/v1/drift`; spec + guardrails updated.

**Pending:**
- ~~**Feature 17 (May) — Mobile Device UI:**~~ ✅ FULLY DEPLOYED 2026-05-26 — EC2 local build (commit `d043def`); mobile UA redirect verified live; ops docs updated.
- ~~**Feature 16 (May) — Strategy Comparison:**~~ ✅ COMPLETE — merged to master, deployed to production 2026-05-25.
- ~~**Feature 18 (May) — Skill-Based Approach Revision:**~~ ✅ COMPLETE — 2026-05-26.
- ~~**Feature 14 i18n Phase 2 Run A:**~~ ✅ COMPLETE — 12 JS loaders wired, 411 keys × 3 locales, merged 6460d9d (2026-05-27).
- ~~**Feature 14 i18n Phase 2 Run B:**~~ ✅ COMPLETE — 35 ops.* keys added (446 total, parity confirmed). Deployed 2026-05-30 (907958d).
- ~~**ATHER instrument:**~~ ✅ REMOVED — no yfinance data. Deployed 2026-05-30 (907958d).
- ~~**Feature 26 Phase 1 (backend data layer):**~~ ✅ COMPLETE — merged `bc0074f` (2026-05-30).
- ~~**Feature 26 Phase 2 (API endpoints + auth state param):**~~ ✅ COMPLETE — merged `4bd0dc9` (2026-05-30).
- ~~**Feature 26 Phase 3 (RITA frontend My Portfolio):**~~ ✅ COMPLETE — merged `3dd19a5` (2026-05-30). **Prod push `9700171` in progress — verify GitHub Actions + alembic at next session start.**
- **Feature 26 Phase 4 (FnO auth gate + My Portfolio):** 🔜 NEXT — start with `/enhance fno "Feature 26 Phase 4"`. Blocked on Phase 3 (COMPLETE).
- Invest Game v2 — arcade layout in progress
- Feature 17 follow-up: ~~update GitHub secret `RITA_BASE_URL`~~ ✅ ~~update Google OAuth redirect URI~~ ✅ ~~update `production.yaml` cors_origins~~ ✅ — all done
- Feature 18 (User Traffic Dashboard): COMPLETE — all phases merged and verified in prod

---

## Current Sprint: COMPLETE — v1.0 Released
**All 42 days complete. v1.0 tag created 2026-04-16.**

---

## Sprint 0 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 1 | PM + Architect | Target folder structure; ADR-001, ADR-002 | `[x]` | Structure created, ADRs written to docs/ |
| Day 2 | Architect | Pydantic schemas for all 15 CSV tables | `[x]` | 16 schema files written to src/rita/schemas/ — derived from actual POC CSV headers |
| Day 3 | TechWriter | Bootstrap Confluence: Architecture section, ADR pages, Sprint board | `[x]` | ADR-001 [65568776] and ADR-002 [65536002] published to Architecture section |

## Sprint 1 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 4 | Engineer A | Pydantic Settings, config YAML hierarchy, remove hardcoded secrets | `[x]` | config.py, pyproject.toml, .env.example written; jwt_secret removed from YAML |
| Day 5 | Engineer B | Repository layer — CSV tables, file locking, schema validation | `[x]` | CsvRepository base + 15 concrete classes; per-instance lock; validation on read+write |
| Day 6 | Ops | Multi-stage Dockerfile, CI v2 pipeline | `[x]` | Multi-stage Dockerfile (builder lints+tests, runtime non-root); CI: lint→test→docker-build |
| Day 7 | QA | Config + repository tests | `[x]` | 8 config tests + 11 repo tests (incl. concurrency); coverage threshold raised to 80% |
| Day 8 | TechWriter | Confluence: Security & Config pages | `[x]` | Config Guide [65863699] + Security page [65994769] published under Engineering section |

## Sprint 2 Tasks

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 9 | Engineer C | System APIs (CRUD routers) | `[x]` | 8 CRUD routers (positions, orders, snapshots, trades, alerts, audit, market_data, config_overrides); wired into main.py |
| Day 10 | Engineer C | Business Process API routers | `[x]` | WorkflowService (train) + BacktestService (backtest/evaluate); 3 routers wired into main.py; services create status=pending records; ML dispatch is Sprint 3 |
| Day 11 | Engineer C | BFF layer | `[x]` | 3 Experience Layer routers: DashboardPayload (positions+model state+alerts), FnoPayload (snapshots+portfolio+manoeuvres), OpsPayload (training+backtest runs+audit); wired into main.py |
| Day 12 | Engineer C | Global exception handler, trace IDs | `[x]` | TraceIDMiddleware (X-Request-ID header, ContextVar); 4 exception handlers (HTTPException, RequestValidationError, RepositoryValidationError, Exception→500); consistent {detail, trace_id} JSON shape |
| Day 13 | QA | API contract tests | `[x]` | 78 tests: 30 system CRUD, 18 workflow, 15 experience, 15 middleware; 100% pass; 1 pre-existing config test failure flagged |
| Day 14 | TechWriter | Confluence: API Reference | `[x]` | Sprint 2 API Reference [66650113] + Master Plan overview updated; all 3 tiers documented |

## Sprint 2.5 Tasks — Database Layer (SQLite + SQLAlchemy)

> **Decision (2026-04-02):** Replace CSV backend with SQLite via SQLAlchemy 2.x ORM.
> ADR-003 written. Zero changes to routers, services, or schemas — repository layer only.
> PostgreSQL upgrade in v2: change one `database_url` config value.

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 15 | Engineer D | SQLAlchemy setup: database.py, 15 ORM models, config.py DB settings, ADR-003 to Confluence | `[x]` | pyproject.toml: sqlalchemy>=2.0, alembic>=1.13; database.py: engine + SessionLocal + Base + get_db(); 15 model files (17 classes); DatabaseSettings in config.py; ADR-003 published [66650129] |
| Day 16 | Engineer D | Repository migration: rewrite base.py (SqlRepository), update all 15 concrete repos, update main.py lifespan | `[x]` | SqlRepository[T,M] added to base.py; 15 repos + new risk.py migrate to SQLAlchemy; services (workflow, backtest) take db: Session; all 14 routers inject get_db(); main.py lifespan creates tables on startup; 78/78 API tests pass |
| Day 17 | Ops | Alembic setup + CI update | `[x]` | alembic init; env.py imports Base + all 17 models, resolves SQLite path to absolute; 16 CREATE TABLE migration verified (upgrade head + downgrade base); CI: alembic upgrade head step added before pytest; Dockerfile: copies alembic/, CMD runs migrations before uvicorn |
| Day 18 | QA | Test suite migration | `[x]` | conftest.py: db_session fixture (sqlite:///:memory:, function-scoped) + client fixture overriding get_db; test_repository.py rewritten for SqlRepository; 96/97 tests pass (1 pre-existing TestJwtSecretFromEnvVar failure); 78 API contract tests confirmed passing |

## Sprint 3 Tasks — Service Layer & Observability

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 19 | Engineer D | WorkflowService, BacktestService (real ML dispatch stubs) | `[x]` | core/ml_dispatch.py + core/backtest_dispatch.py; daemon threads via SessionLocal; pending→running→complete/failed; 96/97 tests pass |
| Day 20 | Engineer D | ManoeuvreService, PortfolioService | `[x]` | ManoeuvreService (record/list_all/list_recent/list_by_date) + PortfolioService (record/list_all/get_by_date/get_latest); fno.py ADR-001 fixed to inject services; 96/97 tests pass |
| Day 21 | Engineer E | structlog JSON logging throughout | `[x]` | logging_config.py; middleware binds trace_id; exception handlers log errors; WorkflowService + BacktestService log job transitions; 96/97 tests pass |
| Day 22 | Engineer E | Prometheus metrics, /health, /readyz | `[x]` | prometheus-fastapi-instrumentator>=6.1; metrics.py with instrument_app(); /health liveness (no DB); /readyz readiness (SELECT 1, 503 on failure); 11 pre-existing ruff warnings fixed; 96/97 tests pass |
| Day 23 | QA | Greeks tests, manoeuvre tests, workflow integration | `[x]` | test_greeks.py (8 B-S reference tests, math only); test_services.py (6 manoeuvre + 4 portfolio); test_workflow_integration.py (6 incl. daemon thread e2e); 120/121 pass |
| Day 24 | TechWriter | Confluence: Observability & Runbook | `[x]` | Observability & Runbook published to operations section [67895297]; structlog format, health probes table, Prometheus metrics, 4 runbook scenarios, k8s probe YAML |

## Sprint 4 Tasks — Frontend & Responsive Design

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 25 | Engineer F | Decompose rita.html → ES modules | `[x]` | 21 ES modules in dashboard/js/rita/; rita.html entry point; window.* bindings for all onclick handlers |
| Day 26 | Engineer F | Decompose fno.html, ops.html → ES modules | `[x]` | fno: 14 ES modules (state.js + 13 feature modules); ops: 12 ES modules; both entry-point HTML files written |
| Day 27 | Engineer F | Responsive CSS (480/768/1100px) | `[x]` | dashboard/css/responsive.css; hamburger toggle in all 3 HTML files; 3 breakpoints: 1100/768/480px |
| Day 28 | Engineer F | Remove localhost:8000 hardcoding | `[x]` | window.RITA_API_BASE in all 3 api.js; apiBase() exported; all direct fetch() calls prefixed; ops.html display text reads from window.location.origin |
| Day 29 | QA | Playwright e2e tests | `[x]` | tests/e2e/: conftest.py (real uvicorn on :8765), test_smoke.py (7 HTTP checks), test_responsive.py (30 Playwright tests, 3 dashboards × 3 viewports); CI e2e job added; docker-build now gates on both test + e2e |
| Day 30 | TechWriter | Confluence: Frontend Architecture | `[x]` | Frontend Architecture page [68616193] published to Engineering section; 4 observability endpoints (/metrics/summary, /step-log, /drift, /mcp-calls) added to power ops.html monitoring |

## Sprint 5 Tasks — Integration, Security & Release

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 31 | QA | Full end-to-end regression + coverage report | `[~]` | Functional scenario tests created for RITA/FnO/Ops (48 tests total); RITA suite run (3/20 pass — 9 missing endpoints, 8 timeouts); TEST menu added to ops.html; /api/v1/test-results endpoint reads JUnit XML; nav.js fixed to include 'test' section; suite cards show passed-only, defects table shows failures; FnO + Ops suites pending |
| Day 32 | Security | CORS, JWT, rate limiting, input validation | `[x]` | CORSMiddleware from settings.security.cors_origins; POST /auth/token (python-jose JWT); get_current_user dependency on workflow routers (train/backtest/evaluate); slowapi 60/min default + 10/min on /auth/token; Field constraints (max_length, ge=0, pattern) on 9 schemas; 8/8 new tests pass; 128/129 total (1 pre-existing config test failure) |
| Day 33 | Ops | Terraform: k8s manifests, AlertManager, cloud provider swap | `[x]` | k8s/deployment.yaml + k8s/service.yaml + k8s/ingress.yaml + docker-compose.yml + terraform/ scaffolding delivered via external AI agent. Files present in repo (untracked — to be committed). |
| Day 34 | PM + TechWriter | Release checklist, v1.0 tag, release notes | `[ ]` | |

## Sprint 6 Tasks — Model Building, Logging & Performance Metrics

> **Decision (2026-04-12):** Port remaining model-building, training tracker, backtest engine (real impl),
> performance analytics, and drift detection from POC. Backtest dispatch was still a stub.

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 35 | Engineer | `train_best_of_n` + real backtest_dispatch + ml_dispatch n_seeds | `[x]` | train_best_of_n added to trading_env.py; backtest_dispatch replaced with real run_episode() engine; ml_dispatch has n_seeds support + structlog events |
| Day 36 | Engineer | TrainingTracker + structlog step events in ml_dispatch | `[x]` | core/training_tracker.py created; wired into workflow_service (try/except safe); structlog step events in ml_dispatch |
| Day 37 | Engineer | Performance analytics (portfolio comparison, feedback, stress) + 2 new API endpoints | `[x]` | build_portfolio_comparison, build_performance_feedback, simulate_stress_scenarios added to core/performance.py; /performance-feedback + /portfolio-comparison + /stress-scenarios added to observability.py |
| Day 38 | Engineer | DriftDetector rebased on DB + /api/v1/drift upgrade | `[x]` | core/drift_detector.py created (5 checks, DB-backed); /drift endpoint now uses DriftDetector; 121/122 tests pass (1 pre-existing config failure) |

---

## Post-Sprint 6 Completion Plan

| Day | Role | Task | Status | Notes |
|---|---|---|---|---|
| Day 39 | Engineer | Fix RITA scenario test suite (20 tests) | `[x]` | Sprint 6 added all missing endpoints. Fixed 2 test bugs: (1) drift test now checks summary/checks (not health/report); (2) training test now sends JWT via auth_token fixture in e2e conftest.py. Run: `pytest tests/e2e/test_rita_scenarios.py --junitxml=test-results/junit-rita-scenarios.xml -v` |
| Day 40 | QA | Run FnO + Ops scenario suites; fix failures | `[x]` | FnO: 11/11 pass. Ops: 16/16 pass (when run individually). Fixed 8 missing portfolio endpoints + /api/v1/data-prep/status + drift test bug (health/report → summary/checks). |
| Day 41 | TechWriter + PM | Sprint 6 Confluence docs (Days 35–38); commit untracked files (k8s, terraform, Spec files, docker-compose) | `[x]` | Confluence pages: publish_sprint6_model_ml.py + publish_v1_release_notes.py written. Sprint 6 board updated. All untracked files committed. |
| Day 42 | PM + TechWriter | Release checklist, v1.0 tag, release notes | `[x]` | v1.0 git tag created. Release notes published to Confluence (release_notes section). Program roadmap set to 100%. |

---

## Blockers

_None_

## Notes / Decisions

- 2026-03-30: Plan created.
- 2026-03-30: Sprint 0 complete (Days 1-3). ADR-001, ADR-002, 16 Pydantic schemas, full folder structure. ADR pages live on Confluence. Config YAML hierarchy created. Git repo initialised, remote pointed to github.com/sangaw/riia-cowork-jun-demo.git — not yet pushed.
- 2026-03-31: Terraform deployment scaffolded. Local deployment uses kreuzwerker/docker provider. Files in riia-jun-release/terraform/. rita_input/ read-only, rita_output/ writable. Sprint 5 Day 33 scoped for cloud.
- 2026-04-02: Sprint 2.5 added — SQLite via SQLAlchemy 2.x replaces CSV backend. ADR-003 written to docs/. Repository interface unchanged; zero impact on routers/services/schemas. Project extends to 34 days total. PostgreSQL upgrade path: change database_url in v2.
- 2026-05-06: invest-game Phase 3 complete — Ops Agent Builds verified, Game AI Compliance page added to Ops dashboard, auto-regenerate metrics.json on game complete, 18 ruff errors fixed, retrospective build run logs created, Spec_RITA_App.md + Spec_JS_Code.md updated. Commits: 8f7c738, a7a093d.
- 2026-05-11: RITA page swap feature complete — Market Signals becomes Overview landing page (Phase 01, instrument selector); previous Overview content moved to "Model Overview" (Phase 03); nav.js _currentSection default changed; .inst-tab moved into sec-market-signals; 17 unit tests added (17/17 pass); Confluence Engineering page updated; merged at 666c16a.
- 2026-05-12: Agent Performance Metrics feature built and merged (f23f74b, 79f1bbd, cd79570). 2 tasks pending. See `project-office/features/agent-performance-metrics/PLAN_STATUS.md`.
- 2026-05-14: Agent Performance Metrics closed — 10/10 DoD. Browser verify passed. Human score recorded (accuracy 3, relevance 4, planning_ok false, csat 2, time_saved 32h). aggregate_metrics.py re-run. 3 threshold alerts fired: FC-001 ×7, engineer first-pass rate 44%, CSAT 2.0/5. program-roadmap.html retired from end-of-day routine.
- 2026-05-14: /agent-performance-improvements run — FC-001 STOP gate added to all 3 skill files; FC-PARTIAL-IMPL files-count cross-check added to /enhance Step 4; aggregate_metrics.py skill_version_history preservation fixed; /agent-performance-improvements command created. Commit: 26f965b.
- 2026-05-14: Feature 05 (rita-app-improve) complete — all 5 phases delivered (Technical Analysis, Geography Overview, Learnings, ANALYSE reorg, Monitor→ds.html migration). Cosmetic fix: mkTbl badge rendering for status columns applied across ds.html MODEL + non-MODEL sections. See `project-office/features/May/05 rita-app-improve/PLAN_STATUS.md`.
- 2026-05-15: Agent Builds defect fix + Actual Token Tracking (Feature 0501) complete — 4 defects fixed (P1 trend lines, P1 skill version history, P2 token estimate cards, P3 recent_commits); Actual Token Tracking feature added (schema, ORM, Alembic migration, ops.py, agent-builds.js, ops.html, aggregate_metrics.py). Merged at a872db1. Confluence Engineering page updated v9→v10. 18 QA tests pass. DB migrated + seeded. See `project-office/features/May/0501 Defect Fix - Agent Builds Page/PLAN_STATUS.md`.
- 2026-05-15: /agent-performance-improvements — FC-PARTIAL-IMPL HTML Grep+Edit guardrail added to all 3 skill files + enhance.md step 7b; Alembic migration hard gate added to all 3 skill files + enhance.md step 7c. Commits: c8c10cd, 393d1d5.
- 2026-05-15: AI Commentary feature (06) complete — POST /api/v1/commentary, narrator boxes on Overview + Strategy pages, commentary_logs DB table, 3 KPIs added to chat/monitor, 34 tests pass. Confluence page published (82313217). Post-merge: Agent Commentary rename, font fix, Technical Analysis commentary style aligned, Chat Analytics half/half chart (intent distribution + commentary metrics), Confluence token bug fixed across 6 publish scripts. See `project-office/features/May/06 ai-commentary/PLAN_STATUS.md`.
- 2026-05-16: Feature 07 (agent-build-runs) — COMPLETE. DB write infrastructure for /enhance runs: upsert_run/upsert_agents in AgentBuildRepository, write_run_to_db.py helper, enhance.md Step 7 updated. DoD 8/8, 23 QA tests pass. Merged at 89fb5dd. /agent-performance-improvements also run: FC-001 n/a rule tightened + HTML completeness DoD item added across all 3 skill files. Commit 11f440c. See `project-office/features/May/07 agent-build-runs/PLAN_STATUS.md`.
- 2026-05-17: Feature 08 (API Layer Rationalization) — COMPLETE. Run A (20260517-1130): 3 experience endpoints added (backtest-daily, risk-timeline, training-history), 8 rita JS files + mobile app updated, portfolio adjust-position-action added, dead metrics fetch removed, ops/users.js path fixed. Run B R4+R5 (20260517-1430): session cache module (api-cache.js), API monitoring middleware + DB table, /api/experience/ops/api-metrics endpoint, API Metrics table in Ops dashboard, aggregate_metrics.py api_metrics block. Post-merge hotfixes: import path fix, setEl missing export, conflict marker (FC-IMP + FC-MERGE gates added to all skill DoDs). See `project-office/features/May/08 API Layer Rationalization/PLAN_STATUS.md`.
- 2026-05-17: /agent-performance-improvements — FC-001 v3: active spec grep added to enhance.md Step 4 (orchestrator independently verifies endpoint path in spec file). FC-IMP v2: named-import check promoted from DoD checklist to inline build step 4.5/5.5 in all 3 skill files. CSAT v1: smoke-test gate added to TechWriter step in all 3 skill files. Commits: 2f09e2c, 9dd8cb3.
- 2026-05-18: Feature 09 Run A continuation — QA agent (19/19 tests in tests/unit/test_instrument_onboard.py, mock yfinance, all edge cases) + TechWriter (Confluence Engineering v16, all 3 spec files confirmed current). Run log: run-20260518-0545.json. Commit: 1442756.
- 2026-05-18: /agent-performance-improvements — FC-001 v4: mandatory self-verify grep added to spec-update step in all 3 skill files (Engineer must report grep output, not just claim "yes"). FC-IMP v3: path-depth verification added to inline check + DoD gate in all 3 skill files (../../ vs ../ for shared/ modules). Commit: 1442756.
- 2026-05-18: Feature 09 Run B complete — instrument onboard UI panel: searchInstrument() + onboardInstrument() added to daily-ops.js, window bindings in main.js, Instrument Onboard card inserted in ops.html (sec-dailyops), 19/19 QA tests pass, Confluence Engineering page v17→v18. Merged at 57bf151.
- 2026-05-18: /agent-performance-improvements (alert threshold recalibration) — FC alert changed to recent_fires>0 (eliminates FC-001 total=7 false positive); engineer alert now uses recent_first_pass_rate/last-5 (100%, was 59% all-time); CSAT now requires ≥3 rated runs; API error alert split into combined 15% + 5xx 2% thresholds; skill_version_history after_first_pass_rate set to 1.0 for all 3 skill files. Commit: da99cb9.
- 2026-05-18 (EOD): Feature 09 COMPLETE — QA 21/21 tests (2 gap tests added: ETF filter + search 502); RITA dynamic instrument tabs (loadInstrumentTabs() via geography-overview, static fallback); Spec_JS_Code.md updated; Confluence Engineering v19; run-20260517-2137.json written. Commit: 3b9fa77.
- 2026-05-18: Feature 10 (JS Modular Restructure) — Phase 1 complete (commit 24102af). shared/api.js, shared/utils.js, shared/charts.js, shared/nav-base.js created; rita/charts.js → re-export shim; Spec_JS_Code.md updated; 40/40 QA tests pass; Confluence Engineering v20. Phases 2–5 pending. See `project-office/features/May/10 Restructure JS scripts as Modular/PLAN_STATUS.md`.
- 2026-05-18: Feature 10 Phase 3 QA + TechWriter complete — fno/api.js thin re-export + fno/app-init.js merged (cb79df2); Confluence Engineering v22; run-20260518-1253.json written.
- 2026-05-18: /enhance command extended to support ds app — skill-add-ds-feature.md created; ds routing added to .claude/commands/enhance.md.
- 2026-05-18: Feature 10 Phase 4 (DS module extraction) complete — 24 JS modules in dashboard/js/ds/ (19 sections + api/nav/main/state/utils); ds.html inline scripts (~2500 lines) replaced with single ES module entry point; FC-TIER + FC-API-SIG violations caught and fixed by QA; merged at 9c59fdb; run-20260518-1608.json written.
- 2026-05-18: /agent-performance-improvements — FC-TIER guardrail (banned system-tier API self-verify grep gate) + FC-API-SIG guardrail (api() POST positional signature) added to skill-add-ds-feature.md; skill_version_history entry added to metrics.json.
- 2026-05-18: Feature 11 (Improve Invest Game UI) — COMPLETE (off-cycle). Independent fractional buys/sells fixed; AI SELL display corrected (effective action computed pre-calculateDay). Commit: 5cde347. See `project-office/features/May/11 Improve Invest Game UI/PLAN_STATUS.md`.
- 2026-05-18: Feature 13 (Build an Agent Dashboard) — COMPLETE (off-cycle). Click-to-expand chart zoom modal added to Agent Builds screen (4 charts; ✕/backdrop/Escape dismiss; matches DS pattern). Commit: 24e8d79. See `project-office/features/May/13 Build a Agent Dashboard/PLAN_STATUS.md`.
- 2026-05-19: Feature 12A (agent-ops path migration) closed — Confluence Engineering page updated v25→v26; run-20260519-0740.json + metrics.json + Spec_RITA_App.md committed (d1b5c2d).
- 2026-05-19: Feature 12B (mobile UI restructure) — all rita-build-portfolio/ UI files relocated to riia-jun-release/mobileapp/; /mobileapp StaticFiles mount added to main.py; /onboarding route path fixed; rita-build-portfolio/ added to .gitignore and removed from git index (git rm --cached). Commits: df905db, 84b5d22.
- 2026-05-19: Feature 14 (i18n) — IN PROGRESS. Phase 1 complete: shared/i18n.js + locales (en/nl/fr, 105 keys), capsule on index.html (landing page only), main.js wiring for rita/fno/ops/ds, mobile PWA capsule on home screen. Phase 2 partial: RITA main sections done (health, market-signals, trades, performance, risk, scenarios, explainability). Remaining: agent-panel.js, ai-compliance.js, technical-analysis.js, learnings.js; all FnO section loaders except dashboard.js; all Ops section loaders. QA tests + Confluence deferred. See `project-office/features/May/14 Support for Dutch and French language/PLAN_STATUS.md`.
- 2026-05-19: Feature 15 (AWS Cloud Deployment) — site LIVE on EC2 t3.micro Mumbai (ap-south-1). Prod repo: san-work-ravionics/riia-jun-release-prod. All 6 phases complete; post-deploy JS + static file defects being fixed (crypto.randomUUID HTTP fallback, ops/ COPY in Dockerfile, agent-ops-data path fix, volume mount /app/data). See `project-office/features/May/19 Deploy to AWS Cloud/PLAN_STATUS.md`.
- 2026-05-20: investgame_v2.html committed (5e1580e) — arcade UX (one day at a time; round BUY/HOLD/SELL buttons with 3D press; journey track nodes; You-vs-AI score cards; reveal bar after each action; game log as rows). Complements investgame.html (v1 — spreadsheet/blotter UX, days as columns, inline text buttons, external JS). Both call the same backend (`/api/experience/invest-game`). v2 currently left in MOCK_MODE=true pending user review — flip to false to go live. Backend is fully implemented and registered (invest_game.py, 5-agent chain, real ASML/NVIDIA CSVs). Next: decide whether v1 is replaced or both are kept; add nav link to v2 from main dashboard; flip MOCK_MODE.
- 2026-05-20: mobileapp archive cleanup (e3468cb) — 25 unused design artifacts (RITA Mobile prototypes, JSX components, wireframes, zip backup, draft backups) moved to mobileapp/archive/. Active tree: PWA shell + v1 invest-flow-app (00–08 screens) + v2 invest-dashboard. Mobile breakpoints added to invest-flow-app/styles.css (≤480px: phone shell fills device viewport instead of fixed 360×780px mockup). investgame_v2.html also got ≤640px breakpoints (stacked arcade panel, scrollable day track, hidden nav links).
- 2026-05-21: Feature 16 (All Instruments Data Refresh Command) — COMPLETE. Run A (e920177) + Run B (8e7aa40) merged to master. yf_ticker column added to instruments table (Alembic migration applied + backfill on startup); POST /api/v1/instrument/refresh-all fetches delta OHLCV from yfinance for all 11 instruments, rebuilds input CSVs, upserts cache; /refresh-all-instruments-data slash command; project-office/scripts/run_data_refresh.py; 8 unit tests; specs + Confluence Engineering page updated (v28). NIFTY/BANKNIFTY manual CSV workflow retired. See `project-office/features/May/20 Data Refresh Command/PLAN_STATUS.md`.
- 2026-05-21: Geography panel redesign — tiles replace instrument tab row (selectGeoInstrument() on click, geo-kpi-active highlight); region labels India/United States/Europe; instrument names shortened; KPI tile padding tightened; name always occupies 2 lines. Alembic migration 20260520_add_yf_ticker applied to live DB (was missing, causing 4-instrument display bug). Pushed to prod e920177..bf59163.
- 2026-05-23: Production deploy stabilisation — SSH key rotation, 2GB swap, split-SSH pipeline, CPU-only PyTorch (image 9.4GB→~2GB), CloudWatch Logs + alarms, instrument seeding SQLite fix, SPEC_Prod_Deploy.md updated with 6 new failure rows. Geography panel live (India 5 / US 4 / EU 4). See session notes above.
- 2026-05-24: Ops observability fix — live /api/experience/ops/functional-kpis endpoint; API Metrics panel 3-bug fix (SECTIONS, inline style, CSS classes); 29 unit tests; deployed to prod (7b30b73). Feedback: Engineer CSS class generation guardrail saved to memory.
- 2026-05-26: Feature 17 (Mobile Device UI) — requirements written. Option C selected: `/mobile` gateway hub, UA detection in `main.py` root route, client-side JS snippet on all 5 desktop dashboards, `?desktop=1` escape hatch. 5 phases, 12 DoD checks defined. See `project-office/features/May/17 Mobile Device UI/REQUIREMENTS.md`.
