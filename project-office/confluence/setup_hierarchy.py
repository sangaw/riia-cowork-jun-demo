"""
One-time script: Creates the Confluence page hierarchy and moves existing pages.

Target hierarchy:
  RIIA-Project-Refactor (homepage 65110332)
  ├── Project Management
  │   ├── Master Plan
  │   ├── Sprint Planning and Metrics
  │   └── Sprint Boards/          (sub-pages added per sprint)
  ├── How We Work
  │   ├── Claude Cowork vs Human Team
  │   ├── Claude Cowork Setup Guide
  │   ├── How We Use Claude Cowork -- User Guide
  │   └── Token Budget and Daily Work Planning
  ├── Architecture and Design     (ADRs + schemas go here in Sprint 0)
  ├── Engineering Documentation   (API ref, service guide, security in Sprint 2-3)
  ├── Quality and Testing         (test strategy, coverage reports in Sprint 3-5)
  ├── Operations                  (runbooks, k8s, alerting in Sprint 3-5)
  └── Release Notes               (v1.0 release notes in Sprint 5)
"""
import sys, time
from pathlib import Path

# Inline the client here to avoid import path issues
import urllib.request, urllib.error, json, base64, os

EMAIL     = os.environ.get("CONFLUENCE_EMAIL", "")
BASE_URL  = os.environ.get("CONFLUENCE_BASE_URL", "https://ravionics.atlassian.net/wiki/rest/api")
SPACE_KEY = os.environ.get("CONFLUENCE_SPACE_KEY", "RIIAProjec")
HOMEPAGE_ID = "65110332"

def _load_token():
    if os.environ.get("CONFLUENCE_API_TOKEN"):
        return os.environ["CONFLUENCE_API_TOKEN"]
    key_file = Path(__file__).parent.parent.parent / "confluence-api-key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    raise RuntimeError("Set CONFLUENCE_API_TOKEN env var or place token in project root confluence-api-key.txt")

def _make_headers():
    token = _load_token()
    creds = base64.b64encode(f"{EMAIL}:{token}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json", "Accept": "application/json"}

def _req(method, path, body=None):
    headers = _make_headers()
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()), e.code

def create_page(title, body_html, parent_id=HOMEPAGE_ID):
    payload = {
        "type": "page", "title": title,
        "space": {"key": SPACE_KEY},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": body_html, "representation": "storage"}}
    }
    result, status = _req("POST", "/content", payload)
    if status in (200, 201):
        url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
        return result["id"], url
    raise RuntimeError(f"Create '{title}' HTTP {status}: {result.get('message','')[:100]}")

def move_page(page_id, new_parent_id):
    result, status = _req("GET", f"/content/{page_id}?expand=version,body.storage,ancestors")
    if status != 200:
        raise RuntimeError(f"GET {page_id} failed: HTTP {status}")
    payload = {
        "version": {"number": result["version"]["number"] + 1},
        "title": result["title"],
        "type": "page",
        "ancestors": [{"id": new_parent_id}],
        "body": {"storage": {
            "value": result["body"]["storage"]["value"],
            "representation": "storage"
        }}
    }
    r2, s2 = _req("PUT", f"/content/{page_id}", payload)
    if s2 == 200:
        print(f"  MOVED [{page_id}] '{result['title']}'")
    else:
        raise RuntimeError(f"Move {page_id} HTTP {s2}: {r2.get('message','')[:100]}")

# (using module-level functions defined above)

# ── Existing page IDs ─────────────────────────────────────────────────────────
EXISTING = {
    "master_plan":       "65110386",
    "token_budget":      "65273872",
    "cowork_user_guide": "65339404",
    "sprint_planning":   "65241094",
    "cowork_vs_human":   "65404929",
    "setup_guide":       "65241110",
    "project_context":   "65273857",
}

