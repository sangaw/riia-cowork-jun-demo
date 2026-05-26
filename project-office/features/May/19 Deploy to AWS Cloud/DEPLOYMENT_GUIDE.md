# RITA AWS Deployment Guide

**Feature 15 — Deploy to AWS Cloud (Docker on EC2, free tier)**
Last updated: 2026-05-19

---

## Architecture

```
Developer Machine
    │
    └── git push (master) ──► GitHub Actions
                                    │
                          ┌─── Job 1: build-and-push ───┐
                          │  docker build ./Dockerfile   │
                          │  push to GHCR (free)        │
                          └──────────────┬───────────────┘
                                         │
                          ┌─── Job 2: deploy ──────────────┐
                          │  SSH into EC2                  │
                          │  docker pull (from GHCR)       │
                          │  docker stop/rm old container  │
                          │  docker run new container      │
                          │  health check /health          │
                          └──────────────┬─────────────────┘
                                         │
                            EC2 t2.micro (free tier)
                            ├── Docker daemon
                            └── rita container
                                ├── /app/src/      (API)
                                ├── /app/dashboard/ (dashboards)
                                └── /app/mobileapp/ (PWA)
                                Bind mounts:
                                ├── /opt/rita_input/  (CSV data, read-only)
                                └── /opt/rita_output/ (SQLite DB + model output)
```

**AWS resources (all free tier eligible):**
- VPC + public subnet + Internet Gateway
- Security Group: inbound 22 (SSH), 80 (HTTP), 443 (HTTPS)
- EC2 `t2.micro` (1 vCPU, 1 GB RAM, 30 GB gp3) — 750 hrs/month free
- Elastic IP — free when attached to a running instance

---

## Free Tier Limits to Watch

| Resource | Free allowance | Our usage |
|---|---|---|
| EC2 t2.micro | 750 hrs/month (12 months) | ~744 hrs/month |
| EBS gp3 | 30 GB | 30 GB |
| Elastic IP | Free when attached | 1 attached |
| Data transfer out | 100 GB/month | Low (dashboard traffic only) |

> After 12 months the EC2 cost is ~$8.50/month (t2.micro on-demand).

---

## Prerequisites

| Tool | Install |
|---|---|
| AWS CLI v2 | https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html |
| Terraform >= 1.6 | https://developer.hashicorp.com/terraform/install |

---

## Phase 1: AWS Console — Create an IAM User

Terraform needs AWS credentials to create resources on your behalf. Do this once in the AWS Console.

**1.1 Open IAM**

- Log into the AWS Console at https://console.aws.amazon.com
- Search for **IAM** in the top search bar and open it

**1.2 Create a new user**

- Left sidebar → **Users** → **Create user**
- Username: `rita-deploy`
- Click **Next**

**1.3 Attach permissions**

- Select **Attach policies directly**
- Search for and check: `AmazonEC2FullAccess`
- Click **Next** → **Create user**

**1.4 Create access keys**

- Click the `rita-deploy` user → **Security credentials** tab
- Scroll to **Access keys** → **Create access key**
- Use case: **Command Line Interface (CLI)** → check the confirmation box → **Next**
- Description tag: `terraform` → **Create access key**
- **Copy both the Access Key ID and Secret Access Key** — you will not be able to see the secret again

**1.5 Configure AWS CLI on your machine**

```powershell
aws configure
```

Enter when prompted:
```
AWS Access Key ID:     <paste Access Key ID>
AWS Secret Access Key: <paste Secret Access Key>
Default region name:   ap-south-1        ← Mumbai, closest to India
Default output format: json
```

> Region options: `ap-south-1` (Mumbai), `ap-southeast-1` (Singapore), `us-east-1` (Virginia).
> Use `ap-south-1` for lowest latency from India.

Verify it works:
```powershell
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/rita-deploy"
}
```

---

## Phase 2: Provision AWS Infrastructure (Terraform)

**2.1 Update region in terraform.tfvars**

```powershell
cd riia-jun-release\terraform
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
rita_env   = "production"

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
jwt_secret = "YOUR_32_CHAR_MINIMUM_SECRET_HERE"
```

Edit `providers.tf` to set your region (if not us-east-1):
```hcl
provider "aws" {
  region = "ap-south-1"   # or your chosen region
}
```

Also update `variables.tf` default region if needed.

> `terraform.tfvars` is gitignored — never commit it.

**2.2 Initialise, plan, and apply**

```powershell
terraform init
terraform plan      # review: should show ~9 resources to create
terraform apply     # type "yes" when prompted
```

This takes about 2 minutes. Expected output at the end:
```
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

Outputs:
  public_ip   = "1.2.3.4"
  ssh_command = "ssh -i generated-key.pem ubuntu@1.2.3.4"
```

**Write down your `public_ip`** — needed for GitHub Secrets.

**2.3 Save the SSH private key**

