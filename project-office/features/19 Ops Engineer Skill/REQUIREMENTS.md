# Feature 19 — Ops Engineer Skill + `/aws-production-deploy` Command

**Date:** 2026-05-23
**Status:** REQUIREMENTS

---

## Goal

Build a Claude Code skill (`ops-engineer`) and slash command (`/aws-production-deploy`) that give Claude a persistent, improving ops engineer persona for RITA production deployments. The skill accumulates learnings from past failures so every future deployment benefits from institutional memory.

---

## Two Deliverables

| Deliverable | File | Purpose |
|---|---|---|
| Ops Engineer skill | `project-office/skills/skill-ops-engineer.md` | Role card + deployment knowledge reference |
| Deploy command | `.claude/commands/aws-production-deploy.md` | Step-by-step deploy procedure callable via `/aws-production-deploy` |
| Knowledge base | `project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md` | Living log of deployment incidents, root causes, and prevention steps |

---

## Skill: `ops-engineer`

### Role

The Ops Engineer skill gives Claude a focused identity for all production operations work: syncing repos, triggering deployments, diagnosing failures, and updating the knowledge base after each incident.

### Trigger Conditions

Use this skill when the user asks to:
- Deploy to production (`/aws-production-deploy`)
- Diagnose a deployment failure or EC2 issue
- Check production health or container status
- SSH into EC2 for ops commands
- Update GitHub secrets or Actions config
- Add or fix anything in `riia-jun-release/.github/workflows/deploy.yaml`

### Skill Responsibilities

1. **Know the two-repo setup** — never confuse inner (dev) and outer (prod) repos
2. **Execute deployments safely** — sync both repos, validate before pushing to prod
3. **Consult the knowledge base first** — before any deployment step, check `DEPLOYMENT_KNOWLEDGE.md` for known failure patterns
4. **Update the knowledge base after incidents** — any new failure gets logged with symptom, root cause, fix, and prevention rule
5. **Never run `terraform` commands from inside `terraform/`** — always from `riia-jun-release/` root

### Two-Repo Reference (embedded in skill)

| | Dev repo (inner) | Prod repo (outer) |
|---|---|---|
| Local path | `riia-cowork-jun-demo/` | `riia-cowork-jun-demo/riia-jun-release/` |
| Remote | `github.com/sangaw/riia-cowork-jun-demo` | `github.com/san-work-ravionics/riia-jun-release-prod` |
| Push account | `sangaw` | `san-work-ravionics` (PAT in remote URL) |
| CI/CD | `ci.yml` — lint/test only | `deploy.yaml` — build Docker → push GHCR → deploy EC2 |
| Branch | `master` | `master` |

**Rule:** Code fixes that must go live are committed and pushed from `riia-jun-release/` only.

---

## Command: `/aws-production-deploy`

### What It Does

Runs a safe, validated production deployment by executing these phases in order:

### Phase 1 — Pre-flight

1. Check working directory is `riia-cowork-jun-demo/` (dev repo root)
2. Run `git status` on dev repo — abort if there are uncommitted changes that should go to prod
3. Run `git status` inside `riia-jun-release/` — report any uncommitted changes
4. Consult `DEPLOYMENT_KNOWLEDGE.md` for any active known issues or gotchas
5. Report current status to user before proceeding

### Phase 2 — Sync Inner Repo (dev)

1. `git pull origin master` in dev repo (`riia-cowork-jun-demo/`)
2. Report how many commits were pulled or confirm already up to date

### Phase 3 — Sync Outer Repo (prod)

1. `git pull origin master` inside `riia-jun-release/`
2. Report how many commits were pulled or confirm already up to date
3. If there are diverged commits: surface the diff to the user and ask whether to proceed

### Phase 4 — Stage and Commit (if there are local changes to deploy)

