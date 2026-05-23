# SPEC — Production Deployment

**Last updated:** 2026-05-23 (deploy fixes: SSH key, swap, split SSH, CPU torch, CloudWatch logs + alarms, instrument seeding)
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
5. Health check polls `http://<EC2_IP>/health` from the **GitHub Actions runner** (not SSH) for up to 3 minutes

**Deploy pipeline structure (updated 2026-05-23):** The deploy job runs three short SSH calls instead of one long heredoc. This prevents the session being killed by the OOM spike during container swap on the 1 GB t3.micro:
1. **Pull image** — `docker login` + `docker pull` (network I/O only)
2. **Swap container** — `docker stop` + `docker rm` + `docker run -d` (returns immediately, detached)
3. **Health check** — `curl http://<EC2_IP>/health` polled from the runner, no SSH

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

## Observability (added 2026-05-23)

### Container logs — CloudWatch
Docker uses the `awslogs` driver. Logs stream to **CloudWatch → Log groups → `/rita/app` → stream `rita-container`**.
No SSH needed. The EC2 instance has an IAM role (`rita-ec2-role`) with `CloudWatchLogsFullAccess`.

**Never `docker logs` over SSH to debug production** — on a 1 GB instance, SSH + log streaming causes OOM and kills the container.

### Alarms — SNS email to contact@ravionics.nl
| Alarm | Trigger | Action |
|---|---|---|
| `rita-cpu-high` | CPU > 80% for 10 min | Email alert |
| `rita-status-check-failed` | EC2 status check fails | Email alert |

Terraform resources for both alarms and the SNS topic are in `terraform/main.tf`.

### After attaching a new IAM role to EC2
The `awslogs` Docker log driver reads credentials from the EC2 instance metadata service. The IAM role must be attached **before** the first deploy that uses `awslogs`, otherwise `docker run` hangs trying to reach CloudWatch and the SSH session times out with "Broken pipe".

---

## EC2 Instance Setup Checklist (first boot / after rebuild)

Run these once after any new EC2 instance is provisioned — before the first deploy.

```bash
# SSH in with the terraform key
ssh -i terraform/generated-key.pem -o StrictHostKeyChecking=no ubuntu@<EC2_IP>

# 1. Add 2GB swap — t3.micro has 1GB RAM; docker pull OOMs without it
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h   # confirm Swap: 2.0Gi

# 2. Verify authorized_keys matches the terraform-generated key
#    (the GitHub SSH_PRIVATE_KEY secret must match this key)
cat ~/.ssh/authorized_keys
```

**After rebuilding the EC2 instance with Terraform:** the `generated-key.pem` changes.
Update the `SSH_PRIVATE_KEY` GitHub secret to match — see "Rotating the SSH key" below.

**After provisioning:** also attach the `rita-ec2-role` IAM instance profile via
AWS Console → EC2 → Instance → Actions → Security → Modify IAM role, and create
the CloudWatch log group `/rita/app` with 30-day retention before the first deploy.

---

## Rotating the SSH key

If the `SSH_PRIVATE_KEY` GitHub secret and the key on EC2 get out of sync, CI fails with:
```
Connection closed by <IP> port 22
Error: Process completed with exit code 255
```

Fix:
```python
# Run this locally to update the secret via GitHub API
# (requires: pip install PyNaCl)
import base64, json, urllib.request
from nacl import encoding, public

PAT = "<GHCR_PAT>"          # san-work-ravionics PAT with repo scope
REPO = "san-work-ravionics/riia-jun-release-prod"
SECRET_NAME = "SSH_PRIVATE_KEY"
KEY_FILE = "riia-jun-release/terraform/generated-key.pem"

with open(KEY_FILE) as f:
    secret_value = f.read()

headers = {"Authorization": f"token {PAT}", "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28"}
req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", headers=headers)
with urllib.request.urlopen(req) as r:
    pk = json.loads(r.read())

encrypted = public.SealedBox(public.PublicKey(base64.b64decode(pk["key"]))).encrypt(secret_value.encode())
payload = json.dumps({"encrypted_value": base64.b64encode(encrypted).decode(), "key_id": pk["key_id"]}).encode()
req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}",
    data=payload, headers={**headers, "Content-Type": "application/json"}, method="PUT")
with urllib.request.urlopen(req) as r:
    print(f"HTTP {r.status}")  # 204 = success
```

---

## Docker / EC2 Ops Commands

```bash
# SSH in
ssh -i terraform/generated-key.pem -o StrictHostKeyChecking=no ubuntu@<EC2_IP>

# !! Do NOT run docker logs over SSH on prod — use CloudWatch instead !!
# AWS Console → CloudWatch → Log groups → /rita/app → rita-container

# Check volume mounts
docker inspect rita --format '{{json .HostConfig.Binds}}'

# Restart container manually
docker restart rita

# Check disk — keep > 8 GB free or docker pull will fail
df -h /
sudo du -sh /var/lib/containerd/

# Free disk: remove old images + clean containerd blobs from failed pulls
docker image prune -a -f
# If containerd blobs are large (sudo du -sh /var/lib/containerd/io.containerd.content.v1.content/):
sudo systemctl stop docker
sudo rm -rf /var/lib/containerd/io.containerd.content.v1.content/ingest/
sudo mkdir -p /var/lib/containerd/io.containerd.content.v1.content/ingest/
sudo systemctl start docker
# Then retrigger deploy with an empty commit
```

