# RITA Deployment Knowledge Base

**Last updated:** 2026-05-23
**Maintainer:** Ops Engineer skill (`project-office/skills/skill-ops-engineer.md`)

> Read the **Active Gotchas** section before every deploy. Write a new **Known Failure Pattern** entry after every incident. This document is the institutional memory for all RITA production deployments.

---

## Active Gotchas

> Short-lived warnings — remove when resolved.

_None currently active._

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

## Successful Deploys Log

| Date | Commit | Notes |
|---|---|---|
| 2026-05-20 | multiple | Feature 15 — initial AWS deploy; 6 phases complete |
| 2026-05-21 | `8ea39ce` | nginx baked into Terraform cloud-init after accidental destroy recovery |
| 2026-05-21 | `1113c2e` | All 13 instruments seeded with `is_available=True`; TRU added |
| 2026-05-21 | `4dfcaf6` | OAuth `at_hash` fix (PATTERN-005); Feature 18 User Traffic complete |

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
