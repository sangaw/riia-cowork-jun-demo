# RITA Deployment Knowledge Base

**Last updated:** 2026-06-20 (88b1aa6 deployed — Invest Game v2 + data refresh; GHCR_PAT rotated after PATTERN-003 recurrence)
**Maintainer:** Ops Engineer skill (`project-office/skills/skill-ops-engineer.md`)

> Read the **Active Gotchas** section before every deploy. Write a new **Known Failure Pattern** entry after every incident. This document is the institutional memory for all RITA production deployments.

---

## Active Gotchas

> Short-lived warnings — remove when resolved.

- **Current EC2 IP:** `13.206.230.76` (ap-south-1 Mumbai) — update GitHub Secret `AWS_EC2_IP` and Google OAuth redirect URI if this changes after a `terraform apply`
- **Prod push auth:** the valid `san-work-ravionics` PAT is in repo-root **`git-key.txt`** — push with the inline `x-access-token` helper (see PATTERN-018). Do NOT let osxkeychain fall back to `sangaw` (→ `403 denied`), and do NOT ask the user to paste a token.

---

## Known Failure Patterns

---

### PATTERN-001 — Venv shebang paths invalid at runtime

- **Symptom:** `bash: line 1: ***: No such file or directory` — container starts but every Python script call fails (exit code 127)
- **Root cause:** Dockerfile builder stage used `WORKDIR /build` → venv created at `/build/venv` → shebang lines in installed scripts point to `/build/venv/bin/python` → path doesn't exist in the final runtime image
- **Fix:** Change Dockerfile builder stage to use `WORKDIR /app` so venv is built at `/app/venv` and shebang paths match the runtime filesystem
- **Prevention:** Always set `WORKDIR /app` in the builder stage. Confirm with: `docker run --rm <image> /app/venv/bin/python --version`
- **Date first seen:** 2026-05-20
- **Recurrences:** 0

---

### PATTERN-002 — SSH heredoc with quoted delimiter breaks on secrets with special characters

- **Symptom:** Deploy step exits 127 with `bash: line 1: ***: No such file or directory` inside the SSH block even though the image built correctly
- **Root cause:** `KEY='value' bash << 'ENDSSH'` uses a quoted heredoc delimiter — GitHub Actions does NOT expand `${{ secrets.* }}` inside quoted heredocs before sending the script over SSH. If secret values contain special shell characters, the heredoc boundaries break.
- **Fix:** Use an unquoted heredoc delimiter: `bash -s << ENDSSH` — GitHub Actions expands `${{ secrets.* }}` locally in the runner before the string is sent over SSH
- **Prevention:** All SSH heredoc blocks in `deploy.yaml` must use unquoted `ENDSSH` (or `EOF`), never `'ENDSSH'`
- **Date first seen:** 2026-05-20
- **Recurrences:** 0

---

### PATTERN-003 — EC2 cannot pull GHCR image (private package, no credentials)

- **Symptom:** Deploy step hangs or fails silently; old container keeps running; `docker pull` log shows authentication error or `manifest unknown`
- **Root cause:** GHCR packages are private by default. EC2 has no credentials to pull from `ghcr.io/san-work-ravionics/` unless explicitly logged in
- **Fix:**
  1. Add `GHCR_PAT` secret to the prod repo (GitHub PAT for `san-work-ravionics` with `read:packages` scope)
  2. Add this step to `deploy.yaml` before `docker pull`: `echo '${{ secrets.GHCR_PAT }}' | docker login ghcr.io -u san-work-ravionics --password-stdin`
- **Prevention:** Any time the prod repo is recreated or repo visibility changes, verify `GHCR_PAT` secret is present and the login step is in `deploy.yaml`. When rotating the Classic PAT, also update the `GHCR_PAT` secret — they use the same token.
- **Date first seen:** 2026-05-20
- **Recurrences:** 1
  - 2026-06-20: Classic PAT expired; `docker login` returned `denied: denied`. Rotated `GHCR_PAT` secret + prod remote URL to new Classic PAT. Retrigger green.

---

### PATTERN-004 — Google OAuth callback fails Error 400 `redirect_uri` mismatch

- **Symptom:** After login redirect, Google returns `Error 400: invalid_request` with `redirect_uri=https://...` in the URL
- **Root cause:** `RITA_BASE_URL` GitHub Secret was set to `https://<EC2_IP>` but EC2 has no TLS certificate — the app builds an `https://` OAuth redirect URI but that URL is not registered in Google Cloud Console
- **Fix:**
  1. Set `RITA_BASE_URL` secret to `http://<EC2_IP>` (no https, no trailing slash)
  2. Register exactly `http://<EC2_IP>/auth/callback` in Google Cloud Console → OAuth 2.0 → Authorized redirect URIs
  3. If using Cloudflare (`https://riia.ravionics.nl`): register the Cloudflare URL as well
- **Prevention:** `RITA_BASE_URL` must exactly match a registered redirect URI in Google Cloud Console. When EC2 IP changes after a `terraform apply`, update both the secret AND the Google Cloud Console entry
- **Date first seen:** 2026-05-20
- **Recurrences:** 0

---

### PATTERN-005 — Google OAuth callback 500: `JWTClaimsError: No access_token provided to compare against at_hash claim`

- **Symptom:** OAuth login redirects back but the callback endpoint returns HTTP 500; logs show `JWTClaimsError: No access_token provided to compare against at_hash claim`
- **Root cause:** `jose.jwt.decode(id_token, "", options={"verify_signature": False})` still validates the `at_hash` claim present in Google's ID token. `at_hash` requires the `access_token` to be passed to `jwt.decode()` for validation — we don't pass it
- **Fix:** Replace `jwt.decode(id_token, "", options=...)` with `jwt.get_unverified_claims(id_token)` in `src/rita/api/v1/auth.py`. This is safe because the token was obtained via a server-to-server HTTPS call to Google — we are not accepting it from untrusted input
- **Prevention:** When using `python-jose` to inspect Google ID tokens, always use `get_unverified_claims()` rather than `decode()` with `verify_signature=False`
- **Date first seen:** 2026-05-21
- **Recurrences:** 0
- **Commit fix:** `4dfcaf6`

---

### PATTERN-006 — Volume mount mismatch: app cannot find data files at startup

- **Symptom:** App starts but all data endpoints return empty or error; container logs show `FileNotFoundError` for CSV paths under `/app/data/`
- **Root cause:** Volume bind mount specified `/app/rita_input:/app/data` but the Dockerfile COPYs data to a different path, or the `docker run` command in `deploy.yaml` uses the old path `/app/rita_input` (not `:ro` suffix or wrong target)
- **Fix:** Ensure the `docker run` volume flag is: `-v /opt/rita_input:/app/data:ro -v /opt/rita_output:/app/rita_output`
  - Source on EC2: `/opt/rita_input/` and `/opt/rita_output/`
  - Target in container: `/app/data` (read-only) and `/app/rita_output` (read-write)
- **Prevention:** After any Dockerfile or `docker run` command change, verify mounts with: `docker inspect rita --format '{{json .HostConfig.Binds}}'`
- **Date first seen:** 2026-05-20
- **Recurrences:** 0

---

### PATTERN-007 — Push to dev repo triggers no deploy

