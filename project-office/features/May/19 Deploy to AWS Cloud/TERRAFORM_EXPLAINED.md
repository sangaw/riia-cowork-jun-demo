# Terraform Explained — RITA AWS Infrastructure

**What Terraform does, why each resource exists, and how to maintain it.**

---

## What Is Terraform?

Terraform is an **Infrastructure as Code (IaC)** tool. Instead of clicking through the AWS Console to create servers and networks, you write what you want in `.tf` files and Terraform creates, updates, or deletes the real AWS resources to match.

The key idea: **Terraform is declarative.** You describe the *desired end state*, not the steps to get there. Terraform figures out what needs to be created, changed, or deleted.

```
Your .tf files  ──► terraform apply  ──► Real AWS resources
(desired state)                          (actual state)
                         ▲
                   terraform.tfstate
                   (Terraform's memory of
                    what it already created)
```

---

## File Structure

```
terraform/
├── providers.tf          # Which cloud provider to use (AWS) and which version
├── variables.tf          # All configurable inputs (region, instance size, secrets)
├── main.tf               # The actual AWS resource definitions
├── outputs.tf            # Values printed after apply (IP address, SSH command)
├── terraform.tfvars      # YOUR actual values — gitignored, never commit this
├── terraform.tfvars.example  # Safe example to commit — shows what values are needed
├── terraform.tfstate     # Terraform's record of what it created — keep this safe
└── generated-key.pem     # SSH private key written by Terraform after apply — gitignored
```

---

## What Each File Does

### `providers.tf` — The Cloud Connection

```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
    tls = { source = "hashicorp/tls", version = "~> 4.0" }
  }
}

provider "aws" {
  region = var.aws_region
}
```

**What it does:**
- Declares that we're using AWS and the `tls` provider (for SSH key generation)
- Pins provider versions so your infrastructure doesn't break when AWS releases a new API
- Reads AWS credentials from `~/.aws/credentials` (set by `aws configure`) — no keys in code

**`terraform init` downloads** the `hashicorp/aws` and `hashicorp/tls` plugins into `.terraform/` locally.

---

### `variables.tf` — All the Dials

Variables are the configurable inputs to your infrastructure. They have defaults but can be overridden in `terraform.tfvars`.

| Variable | Default | Purpose |
|---|---|---|
| `aws_region` | `us-east-1` | Which AWS datacenter to deploy into |
| `rita_env` | `staging` | Value injected as an env var into the app |
| `jwt_secret` | *(required)* | JWT signing key for RITA's auth — sensitive |
| `google_client_id` | `CHANGE_ME` | Google OAuth client ID |
| `google_client_secret` | `CHANGE_ME` | Google OAuth client secret — sensitive |
| `vpc_cidr` | `10.0.0.0/16` | IP range for our private network |
| `subnet_cidr` | `10.0.1.0/24` | IP range for the public subnet inside the VPC |
| `instance_type` | `t2.micro` | EC2 server size |

**Sensitive variables** (marked `sensitive = true`) are never printed in terminal output even if you run `terraform output`.

---

### `main.tf` — Every AWS Resource Explained

#### 1. VPC — Your Private Network

```hcl
resource "aws_vpc" "rita" {
  cidr_block           = var.vpc_cidr   # 10.0.0.0/16
  enable_dns_hostnames = true
}
```

**What it is:** A Virtual Private Cloud is an isolated private network in AWS. Think of it as your own section of AWS's data center. Nothing outside can reach resources inside unless you explicitly open a door.

**Why:** AWS requires all EC2 instances to live inside a VPC. It's also a security boundary — only traffic you allow in the Security Group can reach your server.

---

#### 2. Internet Gateway — The Door to the Internet

```hcl
resource "aws_internet_gateway" "rita" {
  vpc_id = aws_vpc.rita.id
}
```

**What it is:** Attaches your VPC to the public internet.

**Why:** Without an Internet Gateway, your EC2 instance has no path to the internet — you couldn't SSH in, users couldn't access the dashboard, and GitHub Actions couldn't SSH to deploy.

---

#### 3. Subnet — A Segment of Your VPC

```hcl
resource "aws_subnet" "rita" {
  vpc_id                  = aws_vpc.rita.id
  cidr_block              = var.subnet_cidr     # 10.0.1.0/24
  map_public_ip_on_launch = true
}
```

**What it is:** A subdivision of the VPC. The EC2 instance lives in this subnet.