# ── Section descriptions (light placeholder pages — content added per sprint) ─
SECTIONS = [
    {
        "key": "project_management",
        "title": "Project Management",
        "body": """
<h1>Project Management</h1>
<p>Sprint planning, status tracking, metrics, and the master plan for the RITA production refactor.</p>
<ul>
  <li><strong>Master Plan</strong> -- full sprint roadmap, roles, risks, definition of done</li>
  <li><strong>Sprint Planning and Metrics</strong> -- how sprints are run, what we measure</li>
  <li><strong>Sprint Boards</strong> -- one sub-page per sprint with live task board</li>
</ul>
""",
        "move": ["master_plan", "sprint_planning", "project_context"],
    },
    {
        "key": "how_we_work",
        "title": "How We Work",
        "body": """
<h1>How We Work</h1>
<p>Everything about the Claude Cowork approach: why we use it, how it is set up, and what you need to do each day.</p>
<ul>
  <li><strong>Claude Cowork vs Human Team</strong> -- the case for this approach</li>
  <li><strong>Claude Cowork Setup Guide</strong> -- technical setup: CLAUDE.md, memory, worktrees, Confluence</li>
  <li><strong>How We Use Claude Cowork -- User Guide</strong> -- your daily routine and decision points</li>
  <li><strong>Token Budget and Daily Work Planning</strong> -- how we manage Claude Pro quota</li>
</ul>
""",
        "move": ["cowork_vs_human", "setup_guide", "cowork_user_guide", "token_budget"],
    },
    {
        "key": "architecture",
        "title": "Architecture and Design",
        "body": """
<h1>Architecture and Design</h1>
<p>Architecture Decision Records (ADRs), target system design, and data schemas. Created in Sprint 0.</p>
<ul>
  <li><strong>ADR-001</strong>: Three-Tier API Design (BFF / Business Process / System) -- Sprint 0</li>
  <li><strong>ADR-002</strong>: Repository Pattern (CSV v1 / PostgreSQL v2 swap-in) -- Sprint 0</li>
  <li><strong>ADR-003</strong>: Pydantic Settings and Config Hierarchy -- Sprint 1</li>
  <li><strong>ADR-004</strong>: Security Model (JWT, CORS, rate limiting) -- Sprint 1</li>
  <li><strong>ADR-005</strong>: Frontend Module Structure and Responsive Breakpoints -- Sprint 4</li>
  <li><strong>Data Schema Reference</strong>: All 15 CSV table schemas with field types -- Sprint 0</li>
</ul>
<p><em>Pages will be published here by the Technical Writer agent as each sprint completes.</em></p>
""",
        "move": [],
    },
    {
        "key": "engineering",
        "title": "Engineering Documentation",
        "body": """
<h1>Engineering Documentation</h1>
<p>API reference, service layer guide, security and config setup, repository contracts. Created in Sprints 1-3.</p>
<ul>
  <li><strong>Security and Config Guide</strong> -- Sprint 1</li>
  <li><strong>Repository Contracts</strong> -- Sprint 1</li>
  <li><strong>API Reference</strong> -- Sprint 2</li>
  <li><strong>Service Layer Guide</strong> -- Sprint 3</li>
  <li><strong>Frontend Architecture</strong> -- Sprint 4</li>
</ul>
<p><em>Pages will be published here by the Technical Writer agent as each sprint completes.</em></p>
""",
        "move": [],
    },
    {
        "key": "quality_testing",
        "title": "Quality and Testing",
        "body": """
<h1>Quality and Testing</h1>
<p>Test strategy, coverage reports, and QA runbooks. Created in Sprints 3-5.</p>
<ul>
  <li><strong>Test Strategy</strong> -- test pyramid, coverage targets, how to run -- Sprint 3</li>
  <li><strong>Coverage Reports</strong> -- published after each sprint QA run</li>
  <li><strong>End-to-End Test Guide</strong> -- Playwright setup and scenarios -- Sprint 4</li>
</ul>
<p><em>Pages will be published here by the QA agent and Technical Writer agent.</em></p>
""",
        "move": [],
    },
    {
        "key": "operations",
        "title": "Operations",
        "body": """
<h1>Operations</h1>
<p>Deployment, monitoring, alerting, and runbooks. Created in Sprints 3-5.</p>
<ul>
  <li><strong>Observability Runbook</strong> -- logs, metrics, alerts, dashboards -- Sprint 3</li>
  <li><strong>Operations Manual</strong> -- k8s deployment, rollback, secrets -- Sprint 5</li>
  <li><strong>CI/CD Pipeline Guide</strong> -- GitHub Actions workflow -- Sprint 1</li>
</ul>
<p><em>Pages will be published here by the Ops agent and Technical Writer agent.</em></p>
""",
        "move": [],
    },
    {
        "key": "release_notes",
        "title": "Release Notes",
        "body": """
<h1>Release Notes</h1>
<p>Release documentation for each RITA production version.</p>
<ul>
  <li><strong>Release v1.0</strong> -- what changed from POC, migration notes, known issues -- Sprint 5</li>
</ul>
<p><em>Pages will be published here by the Technical Writer agent at sprint 5.</em></p>
""",
        "move": [],
    },
]