- **Symptom:** Code changes committed and pushed but no GitHub Actions run appears in the prod repo; production is unchanged
- **Root cause:** The push went to the dev repo (`github.com/sangaw/riia-cowork-jun-demo`) instead of the prod repo (`github.com/san-work-ravionics/riia-jun-release-prod`). The dev repo has only `ci.yml` (lint/test) — no deploy pipeline
- **Fix:** From inside `riia-jun-release/` directory, run `git push origin master` — this directory has its own `.git` pointing to the prod remote
- **Prevention:** Always verify you are in `riia-jun-release/` before pushing a production fix. Run `git remote -v` to confirm the remote is `san-work-ravionics/riia-jun-release-prod`
- **Date first seen:** 2026-05-20
- **Recurrences:** 0

---

### PATTERN-008 — Accidental `terraform destroy` from ops terminal (infrastructure wipeout)

- **Symptom:** EC2 instance and Elastic IP disappear from AWS console mid-session; site goes offline; all SSH connections fail
- **Root cause:** Running SSH/SCP ops commands from inside the `terraform/` directory. `terraform destroy` was typed accidentally (or autocompleted) in the same terminal session being used for SSH ops
- **Recovery steps (45-minute procedure):**
  1. `cd riia-jun-release/terraform && terraform state rm` for any already-deleted resources (instance, EIP, key pair)
  2. `terraform destroy` to clean up remaining state (VPC, security groups)
  3. `terraform apply` to rebuild — new EC2 instance created; new public IP assigned
  4. Update GitHub Secret `AWS_EC2_IP` with the new instance IP
  5. Re-upload data files: `scp -r data/* ubuntu@<NEW_IP>:/opt/rita_input/`
  6. Push an empty commit to trigger GitHub Actions: `git commit --allow-empty -m "chore: trigger redeploy after infra rebuild" && git push origin master`
  7. Verify nginx is running (cloud-init includes nginx since commit `8ea39ce`)
  8. Confirm health: `curl https://riia.ravionics.nl/health`
- **Prevention:** Never run SSH, SCP, or any non-terraform command from inside `terraform/`. All EC2 ops must be run from `riia-jun-release/` root, referencing the key as `terraform/generated-key.pem`. Use separate terminal tabs for terraform vs SSH ops
- **Date first seen:** 2026-05-21
- **Recurrences:** 0
- **Infrastructure fix applied:** nginx install baked into `terraform/main.tf` `user_data` — future `terraform apply` rebuilds include nginx automatically

---

### PATTERN-009 — Prod repo `.git` missing on new machine — `git -C riia-jun-release` silently runs against dev repo

- **Symptom:** `git -C riia-jun-release remote -v` shows `sangaw/riia-cowork-jun-demo` (dev repo remote) instead of `san-work-ravionics/riia-jun-release-prod`; status checks show dev repo state, not prod repo state
- **Root cause:** `riia-jun-release/` has no `.git` directory on this machine. Git traverses up to the parent dev repo's `.git`. All prod repo commands silently operate on the dev repo instead.
- **Fix:**
  1. `git init` inside `riia-jun-release/` — creates inner `.git`, `master` branch
  2. `git -C riia-jun-release remote add origin https://<PAT>@github.com/san-work-ravionics/riia-jun-release-prod.git`
  3. `git -C riia-jun-release fetch origin`
  4. `git -C riia-jun-release reset --hard origin/master`
  5. `git -C riia-jun-release branch --set-upstream-to=origin/master master`
- **Prevention:** After cloning the dev repo on any new machine, immediately check for the inner `.git`: `ls riia-jun-release/.git`. If absent, run the fix steps before any deployment attempt. The `/aws-production-deploy` command pre-flight (Phase 1d) will catch this automatically.
- **Date first seen:** 2026-05-23
- **Recurrences:** 0

---

### PATTERN-010 — EC2 disk full during Docker image layer extraction

- **Symptom:** GitHub Actions deploy step fails with `write ... libtorch_cpu.so: no space left on device` during `docker pull`; new container never starts; old container keeps running
- **Root cause:** Accumulated stale Docker images on EC2 consume all available disk space. Each deploy pushes a new image (~3–4 GB due to PyTorch) without removing old ones. After several deploys the volume fills
- **Fix:**
  1. SSH into EC2: `ssh -i riia-jun-release/terraform/generated-key.pem ubuntu@<EC2_IP>`
  2. Check disk: `df -h /` — if >90%, prune immediately
  3. Prune all unused images: `docker image prune -a -f`
  4. Confirm free space: `df -h /` — target <50% used
  5. Re-trigger deploy: push an empty commit `git commit --allow-empty -m "chore: trigger redeploy after EC2 disk cleanup" && git push origin master`
- **Prevention:** After every successful deploy, SSH in and run `docker image prune -a -f`. The active image is never pruned (Docker protects running containers). Consider adding an automatic prune step to `deploy.yaml` before `docker pull`
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

## Successful Deploys Log

