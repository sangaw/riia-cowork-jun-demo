# Skill: End-of-Day Routine

## When to use this skill
Use when completing a sprint day — marking tasks done, updating the roadmap, publishing to Confluence, and committing all artifacts. All 4 steps are mandatory. Do not mark a day done until all 4 are complete.

---

## Step 1 — Update PLAN_STATUS.md

File: `riia-cowork-jun/PLAN_STATUS.md`

1. Find today's row in the sprint table (search for `| Day N |`)
2. Change `[ ]` to `[x]` in the Status column
3. Add a brief entry in the Notes column — what was actually delivered (e.g. "3 skill files + /fix-bug command committed")
4. Update the `**Last updated:**` date at the top to today's date
5. If this is the last day of a sprint, update the sprint header to `## Sprint N — COMPLETE`

---

## Step 2 — Update program-roadmap.html

File: `project-office/program-roadmap.html`

The file is large (~800 lines). Use targeted grep to find each section — **never read the full file**.

### Fields to update

| Field | How to find it | What to change |
|---|---|---|
| Overall % progress bar | `grep -n "overall-progress\|overall.*%" program-roadmap.html` | Update `width: X%` and the label text |
| Current sprint progress bar | `grep -n "sprint.*progress\|sprint-bar" program-roadmap.html` | Update `width: X%` |
| Days Done KPI | `grep -n "days-done\|Days Done" program-roadmap.html` | Increment the counter |
| Activity feed | `grep -n "activity-feed\|activity-log" program-roadmap.html` | Prepend one new `<li>` entry |
| Sprint badges | `grep -n "badge.*sprint\|sprint.*badge\|In Progress" program-roadmap.html` | Flip `In Progress` → `Done` if sprint just finished |

### Activity feed entry format
```html
<li><strong>YYYY-MM-DD</strong> — Day N: [brief description of what was delivered]</li>
```
Prepend to the top of the feed list — newest entry first.

### Progress % calculation
- Overall: `(days_completed / 42) * 100` — project is 42 days total
- Sprint bar: `(sprint_days_done / sprint_total_days) * 100`

---

## Step 3 — Publish Confluence Sprint Board

Identify the current sprint number N from PLAN_STATUS.md.

```bash
# Run from the workspace root: riia-cowork-jun/
CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/sprint-boards/publish_sprint{N}_board.py
```

The script must have today's day added to the deliverables section with status `Done` before running.

**If the script doesn't exist yet**, create it following the pattern from an existing sprint board script:
- Parent: `SECTION["sprint_boards"]` → `65077274`
- Add a row for today's deliverables with status `Done`
- Run `create_page()` on first run; hardcode the returned `PAGE_ID`; use `update_page()` on subsequent runs

**Confluence rules (never violate):**
- Plain HTML only — no `ac:structured-macro` tags (returns HTTP 400)
- Run from project root with `CONFLUENCE_EMAIL` env var set
- Hardcode `PAGE_ID` after first run — never leave it as `None`

---

## Step 4 — Git Commit

Stage all files changed today:
```bash
git add <specific files>   # never git add -A — list files explicitly
git status                 # verify only intended files are staged
```

Commit format:
```
<type>(<scope>): <what was delivered today>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Types: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `chore` (maintenance), `test` (tests), `refactor`

After committing:
```bash
git status   # must show: nothing to commit, working tree clean
git log --oneline -3   # confirm commit appears
```

---

## Guardrails

- **Never skip steps** — all 4 are mandatory every session
- **Do not mark the day done in PLAN_STATUS.md before steps 2, 3, 4 are done**
- **Do not commit until the app starts end-to-end** — `python riia-jun-release/start.py` must run without errors before committing code changes
- **Absolute dates only** — convert "today", "Thursday" etc. to `YYYY-MM-DD` in PLAN_STATUS.md notes
- **Do not push** — only commit locally unless the user explicitly asks to push

---

## Definition of Done

- [ ] PLAN_STATUS.md: today's row is `[x]`, notes column filled, Last updated date correct
- [ ] program-roadmap.html: overall %, sprint %, Days Done KPI, and activity feed all updated
- [ ] Confluence sprint board: today's row shows `Done`, script ran without HTTP errors
- [ ] Git: clean working tree, commit message matches format, no untracked files left
