"""
Publishes Feature 15 AWS Deployment documentation to Confluence.

Creates 3 pages under SECTION["operations"]:
  - AWS Cloud Deployment         (parent)
    - RITA AWS Deployment Guide  (step-by-step instructions)
    - Terraform Infrastructure   (resource-by-resource explanation)

Run from project root:
    $env:CONFLUENCE_EMAIL = "contact@ravionics.nl"
    python project-office/confluence/pages/publish_aws_deployment.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

# ── Parent page ───────────────────────────────────────────────────────────────

PARENT_TITLE = "AWS Cloud Deployment"

PARENT_BODY = """
<h2>Overview</h2>
<p>
  Feature 15 deploys the RITA FastAPI application as a Docker container on AWS EC2,
  using the free tier (<code>t2.micro</code>). Deployments are automated via GitHub Actions
  on every push to <code>master</code>.
</p>

<h2>Architecture</h2>
<pre><code>Developer Machine
    |
    +-- git push (master) --> GitHub Actions
                                    |
                         +--- Job 1: build-and-push ---+
                         |  docker build ./Dockerfile   |
                         |  push to GHCR (free)        |
                         +-------------+---------------+
                                       |
                         +--- Job 2: deploy -----------+
                         |  SSH into EC2              |
                         |  docker pull (from GHCR)   |
                         |  docker stop/rm old        |
                         |  docker run new container  |
                         |  health check /health      |
                         +-------------+--------------+
                                       |
                           EC2 t2.micro (free tier)
                           +-- Docker daemon
                               +-- rita container
                                   +-- /app/src/       (API)
                                   +-- /app/dashboard/ (dashboards)
                                   +-- /app/mobileapp/ (PWA)
                                   Bind mounts:
                                   +-- /opt/rita_input/  (CSV data, read-only)
                                   +-- /opt/rita_output/ (SQLite DB + outputs)</code></pre>

<h2>AWS Resources (free tier)</h2>
<table>
  <tr><th>Resource</th><th>Free allowance</th><th>Our usage</th></tr>
  <tr><td>EC2 t2.micro</td><td>750 hrs/month (12 months)</td><td>~744 hrs/month</td></tr>
  <tr><td>EBS gp3</td><td>30 GB</td><td>30 GB</td></tr>
  <tr><td>Elastic IP</td><td>Free when attached</td><td>1 attached</td></tr>
  <tr><td>Data transfer out</td><td>100 GB/month</td><td>Low (dashboard traffic only)</td></tr>
</table>
<p>After 12 months the EC2 cost is approximately $8.50/month (t2.micro on-demand).</p>

<h2>Child Pages</h2>
<ul>
  <li><strong>RITA AWS Deployment Guide</strong> — step-by-step instructions to go from zero to live</li>
  <li><strong>Terraform Infrastructure</strong> — every AWS resource explained with maintenance guidance</li>
</ul>
"""

# ── Deployment Guide page ─────────────────────────────────────────────────────

GUIDE_TITLE = "RITA AWS Deployment Guide"

GUIDE_BODY = """
<h2>Prerequisites</h2>
<table>
  <tr><th>Tool</th><th>Install</th></tr>
  <tr><td>AWS CLI v2</td><td>https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html</td></tr>
  <tr><td>Terraform &gt;= 1.6</td><td>https://developer.hashicorp.com/terraform/install</td></tr>
</table>

<h2>Phase 1: AWS Console — Create an IAM User</h2>
<p>Terraform needs AWS credentials to create resources. Do this once.</p>
<ol>
  <li>Log into the AWS Console. Search for <strong>IAM</strong> and open it.</li>
  <li>Left sidebar &rarr; <strong>Users</strong> &rarr; <strong>Create user</strong>. Username: <code>rita-deploy</code>.</li>
  <li>Select <strong>Attach policies directly</strong>, search for and check <code>AmazonEC2FullAccess</code>. Click <strong>Create user</strong>.</li>
  <li>Open the <code>rita-deploy</code> user &rarr; <strong>Security credentials</strong> tab &rarr; <strong>Create access key</strong>.</li>
  <li>Use case: <strong>Command Line Interface (CLI)</strong>. Copy both the <strong>Access Key ID</strong> and <strong>Secret Access Key</strong>.</li>
