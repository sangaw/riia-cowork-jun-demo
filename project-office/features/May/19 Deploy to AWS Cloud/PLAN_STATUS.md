# Feature 15 — Deploy to AWS Cloud: Handoff Status

**Last updated:** 2026-05-21 (session 4)
**Status:** COMPLETE — site live at `https://riia.ravionics.nl` (HTTP via EC2 IP also works).

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

## Current State (end of session 4 — 2026-05-21)

**Last push:** `1113c2e fix(seed): enable all 13 instruments and add TRU to seed`

**All fixes verified and live:**

| Fix | Commit | Status |
|---|---|---|
| nginx baked into Terraform cloud-init | `8ea39ce` | ✅ |
| All 13 instruments seeded with `is_available=True` | `1113c2e` | ✅ |
| TRU added to `_SEED_INSTRUMENTS` | `1113c2e` | ✅ |
| Startup SQL UPDATE fixes `is_available` on existing DBs | `1113c2e` | ✅ |
| Site accessible at `https://riia.ravionics.nl` | Feature 17 | ✅ |

---

## Session 4 Incident — Accidental `terraform destroy` (2026-05-21)

### What happened
Infrastructure was fully destroyed mid-day. EC2 instance and Elastic IP disappeared from AWS console. `terraform destroy` was run accidentally from the `terraform/` directory in a terminal that was also being used for SSH/ops commands.

### Recovery steps taken
1. `terraform state rm` for already-gone resources (instance, EIP, key pair)
2. `terraform destroy` to clean up remaining VPC resources
3. `terraform apply` to rebuild — same Elastic IP reattached, same SSH key reused
4. Updated GitHub Secret `AWS_EC2_IP` with new instance IP (`34.239.207.17`)
5. Re-uploaded data files via SCP: `scp -r data\* ubuntu@34.239.207.17:/opt/rita_input/`
6. Manually installed nginx (cloud-init only had Docker)
7. Pushed empty commit to trigger GitHub Actions deploy
8. Site restored

### Time to recover: ~45 minutes

### Root cause
Running ops commands (SSH, SCP) from inside the `terraform/` directory. `terraform destroy` was typed/triggered accidentally in the same terminal.

**Prevention:** Always run SSH and SCP commands from `riia-jun-release/` root, referencing the key as `terraform\generated-key.pem`. Never work inside `terraform/` for routine ops.

### Infrastructure fix applied
nginx install + reverse-proxy config added to `terraform/main.tf` `user_data` block (commit `8ea39ce`). Future `terraform apply` rebuilds will include nginx automatically — no manual SSH step needed.

---

## Instrument Seed Fix (2026-05-21)

Production DB showed only 7 instruments (8 with ATHER) instead of 13. Root causes:
1. Original 4 instruments (NIFTY, BANKNIFTY, NVIDIA, ASML) were seeded with `is_available=False`
2. TRU was missing from `_SEED_INSTRUMENTS` entirely

Fix in `main.py` (commit `1113c2e`):
- Set `is_available=True` for all 13 seed instruments
- Added TRU (TransUnion, NYSE, `yf_ticker="TRU"`)
- Added startup SQL `UPDATE instruments SET is_available=1` to fix existing DBs on next restart

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

> "Continuing Feature 15 AWS deployment defect fixing. Read `project-office/features/15 Deploy to AWS Cloud/PLAN_STATUS.md` for full context. Code analysis is complete — all known fixes are in the last push (`ec9cd7f`). The only remaining step is live site verification: ask the user to open `http://<EC2_IP>/dashboard/ops.html` and `rita.html` in a browser, check the DevTools Console, and report any errors still visible."

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