**Why:** VPCs are divided into subnets. `map_public_ip_on_launch = true` means EC2 instances in this subnet automatically get a public IP when they start (in addition to the static Elastic IP we add later).

---

#### 4. Route Table + Association — Traffic Rules

```hcl
resource "aws_route_table" "rita" {
  vpc_id = aws_vpc.rita.id
  route {
    cidr_block = "0.0.0.0/0"            # all traffic
    gateway_id = aws_internet_gateway.rita.id  # goes out via IGW
  }
}

resource "aws_route_table_association" "rita" {
  subnet_id      = aws_subnet.rita.id
  route_table_id = aws_route_table.rita.id
}
```

**What it is:** Routing rules telling traffic where to go. `0.0.0.0/0` means "all internet traffic goes out through the Internet Gateway."

**Why:** The Internet Gateway exists but traffic won't flow unless you also set the route. Think of it as: IGW = the door, route table = the sign saying "this way out."

---

#### 5. Security Group — The Firewall

```hcl
resource "aws_security_group" "rita" {
  ingress { from_port = 22,  to_port = 22,  ... cidr_blocks = ["0.0.0.0/0"] }  # SSH
  ingress { from_port = 80,  to_port = 80,  ... cidr_blocks = ["0.0.0.0/0"] }  # HTTP
  ingress { from_port = 443, to_port = 443, ... cidr_blocks = ["0.0.0.0/0"] }  # HTTPS
  egress  { from_port = 0,   to_port = 0,   protocol = "-1" ... }               # all outbound
}
```

**What it is:** A stateful firewall that controls what traffic can reach your EC2 instance.

**Why each rule:**
- Port 22 (SSH): GitHub Actions and you need to SSH in to deploy
- Port 80 (HTTP): Users access RITA dashboards on port 80
- Port 443 (HTTPS): Reserved for future SSL setup
- Egress all: The EC2 instance needs to reach the internet (pull Docker images from GHCR, send API responses)

> **Security note:** The `0.0.0.0/0` on port 22 means anyone can attempt SSH. This is safe because access requires the private key (`generated-key.pem`), which is not guessable. For production hardening you could restrict port 22 to your home IP.

---

#### 6. TLS Key Pair + AWS Key Pair + Local File — SSH Access

```hcl
resource "tls_private_key" "rita" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "rita" {
  key_name   = "rita-k3s-key"
  public_key = tls_private_key.rita.public_key_openssh
}

resource "local_file" "private_key" {
  content  = tls_private_key.rita.private_key_pem
  filename = "${path.module}/generated-key.pem"
  file_permission = "0400"
}
```

**What it is:** Generates an RSA-4096 SSH key pair. Uploads the public key to AWS. Writes the private key to `terraform/generated-key.pem` on your local machine.

**Why:** AWS requires a key pair to allow SSH access to EC2 instances. Terraform generates one automatically so you don't need to create it manually or store it in the repo.

**Important:** `generated-key.pem` is gitignored. It's your only way to SSH in — back it up somewhere safe.

---

#### 7. EC2 Instance — The Server

```hcl
resource "aws_instance" "rita" {
  ami           = data.aws_ami.ubuntu.id   # latest Ubuntu 22.04
  instance_type = var.instance_type        # t2.micro (free tier)
  subnet_id     = aws_subnet.rita.id
  vpc_security_group_ids = [aws_security_group.rita.id]
  key_name      = aws_key_pair.rita.key_name

  root_block_device {
    volume_size = 30    # GB — free tier limit
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    # Runs once on first boot
    mkdir -p /opt/rita_input /opt/rita_output
    chown -R ubuntu:ubuntu /opt/rita_input /opt/rita_output
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker ubuntu
    systemctl enable docker && systemctl start docker
  EOF
}
```

**What it is:** The virtual machine that runs the RITA container.

**`data.aws_ami.ubuntu`:** Terraform automatically looks up the latest Ubuntu 22.04 AMI ID for your region. You never need to hardcode AMI IDs.

**`user_data`:** A bash script that runs once on first boot via cloud-init. It creates the data directories and installs Docker. This is what makes the server self-configuring — you don't need to SSH in and manually install Docker.

**`gp3` volume:** General Purpose SSD. Faster than gp2 and same price. 30 GB is the free tier limit.

---

#### 8. Elastic IP — A Permanent Public Address

```hcl
resource "aws_eip" "rita" {
  instance = aws_instance.rita.id
  domain   = "vpc"
}
```

**What it is:** A static public IP address that stays the same even if the EC2 instance is stopped and restarted.

