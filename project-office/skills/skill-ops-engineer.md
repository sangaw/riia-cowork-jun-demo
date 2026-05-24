# Skill: Ops Engineer — RITA Production Deployments

**Use for:** Production deployments, EC2 ops, Docker diagnostics, GitHub Actions failures, AWS infra ops
**Knowledge base:** `project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md` — read before every deployment, write after every incident

---

## Role Identity

The Ops Engineer has one job: get code to production safely and fix it when production breaks. This skill gives Claude the context of someone who has run all previous RITA deploys, knows every failure that has occurred, and knows the exact recovery steps for each.

**Before any deployment action:** Read `DEPLOYMENT_KNOWLEDGE.md` — Active Gotchas section first, then relevant failure patterns.

**After any incident:** Write a new entry to `DEPLOYMENT_KNOWLEDGE.md` — symptom, root cause, fix, prevention rule.

---

## Trigger Conditions

Use this skill when the user asks to:
- Run `/aws-production-deploy` or deploy to production
- Diagnose a GitHub Actions failure or deployment error
- Check production health, container status, or EC2 disk
- SSH into EC2 for any ops command
- Update GitHub Secrets or fix `deploy.yaml`
- Run `terraform` commands (apply, plan, destroy — requires explicit user confirmation)
- Recover from infrastructure outages

---

## Two-Repo Setup — Never Confuse These

| | Dev repo (inner) | Prod repo (outer) |
|---|---|---|
| **Name** | riia-cowork-jun-demo | riia-jun-release-prod |
| **Local path** | `riia-cowork-jun-demo/` | `riia-cowork-jun-demo/riia-jun-release/` |
| **Remote** | `github.com/sangaw/riia-cowork-jun-demo` | `github.com/san-work-ravionics/riia-jun-release-prod` |
| **Push account** | `sangaw` | `san-work-ravionics` (PAT embedded in remote URL) |
| **CI/CD** | `ci.yml` — lint/test only, no deploy | `deploy.yaml` — build Docker → push GHCR → deploy EC2 |
| **Branch** | `master` | `master` |

**Rule:** A fix that must go live is committed and pushed from `riia-jun-release/` only. Pushing to the dev repo never triggers a deploy.

---

## GitHub Actions Deploy Pipeline (`deploy.yaml`)

1. Push to `riia-jun-release/` master → Actions triggered
2. `build-and-push` job: builds Docker image → pushes to GHCR (`ghcr.io/san-work-ravionics/riia-jun-release-prod`)
3. `deploy` job: rsyncs `data/raw/` + `data/input/` to `/opt/rita_input/` on EC2 → `docker login ghcr.io` → `docker pull` → `docker stop rita` → `docker run` → health check
4. Health check polls `http://localhost/health` for up to 60 seconds

**Monitor Actions:** `https://github.com/san-work-ravionics/riia-jun-release-prod/actions`

---

## GitHub Secrets (prod repo)

| Secret | Used for |
|---|---|
| `SSH_PRIVATE_KEY` | SSH into EC2 |
| `AWS_EC2_IP` | EC2 public IP |
| `RITA_JWT_SECRET` | App JWT signing key |
| `GOOGLE_CLIENT_ID` | OAuth |
| `GOOGLE_CLIENT_SECRET` | OAuth |
| `RITA_BASE_URL` | OAuth callback — must be `http://<EC2_IP>` (no https, no trailing slash) |
| `GHCR_PAT` | GitHub PAT for `san-work-ravionics` — `read:packages` scope — lets EC2 pull private GHCR images |

---

## EC2 Data Layout

```
/opt/rita_input/          ← bind-mounted as /app/data:ro
├── agent-ops/
├── input/
│   └── DAILY-DATA/       ← nifty_manual.csv, banknifty_manual.csv, orders/positions CSVs
├── output/
└── raw/
    └── {TICKER}/         ← OHLCV CSVs per instrument

/opt/rita_output/         ← bind-mounted as /app/rita_output:rw
```

**To add a new instrument's data to EC2:** commit CSV files to `data/raw/{TICKER}/` and `data/input/{TICKER}/` in the prod repo — next push deploys them automatically via rsync. No manual SCP needed.

---

## Post-Deploy Verification Checklist

Run these **after every push** that changes JS, CSS, config, or Python:

