# SPEC — Production Deployment

**Last updated:** 2026-05-19
**Status:** Live on AWS EC2

---

## Two Repos — Never Confuse Them

| | Dev repo | Prod repo |
|---|---|---|
| **Purpose** | Development, planning, agents | What gets deployed to EC2 |
| **Root path (local)** | `C:\Users\Sandeep\Documents\Work\code\riia-cowork-jun\` | `C:\Users\Sandeep\Documents\Work\code\riia-cowork-jun\riia-jun-release\` |
| **GitHub remote** | `https://github.com/sangaw/riia-cowork-jun-demo.git` | `https://github.com/san-work-ravionics/riia-jun-release-prod.git` |
| **Push account** | `sangaw` | `san-work-ravionics` (PAT embedded in remote URL) |
| **GitHub Actions** | `ci.yml` only — lint/test, no deploy | `deploy.yaml` — builds Docker image, deploys to EC2 |

**Rule:** Any code fix that needs to go live must be committed and pushed from the **prod repo** (`riia-jun-release/`), not the dev repo.

---

## How Deployment Works

1. Push a commit to `riia-jun-release/` (prod repo) → `master` branch
2. GitHub Actions picks up `.github/workflows/deploy.yaml` (it's at the root of the prod repo)
3. Workflow builds Docker image → pushes to GHCR → SSHs into EC2 → pulls image → restarts container
4. Health check polls `http://localhost/health` for up to 60 seconds

---

## Making a Fix — Step by Step

```powershell
# 1. Edit the file in the shared working directory
#    (riia-jun-release/ is shared — same physical files for both repos)

# 2. Commit and push via the PROD repo git
cd C:\Users\Sandeep\Documents\Work\code\riia-cowork-jun\riia-jun-release
git add <file>
git commit -m "fix: description"
git push origin master   # uses san-work-ravionics PAT — no login needed

# 3. Watch the deploy
#    https://github.com/san-work-ravionics/riia-jun-release-prod/actions
```

---

## GitHub Secrets (prod repo)

| Secret | Used for |
|---|---|
| `SSH_PRIVATE_KEY` | SSH into EC2 to run docker commands |
| `AWS_EC2_IP` | EC2 instance IP address |
| `RITA_JWT_SECRET` | App JWT signing key |
| `GOOGLE_CLIENT_ID` | OAuth login |
| `GOOGLE_CLIENT_SECRET` | OAuth login |
| `RITA_BASE_URL` | OAuth callback URL — must be `http://<EC2_IP>` (no trailing slash) |

---

## EC2 Data Layout

```
/opt/rita_input/          ← bind-mounted as /app/data (read-only)
├── agent-ops/
├── input/
├── output/
└── raw/
    ├── ASML/
    ├── BANKNIFTY/
    ├── NIFTY/
    ├── NVIDIA/
    └── TRU/

/opt/rita_output/         ← bind-mounted as /app/rita_output (read-write)
```

---

## Docker / EC2 Ops Commands

```bash
# SSH in
ssh -i terraform/generated-key.pem -o StrictHostKeyChecking=no ubuntu@<EC2_IP>

# Live container logs
docker logs rita --tail 50 -f

# Check volume mounts
docker inspect rita --format '{{json .HostConfig.Binds}}'

# Restart container manually
docker restart rita

# Clean old images (if disk full)
docker image prune -a -f

# Check disk
df -h /
```

---

## Common Past Failures

| Symptom | Root cause | Fix |
|---|---|---|
| `bash: line 1: ***: No such file or directory` on deploy | Dockerfile built venv at `/build/venv` — shebang paths invalid in runtime | Use `/app` as builder WORKDIR so shebang = `/app/venv/bin/python` |
| OAuth callback fails on EC2 (redirects to wrong URL) | App auto-detected `http://` from request, then forced `https://` | Set `RITA_BASE_URL` secret to `http://<EC2_IP>`; auth.py uses it directly |
| Volume mount → app can't find data files | Volume was `/app/rita_input` but Dockerfile copies to `/app/data` | Volume mount must be `/opt/rita_input:/app/data:ro` |
| No deploy triggered after push | Pushed to dev repo (`sangaw/riia-cowork-jun-demo`), not prod repo | Always push code fixes from `riia-jun-release/` git, not the parent repo |

---

## Deployment Workflow File Location

- **Prod repo:** `riia-jun-release/.github/workflows/deploy.yaml` — GitHub sees this at `.github/workflows/deploy.yaml` since the prod repo root IS `riia-jun-release/`
- **Dev repo root:** `.github/workflows/ci.yml` — CI only, no deploy