| Date | Commit | Notes |
|---|---|---|
| 2026-05-20 | multiple | Feature 15 — initial AWS deploy; 6 phases complete |
| 2026-05-21 | `8ea39ce` | nginx baked into Terraform cloud-init after accidental destroy recovery |
| 2026-05-21 | `1113c2e` | All 13 instruments seeded with `is_available=True`; TRU added |
| 2026-05-21 | `4dfcaf6` | OAuth `at_hash` fix (PATTERN-005); Feature 18 User Traffic complete |
| 2026-05-23 | `a599ca8` | Smoke test — `/aws-production-deploy` command first run; prod repo `.git` initialised on Mac; pipeline green; health ok |
| 2026-05-24 | `34d8095` | scenarios.js cache fix (backtest period selection); ASML/NVIDIA/BANKNIFTY/NIFTY CSVs added; EC2 disk full (PATTERN-010) — pruned stale images, redeployed |
| 2026-05-24 | `7b30b73` | Ops observability fix — live /api/experience/ops/functional-kpis endpoint; nav.js SECTIONS fix for api-metrics; ops.html CSS class fixes for sec-api-metrics |
| 2026-05-24 | `5df7fb5` | Agent Builds data fix — seeded agent_build_runs/agent_build_agents from 61 JSON run files; deploy.yaml now rsyncs data/agent-ops/ to EC2 and runs idempotent DB seed on every deploy |
| 2026-05-25 | `fc7e9f4` | Ops monitoring overhaul — single-row stats, GitHub Deploys table, CloudWatch active alerts, endpoint availability as drift-style grid, pipeline status removed from sidebar |
| 2026-05-25 | `d21cde4` | Strategy Comparison (Feature 16) — year toggle, scenario selector, chart, 39 unit tests; strategy-comparison.js + schema + tests deployed |
| 2026-05-25 | `0e0f032` | users.html nav fix (Chat Analytics + Daily Ops missing items); Strategy Comparison run-20260525-1559 added to agent-ops/runs for Agent Builds page |
| 2026-05-26 | `d043def` | Feature 17 Phase 1 — mobile UA detection in root() + IIFE snippet in 5 dashboards + /mobile gateway; EC2 disk fix in deploy.yaml. Deployed via EC2 local build (see PATTERN-011) due to GitHub Actions runner queue freeze. |
| 2026-05-26 | `17ffef1` | MCP SSE transport — Claude Desktop connects to production via mcp-remote. Extracted mcp_tools.py (shared), added mcp_sse_app.py (SSE), mounted /mcp/sse + /mcp/messages in main.py. mcp promoted to base deps. nginx /mcp/ location added with proxy_buffering off. End-to-end verified: tool execution + DB logging confirmed. |
| 2026-05-26 | `a50dd05` | DS app MCP calls table — timestamps formatted as EU datetime DD-MMM-YYYY HH:MM:SS AM/PM; fmtDT() + mkTbl fmt support added to ds/utils.js |
| 2026-05-26 | `2b2be01` | Investor onboarding flow v2 — auto-select goal tile per investor type; SLIDER_STOPS.short labels 3m/6m/9m/12m; SLIDER_STOPS.long 5 stops at 3yr steps to 15yr |
| 2026-05-28 | `88a5773` | Feature 25+26 — ASML equity hedge scenarios (covered call + protective put + BS pricing); FnO dashboard consolidated (positions+margin into Overview, ASML-only KPI row, 7 widgets); i18n locale keys; unit tests. Actions run cancelled but code included in next deploy. |
| 2026-05-29 | `e32595e` | Infra fixes — writable /app/data mount (instrument onboarding writes); model backup/restore around container swap; ApiCallLogMiddleware catches unhandled exceptions → 500s now visible in monitoring. GitHub Actions green; health ok. |
| 2026-05-30 | `b48d25e` | data_refresh fixes — NIFTY/BANKNIFTY yf.csv now incremental (append-only, no full overwrite); SKIP_INSTRUMENTS constant added + ATHER skip guard in refresh_all(); test suite unblocked. GitHub Actions green; health ok. |
| 2026-05-30 | `801e811` | RITA UI — nav restructure (Study menu after Overview; Agent Panel in Study); Set Goal field-name fixes; market auto-load on section visit; Performance charts side-by-side; GoalRequest.instrument field added; yearly_returns structured as {year,return_pct}. GitHub Actions green; health ok. |
| 2026-05-30 | `ebf01f7` | Feature 26 Phase 4 — FnO auth gate + My Portfolio section. Multiple hotfixes: auth overlay removed (replaced with redirect); shared/api.js auth_token→rita_token key fix (root cause of all 401s); zero-alloc filter before POST; ValidationError serialization crash fix. Portfolio save + display working on prod. |
| 2026-05-30 | `485c89d` | RITA Portfolio UI — renamed to "Portfolio", Phase 05 nav (pink), kpi-sm allocation tiles, new GET /api/v1/experience/rita/portfolio-performance endpoint, 2025 line chart post-save. Actions green; health ok. |
| 2026-05-30 | `b28602f` | RITA nav — removed Utilities section so Phase 05 Portfolio sits directly after Phase 04. Actions green; health ok. |
| 2026-05-30 | `584e807` | FnO Portfolio UI parity — kpi-sm read-only tiles, 2025 performance chart (same endpoint + pink Chart.js line as RITA), "Portfolio" heading, styled empty state with RITA link. Actions green; health ok. |
| 2026-05-30 | `ffd502c` | Feature 27 Portfolio Hedge — new FnO nav section + GET /api/experience/fno/portfolio-hedge endpoint (JWT-auth, per-instrument hedge recommendations); Invest Game v2 nav link in RITA Study section. Actions pending at EOD. |
| 2026-05-31 | `7f4136d` | Auth SSO fix — switched `rita_token` to `localStorage` (was `sessionStorage`) so a single Google sign-in works across all apps and separate tabs; Logout link added to hub topbar; disclaimer updated; `RITA_GITHUB_PAT` wired into deploy.yaml docker run + secret set via API → GitHub Deploys widget now populated. Actions green; health ok; CF-Cache BYPASS verified.
| 2026-05-31 | `b50633d` | Auth session fix — unified JWT storage key to `rita_token` across all dashboards (index/ds/rita-main/users were stuck on `auth_token`, causing re-login on every cross-app click); fixed index.html post-login routing (`return_url`→`post_login_redirect`); new `shared/dev-auth.js` seeds a `rita-dev` token on localhost so local testing skips Google OAuth (no-op in prod). Actions green; health ok; CF-Cache BYPASS verified on api.js + dev-auth.js. |
| 2026-05-31 | `0ef27ad` | RITA References page — renamed Learnings→References; 2×2 collapsible grid (Investment Philosophies, Why Retail Investors Lose Money, Technical Indicators, Sharpe Ratio); flowing paragraph copy + numbered TA list; Market Trends chart switched NIFTY→ASML. Actions green; health ok. |
| 2026-05-31 | `8d83c9e` | Dashboard UX — Invest Game embedded in RITA shell (inline section, sidebar+topbar stay visible, --game/--ok CSS vars added); DS nav: Ops+Monitor merged into "Ops & Monitor"; MCP Calls + Model MCP merged into single page (KPIs + 3 charts + detailed table). Actions green. |
| 2026-05-31 | `7340475` | DS MCP Calls — three bar charts in single row (card-row-3); User Traffic — Daily Login Activity and Daily Breakdown side by side, table scrolls after 6 rows. Actions pending at EOD. |
| 2026-06-01 | `949f7d4` | Feature 28 Portfolio Builder (RITA) + Portfolio Hedge (FnO) + auth/UX batch. `6530810` failed ruff lint (PATTERN-012); `bbf1391` fixed lint; `949f7d4` fixed Allocate→Google auth redirect. Health ok. |
| 2026-06-02 | `2ef251b` | F28 Portfolio Hedge tab UX — Discover/Selection/Allocation/Hedge grid alignment + wizard polish; agent-ops metrics + run-20260602-1200.json. Actions green; health ok; UI verified. |
| 2026-06-04 | `f6f6f1f` | F30 portfolio-aligned analytics — new /api/experience/fno/portfolio-analytics endpoint, Overview Risk/Greeks/Scenarios/Stress/Payoff/Hedge Radar, user_hedge_plan model/repo/schema, fno_hedge_plan endpoint, alembic migration. First push `8558e8c` failed test (TRU missing from MOCK_PORTFOLIO); fixed in `f6f6f1f`. Actions green; health ok. |
| 2026-06-05 | `3b4e63d` | FnO Equity Hedge UX — geo panel moved from Overview to Equity Hedge; setUnderlying() syncs eh-instrument + calls loadEquityHedge(true) when equity-hedge page active. Actions green; health ok. |
| 2026-06-05 | `ce67495` | FnO Equity Hedge — removed Portfolio Builder form; instrument from state.currentUnd, rolling 12-month date window, widgets always reflect selected geo tile. Actions green; health ok. |
| 2026-06-05 | `b8a8d25` | FnO Equity Hedge — 1σ strike pricing (K_call/K_put from historical vol move, rounded to standard intervals); fractional shares from portfolio allocation/price; 8 KPIs in single row; Date Range + Shares Held tiles added. Actions pending. |
| 2026-06-06 | `15e3780` | FnO Risk page charts — SBIN line fix (portfolio_overview now accepts instruments list; frontend passes portfolio IDs); absolute Y-axis (start_prices in API); stddev table −3σ→+3σ column order; Risk nav above Equity Hedge; Payoff moved to Equity Hedge; equity hedge layout restructure. First push `c63db6a` failed unit test (window.location.hostname in shared/api.js — see PATTERN-013); fixed in `15e3780`. Actions green; health ok. |
| 2026-06-09 | `4b62711` | Equity hedge scenarios, portfolio builder/hedge, FnO risk charts, mobile FnO/Ops, i18n locales, alembic migrations. Prod repo was 47 commits behind on Windows machine; reconciled with `git merge -s ours`. Log files removed from git tracking (.gitignore updated). Gateway test fixed (FnO now mobile-ready → /mobileapp/fno.html). Actions green; health ok. |
| 2026-06-09 | `c4a4be7` | DS Lab mobile-ready — gateway test updated (card-ds → /mobileapp/ds.html); data_refresh CSV path fix (PATTERN-014 code fix). 742/742 unit tests passing. Actions green; health ok. |
| 2026-06-09 | `bd8a2f7` | Invest Game — Jul 2025 ASML earnings shock as volatile preset (-11.37% Day 2); price row % move indicator (▲/▼ per day); equity-scenarios.html + fno.html updates. Actions green; health ok. |
| 2026-06-11 | `d6de57c` | Demo/Live auth toggle (index.html) + shared demo user `webmaster@ravionics.nl` (all access flags) seeded via migration `20260611_seed_demo_user`; `/auth/token` now records login activity. Two CI failures fixed en route (PATTERN-015): migration `no such table: users` on fresh DB → table-exists guard; integration test 500 on `/auth/token` → best-effort try/except. Actions green; health ok; index.html CF-Cache DYNAMIC; live demo login returns 200. |
| 2026-06-11 | `ca427ea` | PATTERN-016 durable fix — `RUN chmod -R a+rX /app/models` baked into Dockerfile so embed `model.safetensors` (written 0600 by newer safetensors umask) is readable by runtime user `rita`. Replaces the ephemeral live chmod hot-fix. Actions green; verified: `/health` 200, `/api/v1/chat` 200 with classifier response, `model.safetensors` perms `0644` in fresh image, CF-Cache api.js BYPASS. |
| 2026-06-14 | `598173f` | PATTERN-017 dep pinning cascade — fastapi<0.137 pins CI back to fastapi-0.136.3 + starlette-1.3.1 (compatible with prometheus-fastapi-instrumentator 8.0.0). 5 consecutive CI failures resolved. Health ok. |
| 2026-06-13 | `1a5613f` | DS Lab CRISP-DM tab content rewrite — Business Understanding line breaks + RIIA rename + sensitive infra details removed; Data Understanding 3-paragraph structure; Data Preparation 5-sentence summary + Trend Score/ATR%/EMA charts replacing 80/20 split plots; Modeling rewritten with technical bullets; Deployment paragraph break. Actions green; health ok. |
| 2026-06-14 | `3d32226` | FnO Equity Hedge — NSE live option chain via nse client (real strikes + LTP for INR instruments, BSM fallback); M&M (MM) onboarded with 5y OHLCV data; NSE Live / BSM Est. source badges; lot size (NSE_LOT_SIZE table, 18 instruments) in hedge overview KPI row + Hedge Overview card banner; activate-env-mac.sh restored. First push failed unit test (hedge_scenarios keys assertion didn't include new `data_source` field); fixed in `3d32226`. Actions green; health ok. |
| 2026-06-20 | `88b1aa6` | Invest Game v2 updates + instrument data refresh (11 CSVs). First push `23af176` failed deploy — GHCR_PAT expired (PATTERN-003 recurrence); rotated PAT in GitHub Secret + prod remote URL; retrigger `88b1aa6` green; health ok. |
| 2026-06-27 | `0178a44` | **Feature 32 Phases 1+2 — agent performance instrumentation + dashboard.** New `agent_performance` table (idempotent Alembic `993fec6a43bd`, ran clean on prod DB), fire-and-forget classifier hook (daemon thread, own session, off chat path), read-only `/api/v1/experience/rita/agent-performance` endpoint, and RITA Agent Performance page (per-agent scorecards on 4 RL params + vertical invocations chart + detail table, demo data until Phases 3–5). Push initially blocked by PATTERN-018 (osxkeychain `403 denied to sangaw`) — resolved via `git-key.txt` + inline x-access-token helper. Actions green; `/health` 200; `/api/v1/experience/rita/agent-performance` 200 with 7 agents. **Marked the June-release golden version.** |

---

---

### PATTERN-014 — refresh-all inserts 0 rows for instruments with large historical CSV (ASML, NVIDIA)

- **Symptom:** `POST /api/v1/instrument/refresh-all` returns `status: ok` but `db_rows_inserted: 0` for ASML or NVIDIA; DB latest date stays stale despite gap_days > 0; second call returns `status: error` with `error: "'date'"`
- **Root cause:** `find_instrument_csv()` picks the **largest CSV by file size** as the primary source. For ASML (`asml_2001-2026.csv`, 276K) and NVIDIA (`nvda_daily_25yr_rounded.csv`, 258K), the large historical file wins over the small yfinance delta file (`asml_daily.csv`, `nvidia_daily.csv`). `fetch_and_write_raw()` always writes to `{instrument_lower}_daily.csv` — never the historical file — so `rebuild_input()` reads the stale historical file and sees no new dates. On first refresh: 0 inserts. On second refresh: pandas merge sets `index.name = None` on write, so `load_ohlcv_csv()` fails with `KeyError: 'date'`
- **Fix (EC2 immediate, no redeploy):**
  1. SSH into EC2 and exec into the container: `docker exec rita python3 -c "..."`
  2. Merge `asml_daily.csv` into `asml_2001-2026.csv` with dedup; set `index.name = 'date'` before writing
  3. Merge `nvidia_daily.csv` into `nvda_daily_25yr_rounded.csv`; same index.name fix
  4. Call `POST /api/v1/instrument/refresh-all` — now picks the updated large file, rebuilds input, inserts rows
- **Fix (code):** `fetch_and_write_raw()` now detects the primary file (largest existing CSV) and appends to it instead of always using `{instrument_lower}_daily.csv`. Always sets `combined.index.name = 'date'` before `combined.to_csv()`. Deployed in `e8b273c`
- **Prevention:** When adding a new instrument with a large historical CSV, ensure `fetch_and_write_raw()` appends to that file, not a new delta file
- **Date first seen:** 2026-06-09
- **Recurrences:** 0

---

### PATTERN-015 — Data/seed migration fails in CI: `no such table: users` (create_all-only table)

- **Symptom:** `test` job fails at **Run database migrations** (`alembic upgrade head`) with `sqlite3.OperationalError: no such table: users`; `build-and-push` and `deploy` jobs skipped. Passes locally.
- **Root cause:** The `users` and `login_events` tables are **not** created by any migration — they exist only because `Base.metadata.create_all()` runs at app startup. The initial migration (`11a27794a41e_initial_15_tables`) creates 16 tables but not these. CI runs the migration chain against a **fresh DB with no `create_all()`**, so `users` is absent. A new seed migration that hard-queried `users` (`SELECT id FROM users`) without a guard was the first to fail; it worked locally only because the local dev DB already had `users` from prior app runs. Every other user-touching migration (e.g. `20260521_add_login_events`) survives CI because it wraps its ops in `try/except`.
- **Fix:** Guard the migration to no-op when the table is absent:
  ```python
  if "users" not in sa.inspect(op.get_bind()).get_table_names():
      return
  ```
  Applied to both `upgrade()` and `downgrade()`. In production the DB is persistent and already has `users`, so the seed still runs there. Validated locally by moving the populated DB aside and running `alembic upgrade head` on a fresh DB (EXIT=0).
- **Prevention:** Any migration that reads or writes `users`, `login_events`, or any other create_all-managed table must guard on `get_table_names()` (or `try/except`) so the CI migration check passes on a fresh DB. Always validate a new migration against a fresh DB, not just the populated local one.
- **Second manifestation (same root cause):** After the migration guard fixed step 5, the `test` job then failed at step 7 **Run integration tests** — `tests/integration/test_security.py::test_login_returns_token` got HTTP 500 because the new `/auth/token` login-tracking code ran `db.query(UserModel)` and the integration tests run against the **same migration-only DB with no `users` table**. The TestClient does not call `create_all()`. **Fix:** wrap the login-tracking lookup/insert in `try/except` with `db.rollback()` so token issuance is never blocked by a tracking failure (missing table or otherwise). Validated by rebuilding a migration-only DB locally (`mv rita.db aside; alembic upgrade head`) and running the security tests — 5 passed with `users` absent. **Rule:** any new DB access added to a previously DB-free endpoint must be tested against a migration-only DB, since CI integration tests do not run `create_all()`.
- **Date first seen:** 2026-06-11
- **Recurrences:** 0
- **Commit fix:** `54bdd3a` (migration guard) + `d6de57c` (endpoint try/except)

---

### PATTERN-016 — Chat endpoint 500: embed model `model.safetensors` baked as `0600 root`, unreadable by runtime user

- **Symptom:** RITA Market Analysis chat (`POST /api/v1/chat`) returns HTTP 500 with `{"detail":"Classification error: No such file or directory: /app/models/embed_model/model.safetensors"}`. Frontend shows "Could not reach RITA API" (`chat.js` catch-all). `/health` is `200` — only chat is affected. The file **does** exist and is full-size (~90 MB).
- **Root cause:** A **file-permission** problem, not a missing/corrupt file. `ls -la /app/models/embed_model/` shows `model.safetensors` as `-rw------- root root` (0600) while every sibling (`config.json`, `tokenizer.json`, …) is `0644`. The container runs as non-root user `rita` (uid 1000, set in Dockerfile), which cannot read the 0600 root-owned weights file. The safetensors/HuggingFace loader surfaces the EACCES as the misleading "No such file or directory". Triggered by the unpinned `sentence-transformers>=2.7` dep: a rebuild resolved a newer `huggingface_hub`/`safetensors` that writes the weights file with a restrictive umask (0600) during `SentenceTransformer.save()`, whereas older versions wrote 0644.
- **Diagnosis (safe on a 1 GB t3.micro):** SSH in and run a single `docker exec rita ls -la /app/models/embed_model/` — trivial memory, no OOM risk. **Do NOT** `docker exec` a model download/regen inside the live container as a first move — a second torch process can breach the 900m cgroup cap and OOM-kill the running container.
- **Hot fix (ephemeral, no restart):** `ssh … "docker exec -u 0 rita chmod 0644 /app/models/embed_model/model.safetensors"`. The classifier loads lazily (`_model` is still `None` after the failure), so the next chat request reads the now-readable file — no container restart needed. Verify: `curl -X POST https://riia.ravionics.nl/api/v1/chat -H 'Content-Type: application/json' -d '{"query":"market sentiment?","instrument":"NIFTY"}'` → expect `200`. **This lives only in the container's writable layer — the next deploy pulls a fresh image and reintroduces the bug.**
- **Durable fix:** add `RUN chmod -R a+rX /app/models` to the Dockerfile immediately after the `m.save('/app/models/embed_model')` step, so every future image has world-readable model files regardless of the saver's umask. Optionally also pin `sentence-transformers==<resolved>` to stop dep drift.
- **Prevention:** Any file baked into the image and read at runtime by the `rita` user must be world-readable (`a+rX`). Never assume a library's `save()`/`download()` writes 0644. When a "file not found" error names a file that demonstrably exists, check **permissions and owning user vs. the container's runtime UID** before assuming it's missing.
- **Date first seen:** 2026-06-11
- **Recurrences:** 0
- **Commit fix:** hot fix `chmod` applied live to prod container 2026-06-11; durable Dockerfile `chmod -R a+rX /app/models` **deployed in `ca427ea` (2026-06-11)** — verified `model.safetensors` is `0644` in the fresh image and `/api/v1/chat` returns 200. Self-healing across future image pulls; no longer dependent on the ephemeral live chmod.

---

### PATTERN-018 — Prod push `403 denied to sangaw` — osxkeychain hijacks the prod credential

- **Symptom:** `git -C riia-jun-release push origin master` fails with `remote: Permission to san-work-ravionics/riia-jun-release-prod.git denied to sangaw.` / `403`. The prod remote is the plain `https://github.com/...` URL with no embedded token.
- **Root cause:** The prod repo belongs to org `san-work-ravionics`; the local user `sangaw` is not a collaborator. The global `credential.helper=osxkeychain` answers the github.com challenge **first** with the cached `sangaw` credential, so the push authenticates as the wrong identity. The correct prod PAT is NOT in the keychain.
- **Where the real token lives:** repo-root **`git-key.txt`** (`…/riia-cowork-jun-demo/git-key.txt`, gitignored, 40-char `ghp_` classic PAT, owned by `san-work-ravionics`). The user refreshes this file on each rotation. **Read it from here — never ask the user to paste a token.**
- **Do NOT trust tokens echoed in old `git remote -v` output in past Claude transcripts** — those are stale/expired. On 2026-06-27 a transcript token `…kTq2` was expired (API 401) while `git-key.txt` `…Iz8v` was valid (API 200). Verify any token with: `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token <PAT>" https://api.github.com/user` → `200`.
- **Fix (verified 2026-06-27, pushed `0178a44`):**
  ```bash
  cd riia-jun-release
  export GIT_KEY=$(tr -d ' \r\n' < ../git-key.txt)
  GIT_TERMINAL_PROMPT=0 git \
    -c credential.helper= \
    -c credential.helper='!f() { echo username=x-access-token; echo "password=$GIT_KEY"; }; f' \
    push origin master
  ```
  The **first empty `-c credential.helper=` is the key** — it clears the helper list so osxkeychain can't answer with `sangaw` before the inline `x-access-token` helper runs. Keeps the token out of `.git/config` (remote stays the plain URL).
- **Prevention:** Same PAT backs the `GHCR_PAT` secret (PATTERN-003) — rotate both together. This mechanism is recorded in the auto-memory `reference-prod-push-token`.
- **Date first seen:** 2026-06-27
- **Recurrences:** 0

---

## Known Model Build Failure Patterns

Model build failures are diagnosed via `/debug-model-build`. See `project-office/skills/skill-model-build-debug.md` for the full diagnostic skill.

---

### BUILD-PATTERN-001 — CSV not found for instrument

- **Symptom:** Container logs show `FileNotFoundError` or `instrument_defaults.not_found` near `ml_dispatch.load_data`; pipeline thread crashes immediately after submission
- **Root cause:** The instrument's OHLCV CSV files were not synced to EC2 before triggering the pipeline. `find_instrument_csv()` searches `/app/data/raw/{INSTRUMENT}/` (bind-mounted from `/opt/rita_input/raw/{INSTRUMENT}/`) — if the directory is empty or missing, it raises immediately
- **Fix:**
  1. Confirm files exist locally: `ls riia-jun-release/data/raw/{INSTRUMENT}/`
  2. If missing locally, add CSVs to `riia-jun-release/data/raw/{INSTRUMENT}/` and commit
  3. Push to prod repo — `deploy.yaml` rsyncs `data/raw/` to EC2 automatically
  4. Re-trigger pipeline after deploy completes
- **Prevention:** Before running a pipeline for a new instrument, verify `ls /opt/rita_input/raw/{INSTRUMENT}/` on EC2 shows at least one OHLCV CSV
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

### BUILD-PATTERN-002 — OOM kill during training (container exits mid-run)

- **Symptom:** `docker inspect rita --format '{{.State.OOMKilled}}'` returns `true`; container restarted; training run stuck in `running` with no `ended_at`; `ml_dispatch.training_complete` never logged
- **Root cause:** stable-baselines3 DQN training with large `buffer_size` or `timesteps` exhausts EC2 instance memory. The kernel OOM-killer terminates the container process mid-training
- **Fix:**
  1. Re-trigger pipeline with reduced parameters: `timesteps=100000, buffer_size=25000`
  2. If OOM persists, add swap: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
  3. Mark the stuck training run in DB: `sqlite3 /opt/rita_output/rita.db "UPDATE training_runs SET status='failed', ended_at=datetime('now') WHERE status='running';"`
- **Prevention:** Check `free -h` on EC2 before triggering training. For the t3.micro/t3.small instances, keep `buffer_size ≤ 50000` and `timesteps ≤ 200000`
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

### BUILD-PATTERN-003 — Training run stuck in `pending` — thread never started

- **Symptom:** `POST /api/v1/pipeline` returned 202 with a `train_run_id`, but DB row stays `pending` indefinitely; no `ml_dispatch.load_data` log line ever appears
- **Root cause:** The daemon thread was launched but the container restarted between the 202 response and the thread's first log line, wiping the in-flight thread. Daemon threads do not survive container restarts
- **Fix:**
  1. Confirm container restart: `docker inspect rita --format '{{.RestartCount}}'` — if > 0, container cycled
  2. Mark stuck run as failed: `sqlite3 /opt/rita_output/rita.db "UPDATE training_runs SET status='failed', ended_at=datetime('now') WHERE status='pending';"`
  3. Investigate why container restarted (check `docker logs rita --tail 50` for crash before the gap)
  4. Re-trigger pipeline once container is stable
- **Prevention:** Resolve any container restart loops before triggering long-running builds. Check `docker ps` for `Restarting` status before initiating a pipeline run
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

### BUILD-PATTERN-004 — Model ZIP not written despite `ml_dispatch.training_complete` log

- **Symptom:** Logs show `ml_dispatch.training_complete` but `ls /opt/rita_output/models/{INSTRUMENT}/` shows no new `.zip` file; training run may be marked `complete` in DB
- **Root cause:** Disk full on EC2 — `model.save()` in stable-baselines3 fails silently or with a low-level OS error that is not caught by the training wrapper. The log event fires before the actual disk write
- **Fix:**
  1. Check disk: `df -h /opt/rita_output/` — if >90% full, clean old model ZIPs: `ls -t /opt/rita_output/models/{INSTRUMENT}/*.zip | tail -n +4 | xargs rm -f`
  2. Clean Docker layers: `docker image prune -a -f`
  3. Re-trigger pipeline with `force_retrain=true`
- **Prevention:** Monitor EC2 disk after every training run. Keep at most 3 ZIP files per instrument. Add a disk-check step to `/debug-model-build` Phase 3f
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

### BUILD-PATTERN-005 — Validation Sharpe = 0 after successful training

- **Symptom:** `ml_dispatch.training_complete` logged, ZIP exists, `training_tracker.round_recorded` logged, but `training_history.csv` shows `val_sharpe=0.0` and `val_trades=0`
- **Root cause:** The validation episode (`run_episode(model, val_df)`) raised an exception that was silently caught in the `try/except` block in `ml_dispatch.train()` (lines 174–183). The exception is not logged — metrics default to 0
- **Fix:**
  1. Check container logs for any exception between `ml_dispatch.training_complete` and `ml_dispatch.validation_complete`
  2. Common cause: `val_df` is too short (< episode_length rows) after the 80/20 split — check `ml_dispatch.data_loaded` row count
  3. If val_df is too short: the input CSV may be truncated — verify `wc -l /opt/rita_input/raw/{INSTRUMENT}/*.csv`
  4. Add more historical data or reduce `episode_length` in `config/instruments/{instrument}.yaml`
- **Prevention:** The validation episode exception should be logged at WARNING level, not silently swallowed. (Known tech-debt: track in backlog)
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

### BUILD-PATTERN-006 — Pipeline trained wrong instrument (active_instrument_id mismatch)

- **Symptom:** Pipeline completed, ZIP exists, but model is for NIFTY when user wanted BANKNIFTY (or vice versa); `instrument` field in DB training run shows unexpected value
- **Root cause:** `POST /api/v1/pipeline` takes an `instrument` parameter, but if triggered from the dashboard without specifying it, it defaults to whatever `active_instrument_id` is set to in `config_overrides` — which may not match the user's intent
- **Fix:**
  1. Confirm what ran: `sqlite3 /opt/rita_output/rita.db "SELECT instrument, status FROM training_runs ORDER BY recorded_at DESC LIMIT 3;"`
  2. Update active instrument if needed: `POST /api/v1/instrument/select` with correct `instrument_id`
  3. Re-trigger pipeline with the correct instrument explicitly in the request body
- **Prevention:** Always specify `instrument` explicitly in pipeline API calls. When triggering from the dashboard, verify the instrument selector shows the intended instrument before clicking Run
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

### BUILD-PATTERN-007 — Backtest never starts after pipeline training completes

- **Symptom:** `ml_dispatch.training_complete` logged, model ZIP exists, but no backtest run appears in the dashboard; `backtest_run_id` from the pipeline response stays in `pending`
- **Root cause:** `_run_backtest_job()` is called in the same background thread after training. If `sim_start`/`sim_end` date parsing fails (invalid ISO string) or `BacktestRunsRepository.upsert()` raises a DB constraint error, the backtest silently never executes
- **Fix:**
  1. Check logs for any exception after `ml_dispatch.validation_complete` in the pipeline thread
  2. Check backtest run status: `sqlite3 /opt/rita_output/rita.db "SELECT run_id, status FROM backtest_runs ORDER BY recorded_at DESC LIMIT 3;"`
  3. If stuck in `pending` with no logs: trigger a standalone backtest via `POST /api/v1/backtest` with the correct instrument and date range
- **Prevention:** Ensure `sim_start` and `sim_end` are valid ISO date strings (`YYYY-MM-DD`) when calling the pipeline API. Do not pass timezone-aware strings to these fields
- **Date first seen:** 2026-05-24
- **Recurrences:** 0

---

### BUILD-PATTERN-008 — Pipeline POST silently fails with 401 — missing Authorization header in shared api()

- **Symptom:** Pipeline button in DS dashboard appears to do nothing or shows a red error badge; dashboard polls `/progress` and `/api/v1/training-progress` continuously but no `POST /api/v1/pipeline` ever appears in container logs; curl test of the endpoint returns `{"detail":"Not authenticated"}`
- **Root cause:** `dashboard/js/shared/api.js` `api()` function never attaches the JWT token from `localStorage.getItem('auth_token')`. All calls to JWT-protected endpoints (`POST /api/v1/pipeline`, `POST /api/v1/instrument/select`) silently fail with 401 — the error is caught in the pipeline.js `catch(e)` block but may not render visibly
- **Fix:** Add token injection to `shared/api.js` `api()`:
  ```js
  const token = localStorage.getItem('auth_token');
  const opts = { method, headers: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } };
  ```
- **Prevention:** Any new JWT-protected endpoint called from the dashboard must be tested while NOT logged in to verify the 401 surfaces correctly, and while logged in to verify the token is attached
- **Date first seen:** 2026-05-24
- **Recurrences:** 0
- **Commit fix:** `e4e4599` (api.js Bearer header), `4a64d44` (ds.html auth guard + post-login redirect)

---

### BUILD-PATTERN-009 — Cloudflare caches stale JS after deploy — pipeline button does nothing

- **Symptom:** Build was recently deployed but pipeline button still silently fails. Nginx access log shows the user's browser (Cloudflare IP `172.69.xxx.xxx`) only makes `/health` requests — no instrument loads, no `POST /api/v1/pipeline`. Curl check confirms `CF-Cache-Status: HIT` and `age: <N>` on JS files. The old JS (e.g., `api.js` without Bearer token) is being served by Cloudflare edge cache.
- **Root cause:** Cloudflare caches static JS/CSS files based on `Cache-Control: max-age=14400` returned by the origin. After a deploy, the new JS is on EC2 but Cloudflare serves the stale cached version for up to 4 hours. Users never receive the fix until the cache expires or is purged.
- **Fix (immediate):** Purge the Cloudflare cache: Cloudflare Dashboard → `riia.ravionics.nl` → **Caching → Purge Cache → Purge Everything**. Then ask the user to hard-refresh (`Cmd+Shift+R`).
- **Fix (permanent):** nginx must send `Cache-Control: no-store, no-cache, must-revalidate` for all `.js` and `.css` files. This is now baked into `terraform/rita.nginx.conf` and the live nginx config on EC2 (applied 2026-05-24). Future deploys will include this automatically.
- **Prevention:** After every deploy that changes JS files, verify with `curl -sI https://riia.ravionics.nl/dashboard/js/shared/api.js | grep CF-Cache-Status`. A `BYPASS` or `MISS` result means Cloudflare is not caching. A `HIT` result means users are getting stale JS.
- **Date first seen:** 2026-05-24
- **Recurrences:** 0
- **Commit fix:** `aaecd42` (nginx no-store for JS/CSS)

---

### BUILD-PATTERN-010 — PermissionError: model dir not writable — relative path resolves inside image layer

- **Symptom:** `pipeline.failed` logged immediately after `POST /api/v1/pipeline 202`; exception: `PermissionError: [Errno 13] Permission denied: 'models/NIFTY'`; no model ZIP ever created; training run stays in `pending` or moves to `failed` within seconds
- **Root cause:** `config/base.yaml` sets `model.path: "models"` (relative). In the container, this resolves to `/app/models/NIFTY` — inside the Docker image layer, which is read-only. The writable bind mount is at `/app/rita_output/` (`/opt/rita_output` on EC2). `production.yaml` did not override `model.path` or `data.output_dir`, so both remained relative.
- **Fix:** Add absolute paths to `config/production.yaml`:
  ```yaml
  data:
    raw_dir: "/app/data/raw"
    input_dir: "/app/data/input"
    output_dir: "/app/rita_output/data_output"
  model:
    path: "/app/rita_output/models"
  ```
  Then redeploy (push to prod repo triggers GitHub Actions → new container image).
- **Prevention:** Any config path that the application writes to must be absolute and point to `/app/rita_output/` in production. After any change to `base.yaml` data/model paths, verify `production.yaml` overrides them. Check with: `docker exec rita python3 -c "from rita.config import settings; print(settings.model.path, settings.data.output_dir)"`
- **Date first seen:** 2026-05-24
- **Recurrences:** 0
- **Commit fix:** `9ef0b1c` (production.yaml absolute paths)

---

### BUILD-PATTERN-011 — TypeError: naive/aware datetime subtraction in post-training duration calc

- **Symptom:** Training completes (model ZIP written, DB run marked `complete`), but `pipeline.failed` is logged immediately after. `training_history.csv` never written. Dashboard shows backtest step spinning indefinitely. Exception: `TypeError: can't subtract offset-naive and offset-aware datetimes` in `workflow_service.py _run_training_job`.
- **Root cause:** SQLite strips timezone info from `TIMESTAMP` columns on read-back, returning a naive `datetime`. `started_at` is stored with `datetime.now(timezone.utc)` (aware) but read back as naive. `ended_at = datetime.now(timezone.utc)` is aware. Python raises `TypeError` when subtracting the two. The crash happens at line 118 in `workflow_service.py` — after the `upsert` that marks the run `complete`, but before `TrainingTracker.record_round()`, so the CSV is never updated.
- **Fix:** Normalise `started_at` to UTC before subtraction:
  ```python
  _started = run.started_at.replace(tzinfo=timezone.utc) if run.started_at and run.started_at.tzinfo is None else run.started_at
  duration_s = round((ended_at - _started).total_seconds(), 1) if _started else None
  ```
- **Prevention:** Whenever computing `timedelta` from DB-sourced datetimes, always normalise `tzinfo` first. SQLite + SQLAlchemy will silently drop timezone on read; never assume a datetime read from DB has the same tz-awareness as one created in-process.
- **Date first seen:** 2026-05-24
- **Recurrences:** 0
- **Commit fix:** `d9da9e8` (workflow_service.py — naive/aware datetime fix)

---

### BUILD-PATTERN-012 — train_best_of_n() missing progress_fn — multi-seed training crashes immediately

- **Symptom:** Pipeline POST returns 202, but `training.failed` logged within seconds: `train_best_of_n() got an unexpected keyword argument 'progress_fn'`. Only affects instruments configured with `n_seeds > 1`. Single-seed instruments (NIFTY default) work fine.
- **Root cause:** `train_best_of_n()` in `trading_env.py` was never updated when `progress_fn` was added to `train_agent()`. `ml_dispatch.py` passes `progress_fn=progress_fn` to both paths unconditionally.
- **Fix:** Add `progress_fn=None` to `train_best_of_n()` signature and pass it to each `train_agent()` call inside the seed loop.
- **Prevention:** Any new kwarg added to `train_agent()` must also be added to `train_best_of_n()`. Both functions share the same call site in `ml_dispatch.py`.
- **Date first seen:** 2026-05-24
- **Recurrences:** 0
- **Commit fix:** `8c5f684` (trading_env.py — progress_fn for multi-seed path)

---

### PATTERN-011 — GitHub Actions runner queue frozen — stuck re-run blocks all new triggers

- **Symptom:** A workflow run stays `queued` for 30+ minutes with no runner assigned; new pushes create zero runs (verified via API `head_sha` filter); `workflow_dispatch` API returns HTTP 500; UI cancel button fails; API cancel returns 409 "Cannot cancel a workflow re-run that has not yet queued"
- **Root cause:** A manual "Re-run jobs" click on an older run created a re-run object in GitHub's internal queue before runners were available. The re-run enters a pre-queue limbo state that GitHub's API and UI cannot cancel or delete. All subsequent push webhooks are processed but no runs are created until the limbo run clears
- **Fix (immediate):** SSH into EC2 and build the Docker image directly:
  1. Clean EC2 disk first: `docker image prune -a -f`
  2. Clone prod repo: `git clone --depth 1 https://<PAT>@github.com/san-work-ravionics/riia-jun-release-prod.git /tmp/rita-build`
  3. Build: `nohup docker build -t rita:local /tmp/rita-build > /tmp/rita-build.log 2>&1 &`
  4. Poll: `tail -f /tmp/rita-build.log` — takes ~20–30 min on t3.micro (torch + venv copy + layer export)
  5. Swap: `docker stop rita && docker rm rita && docker run -d --name rita ... rita:local`
  6. Health: `curl http://localhost/health`
- **Fix (unblock Actions):** Add `workflow_dispatch` to `deploy.yaml`, push, then call `POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatches` with `{"ref":"master"}`. This may still return 500 if the limbo run is active — retry after it clears
- **Prevention:** Never click "Re-run jobs" on a queued or in-progress run. If a run fails, let a new push trigger a fresh run. Add `workflow_dispatch` to `deploy.yaml` permanently so manual triggers are always available without needing a push
- **Date first seen:** 2026-05-26
- **Recurrences:** 0

---

### PATTERN-013 — Unit test gate blocks build: disallowed window.* access in shared/api.js

- **Symptom:** `test` job fails at `Run unit tests` with `AssertionError: shared/api.js must only access window.RITA_API_BASE, window.SESSION_TRACE_ID, and window.location.href`; `build-and-push` and `deploy` jobs skipped
- **Root cause:** `test_shared_api_js_has_no_window_bindings` in `tests/unit/test_shared_js_layer.py` enforces that `shared/api.js` only references four specific `window.*` globals. Any new `window.` access (e.g. `window.location.hostname`) that is not in the allowlist fails the test
- **Fix:** Replace the disallowed `window.X` with the equivalent bare global — e.g. `window.location.hostname` → `location.hostname`. `window` is the global object; all its properties are accessible without the prefix
- **Prevention:** When editing `shared/api.js`, never introduce a new `window.*` reference. The four permitted ones are: `window.RITA_API_BASE`, `window.SESSION_TRACE_ID`, `window.location.href`, `window.location.hostname` is NOT permitted — use `location.hostname` instead. Run `python3 -m pytest tests/unit/test_shared_js_layer.py` locally before pushing
- **Date first seen:** 2026-06-06
- **Recurrences:** 0

---

### PATTERN-017 — Dep pinning cascade: FastAPI major release breaks prometheus-fastapi-instrumentator → CI fails with 422 / 500

- **Symptom:** All integration tests return `422 Unprocessable Entity` on `POST /auth/token` (body not parsed), or all unit tests return `500 Internal Server Error` with `AttributeError: '_IncludedRouter' object has no attribute 'path'` in prometheus middleware
- **Root cause:** `prometheus-fastapi-instrumentator` uses the private FastAPI internal `_IncludedRouter`. When FastAPI releases a new major version, `_IncludedRouter` is renamed or removed, causing runtime `AttributeError` on every request. A secondary failure path: incorrect attempts to fix this by pinning `fastapi<0.116` downgrade FastAPI from 0.136.x → 0.115.x, which pulls in starlette 0.46.x; `BaseHTTPMiddleware.call_next()` in starlette 0.46.x consumes the request body before FastAPI can parse it → all body-parsing routes return 422.
- **Fix:**
  1. Check which FastAPI version was installed in the last successful CI run (get job log from prod Actions)
  2. Pin `fastapi` to `<X.YYY` where `X.YYY` is the version that broke things: `"fastapi>=0.111,<0.137"` (update ceiling each time)
  3. Do NOT also pin prometheus or downgrade starlette — pin FastAPI only
  4. `git -C riia-jun-release add pyproject.toml && git -C riia-jun-release commit && git -C riia-jun-release push origin master`
- **Prevention:** When CI integration tests suddenly fail with 422 on auth routes (previously green), check `prometheus-fastapi-instrumentator` compatibility first by getting the install log from the last good CI run vs the first bad run and diffing FastAPI versions. Do not downgrade FastAPI below 0.130+ or starlette below 1.x.
- **Date first seen:** 2026-06-14
- **Recurrences:** 0
- **Commit fix:** `598173f`

---

### PATTERN-012 — ruff lint gate blocks Docker build (E701 / F841)

- **Symptom:** `build-and-push` job fails at `RUN ruff check src/` with `Found N errors. No fixes available`; deploy job skipped; test job may have passed
- **Root cause:** Dockerfile has a ruff lint gate that runs before the image is pushed. Common violations: `E701` (single-line `if ...: return N` — ruff requires two-line form), `F841` (variable assigned but never used)
- **Fix:**
  1. Run `ruff check src/` locally to get the full error list: `/Users/sgawde/work/py-shared-env/dev/bin/python3 -m ruff check src/`
  2. Expand inline `if ...: return N` to two lines; remove unused assignments
  3. Re-run ruff locally to confirm `All checks passed!`
  4. Commit fixes to prod repo and push — new Actions run triggered automatically
- **Prevention:** Run `ruff check src/` locally before every `git push` to the prod repo. Add it as a pre-push habit, especially when writing new Python helper functions with compact single-line guards
- **Date first seen:** 2026-06-01
- **Recurrences:** 0

---

## How to Add a New Model Build Pattern

After any model build incident, append a new `### BUILD-PATTERN-NNN` block following this template:

```markdown
### BUILD-PATTERN-NNN — <Short descriptive title>

- **Symptom:** What the user or logs show — be specific
- **Root cause:** Why it happens
- **Fix:** Exact commands or steps that resolve it
- **Prevention:** Rule to follow to avoid this in future
- **Date first seen:** YYYY-MM-DD
- **Recurrences:** 0
- **Commit fix:** <sha> (if applicable)
```

Increment the counter from the last BUILD-PATTERN above. If the same pattern recurs, increment **Recurrences** on the existing entry and add a dated note below the fix.

---

## How to Add a New Pattern

After any incident, append a new `### PATTERN-NNN` block following this template:

```markdown
### PATTERN-NNN — <Short descriptive title>

- **Symptom:** What the user or logs show — be specific
- **Root cause:** Why it happens
- **Fix:** Exact commands or steps that resolve it
- **Prevention:** Rule to follow to avoid this in future
- **Date first seen:** YYYY-MM-DD
- **Recurrences:** 0
- **Commit fix:** <sha> (if applicable)
```

Increment the counter from the last pattern above. If the same pattern recurs, increment **Recurrences** on the existing entry and add a dated note below the fix.
