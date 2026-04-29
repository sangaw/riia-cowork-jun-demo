# Confluence Script Improvements

## Fixes

### Fix 1 — Add `append_to_page()` to `publish.py` + clean up `update_requirements_mobile.py`
- `update_requirements_mobile.py` bypasses `client.update_page()` with a raw `_request("PUT")` and dead imports (`urllib.request`, `json`, `base64`, `BASE_URL`, `SPACE_KEY`)
- Root cause: `ConfluenceClient` has no append method
- Fix: add `append_to_page(page_id, html, title)` to `publish.py`; rewrite script to call it
- Status: [x] Done 2026-04-29

### Fix 2 — Add new page IDs to SECTION dict in `publish.py`
- `RL Trading Model` → `76677125`
- `ML Training Pipeline` → `76677141`
- Status: [x] Done 2026-04-29

### Fix 3 — Stale hardcoded page ID in `publish_arch_system_overview.py`
- Verified: both pages exist as siblings under Architecture and Design
  - `68911105` = "System Architecture Overview" (content page)
  - `76644368` = "Architecture" (current-state product doc)
- Added `"arch_system_overview": "68911105"` to SECTION dict
- Replaced hardcoded ID in script with `SECTION["arch_system_overview"]`
- Status: [x] Done 2026-04-29

### Fix 4 — Standardise `sys.path` convention
- Older scripts: `sys.path.insert(0, str(Path(__file__).parent.parent.parent))` — works from any dir
- Newer scripts: `sys.path.insert(0, os.path.abspath("project-office"))` — project root only
- Chat scripts also hardcode `CONFLUENCE_EMAIL` inline as fallback
- Fix: standardise all to the `Path(__file__)` form so scripts work from any directory
- Changed 4 files: publish_ml_rl_model_pages, publish_product_section, update_quality_testing, update_requirements_mobile
- Note: inline CONFLUENCE_EMAIL fallback in chat scripts left as-is (harmless, not worth the churn)
- Status: [x] Done 2026-04-29

### Fix 5 — Delete `_fetch_pages.py`
- Temp debug script created 2026-04-29, no ongoing purpose
- Status: [x] Done 2026-04-29

## Cleanup

### Cleanup A — Delete two orphaned markdown files
- `pages/chat_architecture_content.md` — content duplicated in `publish_chat_architecture.py`
- `pages/chat_engineering_content.md` — content duplicated in `publish_chat_engineering.py`
- Status: [x] Done 2026-04-29

### Cleanup B — Move diagnostic scripts to `tools/` subfolder
- `test_auth.py`, `test_create.py`, `check_trash.py`, `diagnose.py`
- Moved to `confluence/tools/`; updated sys.path from `parent.parent` to `parent.parent.parent`
- Status: [x] Done 2026-04-29

### Cleanup C — Document `setup_hierarchy.py` as one-time script
- Already has "One-time script:" in its docstring — no change needed
- Status: [x] Done (pre-existing) 2026-04-29

## Order of execution
1. Fix 5 (delete temp file) — trivial
2. Cleanup A (delete orphaned .md files) — trivial
3. Fix 2 (SECTION dict) — 2 lines
4. Fix 1 (append_to_page + clean mobile script) — highest value
5. Fix 3 (verify stale page ID) — needs Confluence API check
6. Fix 4 (sys.path standardisation) — touches many files, do last
7. Cleanup B (move diagnostics) — low priority
8. Cleanup C (setup_hierarchy docstring) — trivial