---

## Common Past Failures

| Symptom | Root cause | Fix |
|---|---|---|
| `bash: line 1: ***: No such file or directory` on deploy | Dockerfile built venv at `/build/venv` — shebang paths invalid in runtime | Use `/app` as builder WORKDIR so shebang = `/app/venv/bin/python` |
| `bash: line 1: ***: No such file or directory` in Deploy step (exit 127) | `KEY='value' bash << 'ENDSSH'` SSH pattern breaks when secret values contain special characters | Use unquoted heredoc: `bash -s << ENDSSH` — GitHub Actions expands `${{ secrets.* }}` locally before sending over SSH |
| Deploy step fails silently; old container keeps running | EC2 has no GHCR credentials — `docker pull` fails because GHCR packages are private | Add `GHCR_PAT` secret; add `echo '${{ secrets.GHCR_PAT }}' \| docker login ghcr.io` before `docker pull` in deploy step |
| OAuth callback fails on EC2 (`Error 400: invalid_request`, `redirect_uri=https://...`) | `RITA_BASE_URL` secret set to `https://` but EC2 has no TLS cert | Set `RITA_BASE_URL` to `http://<EC2_IP>` (no https, no trailing slash); also ensure this exact URL is registered in Google Cloud Console authorized redirect URIs |
| Google OAuth callback returns 500 — `JWTClaimsError: No access_token provided to compare against at_hash claim` | `jose.jwt.decode()` validates the `at_hash` claim in Google's ID token even when `verify_signature=False`; requires an `access_token` we don't pass | Replace `jwt.decode(id_token, "", options=...)` with `jwt.get_unverified_claims(id_token)` — safe since the token came via server-to-server TLS |
| Volume mount → app can't find data files | Volume was `/app/rita_input` but Dockerfile copies to `/app/data` | Volume mount must be `/opt/rita_input:/app/data:ro` |
| No deploy triggered after push | Pushed to dev repo (`sangaw/riia-cowork-jun-demo`), not prod repo | Always push code fixes from `riia-jun-release/` git, not the parent repo |
| `Connection closed by <IP> port 22` (exit 255) on deploy SSH step | `SSH_PRIVATE_KEY` secret is stale — doesn't match the public key in `~/.ssh/authorized_keys` on EC2 (happens after Terraform recreates the instance and generates a new key pair) | Re-run the "Rotating the SSH key" script above; then push an empty commit to retrigger |
| `docker pull` hangs; instance becomes unresponsive; deploy times out | t3.micro has 1GB RAM — no swap means the kernel OOM-kills docker pull mid-download | Add 2GB swap before first deploy (see "EC2 Instance Setup Checklist"); swap persists across reboots via `/etc/fstab` |
| `chat_monitor.csv` write fails in production; chat endpoint returns 500 | `data/output` is inside the read-only `/app/data` bind mount on EC2; `chat_monitor.py` was writing there | `chat.monitor_dir` config key now points to `rita_output/` (read-write mount); wrap `_log_query` in try/except so a write failure doesn't break chat |
| `client_loop: send disconnect: Broken pipe` (exit 255) mid-deploy after `docker pull` completes | Single long-running SSH heredoc is alive when the OOM spike hits during container swap — kernel kills sshd | Split deploy into 3 short SSH calls: (1) pull, (2) `docker run -d`, (3) health poll via HTTP from runner. `-d` returns immediately so SSH closes before memory spike |
| `docker run` hangs silently; deploy times out with "Broken pipe" | `awslogs` log driver initialises synchronously — if no IAM role is attached to the EC2 instance, it blocks indefinitely trying to reach CloudWatch | Attach `rita-ec2-role` IAM instance profile to EC2 **before** the first deploy that uses `awslogs`; see EC2 Instance Setup Checklist |
| `failed to extract layer … libcufft.so.12: no space left on device` | `sentence-transformers` → PyTorch → full NVIDIA CUDA stack installed in image (~7 GB); disk fills after 1–2 failed pull attempts leave blobs in `/var/lib/containerd/` | Pre-install CPU-only torch in Dockerfile with `--extra-index-url https://download.pytorch.org/whl/cpu`; image drops from ~9 GB to ~2 GB. Clean dead blobs: stop Docker, remove `ingest/` contents, recreate dir, restart Docker |
| `mkdir /var/lib/containerd/…/ingest/…: no such file or directory` on next pull after cleanup | Deleting the `ingest/` directory itself (rather than its contents) leaves containerd unable to create sub-entries | Always recreate the directory after cleanup: `sudo mkdir -p …/ingest/` then `sudo systemctl restart docker` |
| Geography panel empty; no instruments shown | `startup seed` block raises `sqlite3.OperationalError: near "?": syntax error` on `UPDATE instruments … WHERE instrument_id IN :ids` — SQLite does not support tuple binding via SQLAlchemy `text()` | Replace the single `IN :ids` statement with a per-id loop: `for id in ids: db.execute(text("… WHERE instrument_id = :id"), {"id": id})` |

---

## Deployment Workflow File Location

- **Prod repo:** `riia-jun-release/.github/workflows/deploy.yaml` — GitHub sees this at `.github/workflows/deploy.yaml` since the prod repo root IS `riia-jun-release/`
- **Dev repo root:** `.github/workflows/ci.yml` — CI only, no deploy