# ── Sprint Boards placeholder ─────────────────────────────────────────────────
SPRINT_BOARDS_BODY = """
<h1>Sprint Boards</h1>
<p>One page per sprint showing the task board, daily progress, and sprint review.</p>
<p>Pages are created by the PM agent at the start of each sprint and updated daily.</p>
<ul>
  <li><strong>Sprint 0</strong>: Architecture and Planning -- Days 1-3</li>
  <li><strong>Sprint 1</strong>: Foundation -- Days 4-8</li>
  <li><strong>Sprint 2</strong>: API Decomposition -- Days 9-14</li>
  <li><strong>Sprint 3</strong>: Service Layer and Observability -- Days 15-20</li>
  <li><strong>Sprint 4</strong>: Frontend and Responsive Design -- Days 21-26</li>
  <li><strong>Sprint 5</strong>: Integration, Security and Release -- Days 27-30</li>
</ul>
"""

# ── Run ───────────────────────────────────────────────────────────────────────
print("\n=== Setting up Confluence hierarchy ===\n")

created_ids = {}

# 1. Create section parent pages under homepage
print("Creating section parent pages...")
for s in SECTIONS:
    try:
        page_id, url = create_page(s["title"], s["body"], parent_id=HOMEPAGE_ID)
        created_ids[s["key"]] = page_id
        print(f"  [{page_id}] {s['title']}")
    except RuntimeError as e:
        print(f"  ERROR {s['title']}: {e}")
    time.sleep(0.5)

# 2. Create Sprint Boards under Project Management
print("\nCreating Sprint Boards section...")
pm_id = created_ids.get("project_management")
if pm_id:
    try:
        sb_id, sb_url = create_page("Sprint Boards", SPRINT_BOARDS_BODY, parent_id=pm_id)
        created_ids["sprint_boards"] = sb_id
        print(f"  [{sb_id}] Sprint Boards (under Project Management)")
    except RuntimeError as e:
        print(f"  ERROR Sprint Boards: {e}")

# 3. Move existing pages to correct sections
print("\nMoving existing pages to sections...")
for s in SECTIONS:
    parent_id = created_ids.get(s["key"])
    if not parent_id:
        continue
    for page_key in s["move"]:
        page_id = EXISTING.get(page_key)
        if page_id:
            try:
                move_page(page_id, parent_id)
            except RuntimeError as e:
                print(f"  ERROR moving {page_key}: {e}")
            time.sleep(0.5)

# 4. Print final summary
print("\n=== Hierarchy created ===")
print(f"""
RIIA-Project-Refactor (homepage)
https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/overview

  [{created_ids.get('project_management')}] Project Management
      [65110386] Master Plan
      [65241094] Sprint Planning and Metrics
      [65273857] Project Context
      [{created_ids.get('sprint_boards')}] Sprint Boards

  [{created_ids.get('how_we_work')}] How We Work
      [65404929] Claude Cowork vs Human Team
      [65241110] Claude Cowork Setup Guide
      [65339404] How We Use Claude Cowork -- User Guide
      [65273872] Token Budget and Daily Work Planning

  [{created_ids.get('architecture')}] Architecture and Design
      (ADRs added in Sprint 0)

  [{created_ids.get('engineering')}] Engineering Documentation
      (guides added in Sprints 1-3)

  [{created_ids.get('quality_testing')}] Quality and Testing
      (reports added in Sprints 3-5)

  [{created_ids.get('operations')}] Operations
      (runbooks added in Sprints 3-5)

  [{created_ids.get('release_notes')}] Release Notes
      (v1.0 added in Sprint 5)
""")

# 5. Print IDs to paste into publish.py SECTION dict
print("Paste these into project_office/confluence/publish.py SECTION dict:")
for k, v in created_ids.items():
    print(f'    "{k}": "{v}",')