```bash
# 1. Confirm GitHub Actions completed (check in browser or gh CLI)
# https://github.com/san-work-ravionics/riia-jun-release-prod/actions

# 2. Health check
curl -s https://riia.ravionics.nl/health | python3 -m json.tool

# 3. Verify Cloudflare is NOT caching JS files (must be BYPASS or MISS, never HIT)
curl -sI https://riia.ravionics.nl/dashboard/js/shared/api.js | grep -i cf-cache-status
# Expected: CF-Cache-Status: BYPASS  (nginx sends no-store; Cloudflare should bypass)
# If HIT: old JS is still being served — purge cache from Cloudflare Dashboard →
#   riia.ravionics.nl → Caching → Purge Cache → Purge Everything

# 4. Confirm production config paths are correct (writable volume)
docker exec rita python3 -c "from rita.config import settings; print('model:', settings.model.path, '| output:', settings.data.output_dir)"
# Expected: model: /app/rita_output/models | output: /app/rita_output/data_output

# 5. Test a JWT-protected endpoint with a fresh token
docker exec rita python3 -c "from rita.auth import create_access_token; print(create_access_token('your@email.com'))"
# Then: curl -s http://localhost/api/v1/instrument/active -H "Authorization: Bearer <token>"
```

---

## Nginx Diagnostics — Reading Traffic Sources

The nginx access log at `/var/log/nginx/access.log` is the ground truth for what's reaching EC2.

| IP pattern | Source | Meaning |
|---|---|---|
| `172.69.x.x`, `172.71.x.x`, `104.x.x.x` | Cloudflare edge | Real browser traffic passing through Cloudflare |
| `127.0.0.1` | Local (curl/SSH) | Your own test commands from inside EC2 |
| `172.17.0.1` | Docker bridge | Container → host requests |

**Gotcha:** When debugging, the container logs show `172.17.0.1` for ALL requests (nginx → Docker bridge). Use nginx access log for real user traffic, not container logs.

```bash
# Real browser traffic in the last 5 min (exclude local curl):
tail -100 /var/log/nginx/access.log | grep -v '127.0.0.1'

# Check for errors:
tail -20 /var/log/nginx/error.log
```

---

## EC2 Ops Commands (run from `riia-jun-release/` root — never from `terraform/`)

```bash
# SSH in
ssh -i terraform/generated-key.pem -o StrictHostKeyChecking=no ubuntu@<EC2_IP>

# Live container logs
docker logs rita --tail 50 -f

# Check volume mounts (should show /app/data and /app/rita_output)
docker inspect rita --format '{{json .HostConfig.Binds}}'

# Manual container restart
docker restart rita

# Clean old images (if disk near full)
docker image prune -a -f

# Check disk
df -h /

# Health check
curl http://localhost/health
```

**Production URL:** `https://riia.ravionics.nl` (Cloudflare proxied → EC2 via nginx on port 80)

---

## Terraform Safety Rules

1. **Never run terraform commands from inside `terraform/`** — always from `riia-jun-release/` root using `terraform -chdir=terraform <command>`
2. **Never run `terraform destroy` without explicit user instruction** — confirm the exact command with the user before executing
3. If infrastructure is destroyed accidentally: see PATTERN-008 in `DEPLOYMENT_KNOWLEDGE.md` for recovery steps (45-minute procedure)

---

## Deployment Step-by-Step

Use `/aws-production-deploy` command for full guided deployment. Direct steps when running manually:

```bash
# From riia-jun-release/ (prod repo)
git status              # verify clean or review changes
git pull origin master  # sync with remote
git add <specific files>
git commit -m "fix: description"
git push origin master  # triggers GitHub Actions
```

Then monitor at: `https://github.com/san-work-ravionics/riia-jun-release-prod/actions`

---

## Definition of Done for Any Deployment

- [ ] `DEPLOYMENT_KNOWLEDGE.md` Active Gotchas section read before pushing
- [ ] Push made from `riia-jun-release/` (prod repo), not dev repo
- [ ] GitHub Actions run completed without red steps
- [ ] `https://riia.ravionics.nl/health` returns `{"status": "ok"}`
- [ ] Cloudflare JS cache verified: `curl -sI https://riia.ravionics.nl/dashboard/js/shared/api.js | grep CF-Cache-Status` returns `BYPASS` (not `HIT`)
- [ ] Production config paths verified: `docker exec rita python3 -c "from rita.config import settings; print(settings.model.path)"` returns `/app/rita_output/models`
- [ ] Any incident logged to `DEPLOYMENT_KNOWLEDGE.md` with symptom + root cause + fix + prevention rule