Terraform generates the key and writes it to `terraform/generated-key.pem`.
Copy its full contents (you'll paste it into GitHub Secrets):

```powershell
Get-Content terraform\generated-key.pem
```

---

## Phase 3: GitHub Repository Setup

**3.1 Push RITA code to GitHub**

If the repo isn't on GitHub yet:
```powershell
cd riia-jun-release
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin master
```

**3.2 Make the GHCR package public**

When the GitHub Actions pipeline runs for the first time, it pushes the image to GHCR.
After the first successful build:

- Go to `github.com/YOUR_USERNAME` → **Packages** tab → `rita`
- **Package settings** → **Change visibility** → **Public** → confirm

This allows the EC2 instance to `docker pull` the image without credentials.

**3.3 Add GitHub Actions Secrets**

Go to: `GitHub → Your repo → Settings → Secrets and variables → Actions → New repository secret`

| Secret name | Value |
|---|---|
| `SSH_PRIVATE_KEY` | Full content of `terraform/generated-key.pem` (include the `-----BEGIN...` and `-----END...` lines) |
| `AWS_EC2_IP` | The `public_ip` value from terraform output |
| `RITA_JWT_SECRET` | Same value you put in `terraform.tfvars` (32+ char random string) |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID — or enter `DISABLED` to skip OAuth |
| `GOOGLE_CLIENT_SECRET` | Your Google OAuth client secret — or enter `DISABLED` to skip OAuth |

---

## Phase 4: Upload Data Files (one-time)

The container mounts `/opt/rita_input` (read-only) for CSV price data and
`/opt/rita_output` for the SQLite database and model outputs.
These directories live on the EC2 disk — upload them once after `terraform apply`.

```powershell
# Wait ~2 minutes after terraform apply for Docker to finish installing on the instance

# From riia-jun-release/ on your local machine:
scp -i terraform\generated-key.pem -r rita_input\* ubuntu@YOUR_PUBLIC_IP:/opt/rita_input/
scp -i terraform\generated-key.pem -r rita_output\* ubuntu@YOUR_PUBLIC_IP:/opt/rita_output/
```

Verify:
```powershell
ssh -i terraform\generated-key.pem ubuntu@YOUR_PUBLIC_IP "ls /opt/rita_input/"
# Should list your NIFTY CSV files
```

---

## Phase 5: Trigger First Deploy

Push any commit to `master` to start the GitHub Actions pipeline:

```powershell
git commit --allow-empty -m "chore: trigger initial AWS deploy"
git push origin master
```

Watch progress: `GitHub → Your repo → Actions`

**What happens:**
1. Ubuntu runner builds the Docker image (includes `src/`, `dashboard/`, `mobileapp/`)
2. Pushes image to GHCR with a commit-SHA tag and a `latest` tag
3. SSHes into your EC2 instance
4. Pulls the new image, stops the old container, starts the new one
5. Polls `/health` until the app responds (up to 60 seconds)

First run takes ~4 minutes (image build). Subsequent deploys take ~90 seconds.

---

## Phase 6: Verify

**Health check:**
```powershell
Invoke-WebRequest -Uri http://YOUR_PUBLIC_IP/health | Select-Object -ExpandProperty Content
```
Expected: `{"status": "ok", ...}`

**Access dashboards:**

| Dashboard | URL |
|---|---|
| RITA Main | `http://YOUR_PUBLIC_IP/dashboard/rita.html` |
| FnO | `http://YOUR_PUBLIC_IP/dashboard/fno.html` |
| Ops | `http://YOUR_PUBLIC_IP/dashboard/ops.html` |
| Mobile PWA | `http://YOUR_PUBLIC_IP/mobileapp/` |
| API Docs | `http://YOUR_PUBLIC_IP/docs` |

---

## Ongoing Operations

**Deploy a new version:** Just push to `master` — Actions handles it.

**SSH access:**
```powershell
ssh -i terraform\generated-key.pem ubuntu@YOUR_PUBLIC_IP
```

**View live logs:**
```bash
docker logs rita -f --tail 100
```

**Restart the container:**
```bash
docker restart rita
```

**Container status:**
```bash
docker ps
docker stats rita
```

**Tear down (stop all charges):**
```powershell
cd terraform
terraform destroy
```

---

## Troubleshooting

**SSH permission denied:**
- The PEM key must have the right permissions. On PowerShell: right-click → Properties → Security → give only your user read access.
- Or use WSL: `chmod 400 terraform/generated-key.pem`

**`docker: command not found` on EC2:**
- Docker installs via cloud-init which runs asynchronously. Wait 3 minutes after `terraform apply` before SSHing in.
- Check install status: `sudo cat /var/log/cloud-init-output.log`

**`docker pull` fails / image not found:**
- Make the GHCR package public (Phase 3.2). Or verify the image name matches `ghcr.io/YOUR_USERNAME/YOUR_REPO/rita:latest`.

**Container exits immediately:**
- Check logs: `docker logs rita`
- Common cause: missing data files in `/opt/rita_input/` (alembic runs fine but the CSV loader fails)

**Health check never returns OK:**
- 1 GB RAM is tight. Check memory: `free -h` on the EC2 instance.
- The `--memory 900m` limit in the deploy script prevents the container from OOM-killing the host.

**Out of disk space:**
- `df -h` on the EC2 — 30 GB fills up if you accumulate many Docker images.
- Clean old images: `docker image prune -a`
