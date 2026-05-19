# Feature 15 — Deploy to AWS Cloud: Handoff Status

**Last updated:** 2026-05-19 (session 2)
**Status:** Site is LIVE. Post-deploy defect fixing in progress.

---

## Deployment Summary

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — AWS IAM + access keys | ✅ Done | IAM user `rita-deploy`, AmazonEC2FullAccess, `aws configure` done |
| Phase 2 — Terraform apply | ✅ Done | t3.micro (Mumbai free tier — t2.micro not eligible in ap-south-1) |
| Phase 3 — GitHub secrets | ✅ Done | Prod repo: `san-work-ravionics/riia-jun-release-prod`; 5 secrets added |
| Phase 4 — Data files upload | ✅ Done | `data\*` → `/opt/rita_input/` on EC2; `rita_output\*` → `/opt/rita_output/` |
| Phase 5 — First deploy | ✅ Done | GitHub Actions pipeline working; site is live |
| Phase 6 — Verify | 🔧 In progress | JS + static file defects being fixed (see below) |

---

## Prod Repo

- **GitHub:** `https://github.com/san-work-ravionics/riia-jun-release-prod.git`
- **Local path:** `riia-jun-release/` (has its own `.git` — separate from the dev repo)
- **Branch:** `master`
- **EC2 IP:** stored as GitHub Secret `AWS_EC2_IP`

---

## All Fixes Applied This Session

| Commit area | Fix |
|---|---|
| `.gitignore` | Added — `terraform/.terraform/` was 628 MB and blocked push |
| `terraform/variables.tf` | `t2.micro` → `t3.micro` (Mumbai/ap-south-1 free tier type) |
| `Dockerfile` | Venv built at `/app/venv` (was `/build/venv`) — shebang paths now match runtime |
| `Dockerfile` | CMD uses full paths `/app/venv/bin/alembic` + `/app/venv/bin/uvicorn` |
| `Dockerfile` | `logs/` dir pre-created with `rita` ownership before `USER rita` switch |
| `Dockerfile` | `COPY ops/ /app/ops/` added — ops static JSON files now in image |
| `.github/workflows/deploy.yaml` | `packages: write` permission added to build-and-push job |
| `.github/workflows/deploy.yaml` | Volume mount fixed: `/app/rita_input` → `/app/data` (folder renamed locally) |
| `src/rita/main.py` | `_agent_ops_dir` path: 4 `.parent` calls → 3 (was resolving to `/data/agent-ops` at root) |
| `dashboard/js/shared/utils.js` | `randomUUID()` helper added — `crypto.randomUUID` only works over HTTPS |
| `dashboard/js/rita/agent-panel.js` | `crypto.randomUUID()` → `randomUUID()` (2 callsites) |
| `dashboard/js/fno/main.js` | `crypto.randomUUID()` → `randomUUID()` |

---

## Current State (end of session 2)

**Last push:** `fix: copy ops/ into image; fix agent-ops-data path (4 parents -> 3)`
- This push was in-flight when context was cleared
- It should resolve the 4 x 404 errors for ops static JSON files

**Defects that were visible at context clear:**
```
ops/metrics/source-availability.json  404
ops/metrics/functional-kpis.json      404
ops/alerts/active-alerts.json         404
/agent-ops-data/metrics.json          404
```
The last push should fix all four. After the deploy completes, verify by reloading Ops dashboard and checking browser console.

**Known remaining issue:**
- Node.js 20 deprecation warning in GitHub Actions (not an error — safe until Sep 2026)

---

## EC2 Data Layout

```
/opt/rita_input/          ← bind-mounted as /app/data (read-only)
├── agent-ops/            ← served at /agent-ops-data
├── input/
├── output/
└── raw/
    ├── ASML/asml_2001-2026.csv
    ├── BANKNIFTY/
    ├── NIFTY/
    ├── NVIDIA/
    └── TRU/

/opt/rita_output/         ← bind-mounted as /app/rita_output (read-write)
```

---

## SSH / Ops Commands

```powershell
# SSH in
ssh -i terraform\generated-key.pem -o StrictHostKeyChecking=no ubuntu@YOUR_IP

# Container logs
docker logs rita --tail 50

# Check mounts (should show /app/data and /app/rita_output)
docker inspect rita --format '{{json .HostConfig.Binds}}'

# Disk space
df -h /

# Clean old images if disk fills up
docker image prune -a -f
```

---

## Resume Prompt

> "Continuing Feature 15 AWS deployment defect fixing. Read `project-office/features/15 Deploy to AWS Cloud/PLAN_STATUS.md` for full context. Last push fixed ops static JSON 404s. Check if those are resolved and continue fixing remaining browser console errors."

---

## Original Docs

| File | Contents |
|---|---|
| `REQUIREMENTS.md` | Architecture decisions, file change log |
| `DEPLOYMENT_GUIDE.md` | Step-by-step phases 1–6 |
| `TERRAFORM_EXPLAINED.md` | Every AWS resource explained |

### Confluence

| Page | ID |
|---|---|
| AWS Cloud Deployment (parent) | 83820554 |
| RITA AWS Deployment Guide | 83951618 |
| Terraform Infrastructure — Explained | 83984385 |