</ol>
<p>Configure the AWS CLI on your local machine:</p>
<pre><code>aws configure
# AWS Access Key ID:     &lt;paste key&gt;
# AWS Secret Access Key: &lt;paste secret&gt;
# Default region name:   ap-south-1   (Mumbai — closest to India)
# Default output format: json</code></pre>
<p>Verify:</p>
<pre><code>aws sts get-caller-identity</code></pre>

<h2>Phase 2: Provision AWS Infrastructure (Terraform)</h2>
<pre><code>cd riia-jun-release\terraform
Copy-Item terraform.tfvars.example terraform.tfvars</code></pre>
<p>Edit <code>terraform.tfvars</code>:</p>
<pre><code>rita_env   = "production"
jwt_secret = "YOUR_32_CHAR_MINIMUM_SECRET_HERE"</code></pre>
<p>If using Mumbai region, edit <code>providers.tf</code>: set <code>region = "ap-south-1"</code>.</p>
<pre><code>terraform init
terraform plan     # review: ~9 resources
terraform apply    # type "yes"</code></pre>
<p>After apply, note the outputs:</p>
<pre><code>public_ip   = "1.2.3.4"
ssh_command = "ssh -i generated-key.pem ubuntu@1.2.3.4"</code></pre>
<p>Copy the contents of <code>terraform/generated-key.pem</code> — needed for GitHub Secrets.</p>

<h2>Phase 3: GitHub Repository Setup</h2>
<ol>
  <li>Push the RITA codebase to a GitHub repository if not already done.</li>
  <li>
    After the first GitHub Actions build, make the GHCR package public:<br/>
    <code>github.com/YOUR_USERNAME &rarr; Packages &rarr; rita &rarr; Package settings &rarr; Change visibility &rarr; Public</code>
  </li>
  <li>
    Add these GitHub Secrets at <code>Settings &rarr; Secrets and variables &rarr; Actions</code>:
    <table>
      <tr><th>Secret name</th><th>Value</th></tr>
      <tr><td><code>SSH_PRIVATE_KEY</code></td><td>Full content of <code>terraform/generated-key.pem</code></td></tr>
      <tr><td><code>AWS_EC2_IP</code></td><td>The <code>public_ip</code> from terraform output</td></tr>
      <tr><td><code>RITA_JWT_SECRET</code></td><td>Same value used in <code>terraform.tfvars</code></td></tr>
      <tr><td><code>GOOGLE_CLIENT_ID</code></td><td>Google OAuth client ID (or <code>DISABLED</code>)</td></tr>
      <tr><td><code>GOOGLE_CLIENT_SECRET</code></td><td>Google OAuth client secret (or <code>DISABLED</code>)</td></tr>
    </table>
  </li>
</ol>