1. `git diff --stat` inside `riia-jun-release/` — show the user what will be committed
2. Ask user to confirm commit message (suggest one based on the diff)
3. `git add <specific files>` — never `git add -A` without user approval
4. `git commit -m "<message>"` — do not skip hooks

### Phase 5 — Push to Prod

1. `git push origin master` inside `riia-jun-release/`
2. Print the GitHub Actions URL to monitor: `https://github.com/san-work-ravionics/riia-jun-release-prod/actions`
3. Wait for user to confirm the action run has started

### Phase 6 — Health Check

1. Remind the user to poll: `curl http://<EC2_IP>/health`
2. Or ask user to open `https://riia.ravionics.nl/health` in browser
3. Confirm expected response: `{"status": "ok"}`

### Phase 7 — Post-Deploy

1. Ask user: "Did the deployment succeed? Any errors observed?"
2. If failures occurred: log them to `DEPLOYMENT_KNOWLEDGE.md` (symptom, root cause, fix, prevention rule)
3. If successful: log a brief success entry with commit SHA, date, and any notable changes

---

## Knowledge Base: `DEPLOYMENT_KNOWLEDGE.md`

### Purpose

A living document that the Ops Engineer skill reads before every deployment and writes to after every incident. Over time this becomes the institutional memory that prevents repeat failures.

### Structure

```markdown
# RITA Deployment Knowledge Base

## Active Gotchas (check before every deploy)
Short-lived warnings — e.g. "EC2 disk near full, prune images first"

## Known Failure Patterns

### [PATTERN-001] <Short title>
- **Symptom:** what the user/logs show
- **Root cause:** why it happens
- **Fix:** exact commands or steps that resolve it
- **Prevention:** rule to follow to avoid this in future
- **Date first seen:** YYYY-MM-DD
- **Recurrences:** N

## Successful Deploys Log
| Date | Commit | Notes |
```

### Seed Content

The knowledge base is pre-populated from all failures documented in `SPEC_Prod_Deploy.md` and `project-office/features/15 Deploy to AWS Cloud/PLAN_STATUS.md`. These 7 known patterns are the baseline:

| ID | Pattern |
|---|---|
| PATTERN-001 | Venv shebang paths invalid — `WORKDIR` must be `/app` in Dockerfile builder stage |
| PATTERN-002 | SSH heredoc with quoted delimiter breaks when secrets contain special chars — use unquoted `ENDSSH` |
| PATTERN-003 | EC2 can't pull GHCR image — `GHCR_PAT` secret missing or `docker login ghcr.io` step absent |
| PATTERN-004 | OAuth callback fails `Error 400` — `RITA_BASE_URL` set to `https://` but EC2 has no TLS cert |
| PATTERN-005 | Google OAuth callback 500 `at_hash` — `jwt.decode()` validates `at_hash` without `access_token`; use `get_unverified_claims()` |
| PATTERN-006 | Volume mount data not found — mount path mismatch between Dockerfile COPY target and bind mount |
| PATTERN-007 | Deploy not triggered — pushed to dev repo (`sangaw`) not prod repo (`san-work-ravionics`) |
| PATTERN-008 | `terraform destroy` run accidentally from `terraform/` while doing SSH/SCP ops — recovery took 45 min |

---

## Files to Create

| File | Phase |
|---|---|
| `project-office/skills/skill-ops-engineer.md` | Phase 1 |
| `project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md` | Phase 1 |
| `.claude/commands/aws-production-deploy.md` | Phase 2 |

---

## Definition of Done

- [ ] `skill-ops-engineer.md` written — role card, two-repo reference, knowledge base pointer, EC2 ops commands
- [ ] `DEPLOYMENT_KNOWLEDGE.md` written — 8 known failure patterns seeded from historical data
- [ ] `aws-production-deploy.md` command written — all 7 phases, correct repo paths, safety guards
- [ ] Command tested: user can type `/aws-production-deploy` and Claude executes the full flow
- [ ] After a real deployment: knowledge base updated with outcome entry
