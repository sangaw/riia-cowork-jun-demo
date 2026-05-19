# Feature 15 — Deploy to AWS Cloud: Handoff Status

**Last updated:** 2026-05-19
**Status:** Documentation and code complete. Deployment not yet executed — user studying docs before proceeding.

---

## What Was Done This Session

### Code changes (committed + pushed at bf44c89)

| File | Change |
|---|---|
| `Dockerfile` | Added `COPY dashboard/` and `COPY mobileapp/` — both required by FastAPI StaticFiles mount |
| `terraform/main.tf` | Replaced K3s install with Docker install; EBS reduced to 30 GB (free tier) |
| `terraform/variables.tf` | Default instance type changed to `t2.micro` (free tier) |
| `k8s/secrets.yaml` | Hardcoded `PLACEHOLDER_*` strings replaced with `${VAR}` envsubst syntax |
| `k8s/deployment.yaml` | Image placeholder replaced with `${GHCR_IMAGE}` envsubst variable |
| `.github/workflows/deploy.yaml` | Rewrote deploy job: `docker run` via SSH replaces `kubectl apply`; branch trigger fixed `main` → `master` |

### Documentation (in this folder)

| File | Contents |
|---|---|
| `REQUIREMENTS.md` | Architecture decisions, file change log, deployment checklist |
| `DEPLOYMENT_GUIDE.md` | Step-by-step instructions — Phase 1 through Phase 6 |
| `TERRAFORM_EXPLAINED.md` | Every AWS resource explained + maintenance guidance |

### Confluence (published 2026-05-19)

| Page | ID | URL |
|---|---|---|
| AWS Cloud Deployment (parent) | 83820554 | https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/83820554 |
| RITA AWS Deployment Guide | 83951618 | https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/83951618 |
| Terraform Infrastructure — Explained | 83984385 | https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/83984385 |

Publish script: `project-office/confluence/pages/publish_aws_deployment.py`

---

## Deployment Checklist (pending — user to execute)

Work through `DEPLOYMENT_GUIDE.md` in order. Tick each phase as done:

- [ ] **Phase 1** — AWS Console: create IAM user `rita-deploy`, attach `AmazonEC2FullAccess`, create access keys, run `aws configure`
- [ ] **Phase 2** — Terraform: copy `terraform.tfvars.example` → `terraform.tfvars`, fill in `jwt_secret`, run `terraform init` + `terraform apply`, note `public_ip` output, save `generated-key.pem`
- [ ] **Phase 3** — GitHub: push code to GitHub repo, make GHCR package public after first build, add 5 GitHub Secrets (`SSH_PRIVATE_KEY`, `AWS_EC2_IP`, `RITA_JWT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`)
- [ ] **Phase 4** — Data files: `scp rita_input/*` and `rita_output/*` to `/opt/rita_input/` and `/opt/rita_output/` on EC2
- [ ] **Phase 5** — First deploy: `git push origin master`, watch GitHub Actions pipeline
- [ ] **Phase 6** — Verify: `GET /health` returns OK, dashboards load at `http://YOUR_IP/dashboard/rita.html`

---

## Architecture Decision

Switched from K3s to plain Docker on `t2.micro` because K3s requires 2 GB+ RAM and the free tier only provides 1 GB. Docker maps port 80 → container port 8000 directly. `--restart unless-stopped` handles auto-restart on crash or reboot.

---

## Resume Prompt

> "I've studied the Feature 15 AWS deployment docs. Let's continue with the deployment. Read project-office/features/15 Deploy to AWS Cloud/PLAN_STATUS.md and guide me through the next pending phase."

---

## Known Risks

| Risk | Mitigation |
|---|---|
| 1 GB RAM may be tight under load | `--memory 900m` Docker flag prevents OOM-kill of host; avoid triggering training runs on the live instance |
| `terraform.tfstate` lost = can't destroy resources cleanly | Back up the file immediately after `terraform apply`; future: migrate to S3 backend (commented out in `providers.tf`) |
| `generated-key.pem` lost = locked out of EC2 | Save the key in a password manager before proceeding |
| GHCR package still private after first build | The pipeline's `docker pull` on EC2 will silently fail; check Packages tab on GitHub |
