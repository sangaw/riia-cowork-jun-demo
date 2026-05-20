# SPEC — Production Deployment

**Last updated:** 2026-05-20 (deploy fixes: GHCR auth, SSH heredoc pattern, OAuth http vs https)
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
2. GitHub Actions picks up `.github/workflows/deploy.yaml`
3. `build-and-push` job: builds Docker image → pushes to GHCR
4. `deploy` job: checks out repo → rsyncs `data/raw/` + `data/input/` to `/opt/rita_input/` on EC2 → pulls new image → restarts container
5. Health check polls `http://localhost/health` for up to 60 seconds

**Instrument CSV auto-sync (added 2026-05-20):** The `deploy` job now checks out the repo and rsyncs instrument CSVs to EC2 before container restart. To add a new instrument's data to EC2: commit the CSV files to `data/raw/{TICKER}/` and `data/input/{TICKER}/` in the prod repo — the next push deploys them automatically. No manual SCP needed.

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
| `RITA_BASE_URL` | OAuth callback URL — must be `http://<EC2_IP>` (no trailing slash, no https) |
| `GHCR_PAT` | GitHub PAT for `san-work-ravionics` with `read:packages` scope — lets EC2 pull private GHCR images |

---

## EC2 Data Layout

```
/opt/rita_input/          ← bind-mounted as /app/data (read-only)
├── agent-ops/
├── input/
│   ├── DAILY-DATA/       ← nifty_manual.csv, banknifty_manual.csv, orders/positions CSVs
│   ├── ASML/ NVIDIA/ RELIANCE/ SBIN/ ASRNL/ ATO/ AEX/ DJI/ IXIC/
│   └── ...               ← synced from prod repo data/input/ on each deploy
├── output/
└── raw/
    ├── NIFTY/ BANKNIFTY/ ASML/ NVIDIA/   ← original 4 (manually uploaded)
    ├── RELIANCE/ SBIN/ ASRNL/ ATO/ AEX/ DJI/ IXIC/  ← synced from prod repo on deploy
    └── ...               ← new instruments added by committing CSV + pushing

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
| `bash: line 1: ***: No such file or directory` in Deploy step (exit 127) | `KEY='value' bash << 'ENDSSH'` SSH pattern breaks when secret values contain special characters | Use unquoted heredoc: `bash -s << ENDSSH` — GitHub Actions expands `${{ secrets.* }}` locally before sending over SSH |
| Deploy step fails silently; old container keeps running | EC2 has no GHCR credentials — `docker pull` fails because GHCR packages are private | Add `GHCR_PAT` secret; add `echo '${{ secrets.GHCR_PAT }}' \| docker login ghcr.io` before `docker pull` in deploy step |
| OAuth callback fails on EC2 (`Error 400: invalid_request`, `redirect_uri=https://...`) | `RITA_BASE_URL` secret set to `https://` but EC2 has no TLS cert | Set `RITA_BASE_URL` to `http://<EC2_IP>` (no https, no trailing slash); also ensure this exact URL is registered in Google Cloud Console authorized redirect URIs |
| Volume mount → app can't find data files | Volume was `/app/rita_input` but Dockerfile copies to `/app/data` | Volume mount must be `/opt/rita_input:/app/data:ro` |
| No deploy triggered after push | Pushed to dev repo (`sangaw/riia-cowork-jun-demo`), not prod repo | Always push code fixes from `riia-jun-release/` git, not the parent repo |

---

## Deployment Workflow File Location

- **Prod repo:** `riia-jun-release/.github/workflows/deploy.yaml` — GitHub sees this at `.github/workflows/deploy.yaml` since the prod repo root IS `riia-jun-release/`
- **Dev repo root:** `.github/workflows/ci.yml` — CI only, no deploy