**Why:** EC2 instances get a new random public IP every time they restart. With an Elastic IP, your dashboard URL (`http://1.2.3.4/...`) never changes. GitHub Actions also uses this IP as the `AWS_EC2_IP` secret — it would break on every restart without it.

**Cost:** Elastic IPs are free when attached to a running instance. You're charged ~$0.005/hour only when the IP exists but has no attached instance.

---

### `outputs.tf` — Values Printed After Apply

```hcl
output "public_ip" {
  value = aws_eip.rita.public_ip
}

output "ssh_command" {
  value = "ssh -i generated-key.pem ubuntu@${aws_eip.rita.public_ip}"
}
```

After `terraform apply` finishes, these are printed in the terminal. You can also retrieve them later with:

```powershell
cd terraform
terraform output
```

---

### `terraform.tfstate` — Terraform's Memory

After `terraform apply`, Terraform writes `terraform.tfstate` — a JSON file recording every resource it created and its current state (IDs, IPs, etc.).

**This file is critical.** If you lose it:
- Terraform doesn't know the EC2 instance exists
- Running `terraform apply` again creates *duplicate* resources
- Running `terraform destroy` does nothing — it can't find what to delete
- You'd have to manually delete resources from the AWS Console

**Current setup:** State is stored locally in `terraform/terraform.tfstate`. This is gitignored (it can contain sensitive values).

**For the future:** The commented-out block in `providers.tf` shows how to store state in S3 instead, which is safer and allows team collaboration:

```hcl
backend "s3" {
  bucket = "rita-tfstate-123"
  key    = "terraform.tfstate"
  region = "us-east-1"
}
```

---

## Dependency Graph

Terraform works out the creation order automatically by following resource references:

```
aws_vpc
  └── aws_internet_gateway
  └── aws_subnet
        └── aws_route_table_association ← aws_route_table
  └── aws_security_group

tls_private_key
  ├── aws_key_pair
  └── local_file (generated-key.pem)

aws_instance  ← uses: aws_subnet, aws_security_group, aws_key_pair, data.aws_ami
  └── aws_eip
        └── outputs (public_ip, ssh_command)
```

---

## Common Terraform Commands

| Command | What it does |
|---|---|
| `terraform init` | Downloads providers into `.terraform/`. Run once per machine. |
| `terraform plan` | Shows what will be created/changed/deleted. Never makes changes. |
| `terraform apply` | Creates/updates resources to match the `.tf` files. |
| `terraform destroy` | Deletes all resources managed by this state file (stops charges). |
| `terraform output` | Prints the output values (IP, SSH command) from the last apply. |
| `terraform state list` | Lists all resources tracked in `terraform.tfstate`. |
| `terraform show` | Shows full details of every resource in the state file. |

---

## How to Maintain It

### Day-to-day: do nothing
Once deployed, the infrastructure just runs. GitHub Actions handles container updates — you never need to touch Terraform for normal code deploys.

### Changing infrastructure (e.g., opening a new port)
1. Edit the `.tf` file (e.g., add a new `ingress` rule to the security group)
2. `terraform plan` — review the diff
3. `terraform apply` — AWS updates the resource in-place; no downtime for security group changes

### Never manually change AWS resources via the Console
If you manually change something in the AWS Console (e.g., open port 8080 via the Console), Terraform doesn't know about it. The next `terraform apply` will revert it back to what the `.tf` files say. **All changes must go through the `.tf` files.**

### Backing up state
For a solo project, periodically copy `terraform.tfstate` somewhere safe (cloud storage, email to yourself). If your laptop dies and you lose this file, recovering is painful.

### Tearing down to save money
```powershell
cd terraform
terraform destroy
```
This deletes everything: EC2, VPC, Elastic IP, Security Group. All AWS charges stop immediately. Re-running `terraform apply` recreates everything from scratch in ~2 minutes.

### Upgrading provider versions
Periodically run `terraform init -upgrade` to get the latest `~> 5.0` patch release of the AWS provider. Then `terraform plan` to check nothing changed.

---

## What Terraform Does NOT Manage

These are handled outside of Terraform:

| What | How it's managed |
|---|---|
| Docker container (RITA app) | GitHub Actions — `docker run` via SSH on every push to `master` |
| RITA data files | Manual `scp` upload once after `terraform apply` |
| GHCR package visibility | GitHub UI — set to Public once after first image push |
| GitHub Secrets | GitHub UI — set once, never changes |
| `terraform.tfstate` | Local file — back it up manually |
