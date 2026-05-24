# RITA Deployment Knowledge Base

**Last updated:** 2026-05-23 (smoke test deploy — /aws-production-deploy command verified)
**Maintainer:** Ops Engineer skill (`project-office/skills/skill-ops-engineer.md`)

> Read the **Active Gotchas** section before every deploy. Write a new **Known Failure Pattern** entry after every incident. This document is the institutional memory for all RITA production deployments.

---

## Active Gotchas

> Short-lived warnings — remove when resolved.

- **Current EC2 IP:** `13.206.230.76` (ap-south-1 Mumbai) — update GitHub Secret `AWS_EC2_IP` and Google OAuth redirect URI if this changes after a `terraform apply`

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
- **Prevention:** Any time the prod repo is recreated or repo visibility changes, verify `GHCR_PAT` secret is present and the login step is in `deploy.yaml`
- **Date first seen:** 2026-05-20
- **Recurrences:** 0

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

## Successful Deploys Log

| Date | Commit | Notes |
|---|---|---|
| 2026-05-20 | multiple | Feature 15 — initial AWS deploy; 6 phases complete |
| 2026-05-21 | `8ea39ce` | nginx baked into Terraform cloud-init after accidental destroy recovery |
| 2026-05-21 | `1113c2e` | All 13 instruments seeded with `is_available=True`; TRU added |
| 2026-05-21 | `4dfcaf6` | OAuth `at_hash` fix (PATTERN-005); Feature 18 User Traffic complete |
| 2026-05-23 | `a599ca8` | Smoke test — `/aws-production-deploy` command first run; prod repo `.git` initialised on Mac; pipeline green; health ok |

---

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