<h2>Phase 4: Upload Data Files (one-time)</h2>
<p>Wait ~2 minutes after <code>terraform apply</code> for Docker to install on the instance, then:</p>
<pre><code># From riia-jun-release/ on your local machine
scp -i terraform/generated-key.pem -r rita_input/* ubuntu@YOUR_PUBLIC_IP:/opt/rita_input/
scp -i terraform/generated-key.pem -r rita_output/* ubuntu@YOUR_PUBLIC_IP:/opt/rita_output/</code></pre>

<h2>Phase 5: Trigger First Deploy</h2>
<pre><code>git commit --allow-empty -m "chore: trigger initial AWS deploy"
git push origin master</code></pre>
<p>
  Watch the pipeline at <code>GitHub &rarr; Your repo &rarr; Actions</code>.
  The pipeline builds the Docker image, pushes to GHCR, SSHes to EC2, runs
  <code>docker run</code>, and polls <code>/health</code> until the app responds.
  First run takes ~4 minutes; subsequent deploys ~90 seconds.
</p>

<h2>Phase 6: Verify</h2>
<pre><code>Invoke-WebRequest -Uri http://YOUR_PUBLIC_IP/health | Select-Object -ExpandProperty Content
# Expected: {"status": "ok", ...}</code></pre>
<table>
  <tr><th>Dashboard</th><th>URL</th></tr>
  <tr><td>RITA Main</td><td>http://YOUR_PUBLIC_IP/dashboard/rita.html</td></tr>
  <tr><td>FnO</td><td>http://YOUR_PUBLIC_IP/dashboard/fno.html</td></tr>
  <tr><td>Ops</td><td>http://YOUR_PUBLIC_IP/dashboard/ops.html</td></tr>
  <tr><td>Mobile PWA</td><td>http://YOUR_PUBLIC_IP/mobileapp/</td></tr>
  <tr><td>API Docs</td><td>http://YOUR_PUBLIC_IP/docs</td></tr>
</table>

<h2>Ongoing Operations</h2>
<table>
  <tr><th>Task</th><th>Command</th></tr>
  <tr><td>Deploy new version</td><td>Push to <code>master</code> — Actions handles it</td></tr>
  <tr><td>SSH access</td><td><code>ssh -i terraform\generated-key.pem ubuntu@YOUR_PUBLIC_IP</code></td></tr>
  <tr><td>View live logs</td><td><code>docker logs rita -f --tail 100</code></td></tr>
  <tr><td>Restart container</td><td><code>docker restart rita</code></td></tr>
  <tr><td>Container status</td><td><code>docker ps</code> / <code>docker stats rita</code></td></tr>
  <tr><td>Stop all charges</td><td><code>cd terraform &amp;&amp; terraform destroy</code></td></tr>
</table>

<h2>Troubleshooting</h2>
<table>
  <tr><th>Problem</th><th>Cause &amp; Fix</th></tr>
  <tr>
    <td>SSH permission denied</td>
    <td><code>SSH_PRIVATE_KEY</code> must include the full PEM file including header/footer lines.</td>
  </tr>
  <tr>
    <td><code>docker: command not found</code> on EC2</td>
    <td>Docker installs via cloud-init asynchronously — wait 3 minutes. Check: <code>sudo cat /var/log/cloud-init-output.log</code></td>
  </tr>
  <tr>
    <td><code>docker pull</code> fails</td>
    <td>Make the GHCR package public (Phase 3, step 2).</td>
  </tr>
  <tr>
    <td>Container exits immediately</td>
    <td>Check <code>docker logs rita</code>. Common cause: missing CSV files in <code>/opt/rita_input/</code>.</td>
  </tr>
  <tr>
    <td>Health check never OK</td>
    <td>1 GB RAM is tight. Check <code>free -h</code>. The <code>--memory 900m</code> Docker flag prevents OOM-killing the host.</td>
  </tr>
  <tr>
    <td>Out of disk space</td>
    <td>Clean old images: <code>docker image prune -a</code></td>
  </tr>
</table>
"""

# ── Terraform Explained page ──────────────────────────────────────────────────

TERRAFORM_TITLE = "Terraform Infrastructure — Explained"

TERRAFORM_BODY = """
<h2>What Is Terraform?</h2>
<p>
  Terraform is an <strong>Infrastructure as Code (IaC)</strong> tool. Instead of clicking through
  the AWS Console to create servers and networks, you write what you want in <code>.tf</code> files
  and Terraform creates, updates, or deletes the real AWS resources to match.
</p>
<p>
  Terraform is <strong>declarative</strong> — you describe the desired end state, not the steps to
  get there. Terraform works out what needs to be created, changed, or deleted.
</p>
<pre><code>Your .tf files  --&gt;  terraform apply  --&gt;  Real AWS resources
(desired state)                             (actual state)
                         ^
                   terraform.tfstate
                   (Terraform's memory of what it already created)</code></pre>

<h2>File Structure</h2>
<table>
  <tr><th>File</th><th>Purpose</th></tr>
  <tr><td><code>providers.tf</code></td><td>Which cloud provider to use (AWS) and which version</td></tr>
  <tr><td><code>variables.tf</code></td><td>All configurable inputs — region, instance size, secrets</td></tr>
  <tr><td><code>main.tf</code></td><td>The actual AWS resource definitions</td></tr>
  <tr><td><code>outputs.tf</code></td><td>Values printed after apply (IP address, SSH command)</td></tr>
  <tr><td><code>terraform.tfvars</code></td><td>Your actual values — <strong>gitignored, never commit</strong></td></tr>
  <tr><td><code>terraform.tfvars.example</code></td><td>Safe example showing what values are needed</td></tr>
  <tr><td><code>terraform.tfstate</code></td><td>Terraform's record of what it created — <strong>keep safe</strong></td></tr>
  <tr><td><code>generated-key.pem</code></td><td>SSH private key written by Terraform — gitignored</td></tr>
</table>

<h2>What Each Resource Does</h2>

<h3>1. VPC — Your Private Network</h3>
<p>
  A Virtual Private Cloud is an isolated private network in AWS — your own section of the data
  center. Nothing outside can reach resources inside unless you explicitly open a door via the
  Security Group.
</p>
<p><strong>Why:</strong> AWS requires all EC2 instances to live inside a VPC. It is also the security boundary.</p>

<h3>2. Internet Gateway — The Door to the Internet</h3>
<p>Attaches your VPC to the public internet.</p>
<p>
  <strong>Why:</strong> Without it, your EC2 instance has no path to the internet — you could not
  SSH in, users could not access dashboards, and GitHub Actions could not SSH to deploy.
</p>

<h3>3. Subnet — A Segment of the VPC</h3>
<p>
  A subdivision of the VPC where the EC2 instance lives.
  <code>map_public_ip_on_launch = true</code> gives EC2 instances a public IP on start (in addition
  to the static Elastic IP added later).
</p>

<h3>4. Route Table + Association — Traffic Rules</h3>
<p>
  Routing rules: <code>0.0.0.0/0</code> (all traffic) goes out via the Internet Gateway.
  Think of it as: Internet Gateway = the door, route table = the sign saying &ldquo;this way out.&rdquo;
</p>

<h3>5. Security Group — The Firewall</h3>
<table>
  <tr><th>Port</th><th>Why it is open</th></tr>
  <tr><td>22 (SSH)</td><td>GitHub Actions and you need to SSH in to deploy</td></tr>
  <tr><td>80 (HTTP)</td><td>Users access RITA dashboards on port 80</td></tr>
  <tr><td>443 (HTTPS)</td><td>Reserved for future SSL setup</td></tr>
  <tr><td>All egress</td><td>EC2 needs to pull Docker images from GHCR and send responses</td></tr>
</table>
<p>
  Port 22 is open to all IPs (<code>0.0.0.0/0</code>) but access still requires the private key
  (<code>generated-key.pem</code>), which is not guessable.
</p>

<h3>6. SSH Key Pair — SSH Access</h3>
<p>
  Terraform generates a 4096-bit RSA key pair automatically. The public key is uploaded to AWS.
  The private key is written to <code>terraform/generated-key.pem</code> on your machine.
</p>
<p>
  <strong>Important:</strong> <code>generated-key.pem</code> is gitignored. It is your only way to
  SSH in — back it up somewhere safe and paste it into GitHub Secrets as <code>SSH_PRIVATE_KEY</code>.
</p>

<h3>7. EC2 Instance — The Server</h3>
<p>The virtual machine that runs the RITA Docker container.</p>
<ul>
  <li><strong>AMI:</strong> Terraform automatically finds the latest Ubuntu 22.04 image for your region — no hardcoded AMI IDs.</li>
  <li><strong>Instance type:</strong> <code>t2.micro</code> — 1 vCPU, 1 GB RAM, free tier eligible.</li>
  <li><strong>EBS:</strong> 30 GB gp3 SSD — the free tier limit.</li>
  <li>
    <strong>user_data (bootstrap script):</strong> Runs once on first boot via cloud-init.
    Creates <code>/opt/rita_input</code> and <code>/opt/rita_output</code>, then installs Docker.
    This makes the server self-configuring — no manual SSH needed to install Docker.
  </li>
</ul>

<h3>8. Elastic IP — A Permanent Public Address</h3>
<p>
  A static public IP address that stays the same even if the EC2 instance is stopped and restarted.
</p>
<p>
  <strong>Why:</strong> EC2 instances get a new random public IP every restart. With an Elastic IP,
  your dashboard URL never changes and the <code>AWS_EC2_IP</code> GitHub Secret stays valid
  indefinitely.
</p>
<p><strong>Cost:</strong> Free when attached to a running instance. ~$0.005/hour only if the IP exists with no attached instance.</p>

<h2>The terraform.tfstate File</h2>
<p>
  After <code>terraform apply</code>, Terraform writes <code>terraform.tfstate</code> — a JSON file
  recording every resource it created and its current state (IDs, IPs, etc.).
</p>
<p><strong>This file is critical.</strong> If you lose it:</p>
<ul>
  <li>Terraform does not know the EC2 instance exists.</li>
  <li>Running <code>terraform apply</code> again creates <em>duplicate</em> resources.</li>
  <li>Running <code>terraform destroy</code> does nothing — it cannot find what to delete.</li>
</ul>
<p>
  Current setup: state stored locally in <code>terraform/terraform.tfstate</code> (gitignored).
  Back it up periodically. For team use, migrate to an S3 backend (the commented-out block in
  <code>providers.tf</code> shows how).
</p>

<h2>Common Commands</h2>
<table>
  <tr><th>Command</th><th>What it does</th></tr>
  <tr><td><code>terraform init</code></td><td>Downloads providers into <code>.terraform/</code>. Run once per machine.</td></tr>
  <tr><td><code>terraform plan</code></td><td>Shows what will be created/changed/deleted. Never makes changes.</td></tr>
  <tr><td><code>terraform apply</code></td><td>Creates/updates resources to match the <code>.tf</code> files.</td></tr>
  <tr><td><code>terraform destroy</code></td><td>Deletes all resources managed by this state file. Stops all charges.</td></tr>
  <tr><td><code>terraform output</code></td><td>Prints the output values (IP, SSH command) from the last apply.</td></tr>
  <tr><td><code>terraform state list</code></td><td>Lists all resources tracked in <code>terraform.tfstate</code>.</td></tr>
</table>

<h2>How to Maintain It</h2>

<h3>Day-to-day: do nothing</h3>
<p>
  Once deployed, the infrastructure just runs. GitHub Actions handles container updates via
  <code>docker run</code> on every push — you never need Terraform for normal deploys.
</p>

<h3>Changing infrastructure</h3>
<p>Example: open a new port in the Security Group.</p>
<ol>
  <li>Edit <code>main.tf</code> (add the new <code>ingress</code> rule).</li>
  <li>Run <code>terraform plan</code> — review the diff.</li>
  <li>Run <code>terraform apply</code> — AWS updates in-place, no downtime.</li>
</ol>

<h3>The golden rule</h3>
<p>
  <strong>Never manually change AWS resources via the Console.</strong> If you do, the next
  <code>terraform apply</code> reverts it back to what the <code>.tf</code> files say.
  All changes must go through the <code>.tf</code> files.
</p>

<h3>Tearing down to save money</h3>
<pre><code>cd terraform
terraform destroy</code></pre>
<p>
  Deletes everything: EC2, VPC, Elastic IP, Security Group. All AWS charges stop immediately.
  Re-running <code>terraform apply</code> recreates everything in ~2 minutes.
</p>

<h2>What Terraform Does NOT Manage</h2>
<table>
  <tr><th>What</th><th>How it is managed</th></tr>
  <tr><td>Docker container (RITA app)</td><td>GitHub Actions — <code>docker run</code> via SSH on every push to <code>master</code></td></tr>
  <tr><td>RITA data files</td><td>Manual <code>scp</code> upload once after <code>terraform apply</code></td></tr>
  <tr><td>GHCR package visibility</td><td>GitHub UI — set to Public once after first image push</td></tr>
  <tr><td>GitHub Secrets</td><td>GitHub UI — set once</td></tr>
  <tr><td><code>terraform.tfstate</code></td><td>Local file — back it up manually or migrate to S3 backend</td></tr>
</table>
"""

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = ConfluenceClient()

    print("Creating parent page...")
    parent_id, parent_url = client.create_page(
        PARENT_TITLE, PARENT_BODY, parent_id=SECTION["operations"]
    )
    print(f"  CREATED [{parent_id}] {parent_url}")

    print("Creating deployment guide page...")
    guide_id, guide_url = client.create_page(
        GUIDE_TITLE, GUIDE_BODY, parent_id=parent_id
    )
    print(f"  CREATED [{guide_id}] {guide_url}")

    print("Creating Terraform explained page...")
    tf_id, tf_url = client.create_page(
        TERRAFORM_TITLE, TERRAFORM_BODY, parent_id=parent_id
    )
    print(f"  CREATED [{tf_id}] {tf_url}")

    print("\nDone. All page IDs — save these for future updates:")
    print(f"  Parent:              {parent_id}")
    print(f"  Deployment Guide:    {guide_id}")
    print(f"  Terraform Explained: {tf_id}")
