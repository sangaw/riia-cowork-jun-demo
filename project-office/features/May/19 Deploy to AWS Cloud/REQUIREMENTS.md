# Feature 15 — Deploy RITA to AWS Cloud

## Goal

Deploy the RITA FastAPI application as a Docker container on AWS EC2 (free tier),
accessible via a public URL, with automated deployments triggered by every push to `master`.

## Architecture Decision

| Decision | Choice | Reason |
|---|---|---|
| Container registry | GHCR (GitHub Container Registry) | Free for public packages; no ECR setup required |
| Compute | EC2 t2.micro | Free tier eligible; 750 hrs/month free for 12 months |
| Orchestration | Plain Docker (`docker run`) | K3s needs 2 GB+ RAM; t2.micro only has 1 GB |
| Ingress | Docker `-p 80:8000` (direct port bind) | No nginx needed when Docker handles it |
| CI/CD | GitHub Actions | Builds image, SSHes to EC2, runs docker run |
| Data persistence | Bind mounts on EC2 disk (/opt/rita_input, /opt/rita_output) | SQLite DB and CSV files live on the EC2 disk |
| Infrastructure-as-code | Terraform >= 1.6 | All AWS resources in `riia-jun-release/terraform/` |

## Files Changed

| File | Change |
|---|---|
| `Dockerfile` | Added `COPY dashboard/` and `COPY mobileapp/` — both mounted as StaticFiles by `main.py` |
| `k8s/secrets.yaml` | Changed hardcoded placeholders to `${VAR}` envsubst syntax (kept for future K8s upgrade) |
| `k8s/deployment.yaml` | Changed image reference to `${GHCR_IMAGE}` envsubst variable (kept for future K8s upgrade) |
| `terraform/main.tf` | Replaced K3s install with Docker install; reduced EBS to 30 GB (free tier limit) |
| `terraform/variables.tf` | Changed default instance type from `t3a.medium` to `t2.micro` |
| `.github/workflows/deploy.yaml` | Replaced kubectl steps with `docker run`; fixed branch trigger `main` → `master` |

## Documentation in This Folder

| File | Purpose |
|---|---|
| `DEPLOYMENT_GUIDE.md` | Step-by-step deploy instructions |
| `TERRAFORM_EXPLAINED.md` | What each Terraform resource does and how to maintain it |

## Deployment Checklist

- [ ] AWS IAM user `rita-deploy` created with `AmazonEC2FullAccess`
- [ ] `aws configure` run with the IAM user's access keys
- [ ] `terraform apply` completed — note the `public_ip` output
- [ ] `terraform/generated-key.pem` saved
- [ ] 5 GitHub Secrets added: `SSH_PRIVATE_KEY`, `AWS_EC2_IP`, `RITA_JWT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- [ ] GHCR package visibility set to Public
- [ ] RITA data files uploaded to `/opt/rita_input/` and `/opt/rita_output/`
- [ ] First `git push origin master` triggered and pipeline passed
- [ ] `http://YOUR_IP/health` returns `{"status": "ok"}`
