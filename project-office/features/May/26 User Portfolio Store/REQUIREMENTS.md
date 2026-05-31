# Feature 26 — User Portfolio Store

**Created:** 2026-05-30  
**Owner:** Engineer  
**Status:** `[ ] Not started`  
**Guardrail refs:** org · engineer-role · rita-project  
**Affected specs:** Spec_RITA_App.md · Spec_DB.md · Spec_Python_Code.md · Spec_JS_Code.md · Spec_HTML_Code.md  
**Affected skills:** add-db-model · add-endpoint · add-rita-feature · add-fno-feature

---

## Objective

Allow a user to build a personal portfolio (instrument % allocations) inside the RITA app, save it via Google sign-in, and then see that saved portfolio when they log into the FnO app. The entire FnO app moves behind Google Auth. A new "My Portfolio" menu item is added to the FnO sidebar. Hedge analysis over the saved portfolio is deferred to a later feature.

---

## Background

RITA currently has no concept of a user-owned portfolio. The FnO app is open to any visitor. This feature closes both gaps: it adds a portfolio builder to RITA (Google sign-in triggered on save) and adds a Google-auth gate to the entire FnO app, with a new "My Portfolio" section in the FnO sidebar that displays the user's saved allocations. The hedge analysis layer will be added in a follow-on feature once this base is stable.

---

## Security Architecture — Table Isolation

Three-table design ensures that a query on either `users` or `user_portfolios` alone reveals nothing about the other side.

```
users (existing)               user_portfolio_keys (NEW)        user_portfolios (NEW)
─────────────────────          ──────────────────────────────   ─────────────────────────────────
id         ← email/Google sub  key_id   UUID PK ←────────────  key_id   UUID FK  (opaque — no email)
last_login_date                user_id  FK → users.id           portfolio_id UUID PK
first_login_date               created_at                       name  (optional label)
RBAC flags                                                       holdings  JSON  (list of {instrument_id, allocation_pct})
                                                                 created_at
                                                                 updated_at
                                                                 is_active  (soft-delete / replace on re-save)
```

- `user_portfolios` references only `key_id` (UUID) — no email, no Google data visible
- `users` has no reference to portfolios
- `user_portfolio_keys` is the only table that bridges both; never surfaced by the API
- **One portfolio per user** — saving a new portfolio soft-deletes the previous one and inserts a new row

---

## JWT Storage — sessionStorage (no cookies)

JWTs are stored in **`sessionStorage`** (key: `rita_token`):

- Survives page refresh and same-tab navigation (RITA → FnO)
- Automatically cleared when the browser tab/window is closed
- Not accessible from other tabs or browser restarts
- The OAuth callback delivers the token as a URL query param (`?token=…`); JS reads it, writes to `sessionStorage`, then strips it from the URL via `history.replaceState({}, '', location.pathname)`
- No tracking or advertising cookies are used anywhere on this platform
- Any existing `localStorage('rita_token')` references across all dashboard JS files must be migrated to `sessionStorage` as part of this feature

---

## Disclaimer Update — `dashboard/index.html`

The home page disclaimer must be updated to accurately reflect Google OAuth usage and sessionStorage (no cookies):

**Current text:**
> We use only essential functional cookies to improve user experience and platform performance, respecting privacy and data protection regulations.

**Replacement text:**
> Sign-in is handled via Google OAuth 2.0; no passwords are stored on this platform. We do not use tracking or advertising cookies. Session authentication is stored in your browser's session storage and is cleared automatically when you close the tab.

---

## Scope

### In Scope
- New `user_portfolio_keys` ORM model, repository, and Alembic migration
- New `user_portfolios` ORM model (one row per user; replace-on-save), repository, and migration
- `UserPortfolioService` — save/replace, get
- Workflow-tier API: `POST /api/v1/user-portfolio` (create/replace), `GET /api/v1/user-portfolio` — JWT-protected
- Experience-tier API: `GET /api/v1/experience/user-portfolio` — returns user's portfolio, JWT-protected, read-only
- **RITA frontend** — "My Portfolio" section: instrument allocation builder (like DS scenario page), save triggers Google auth if not logged in
- **FnO frontend** — entire FnO app behind Google Auth gate; new "My Portfolio" nav item (bottom of sidebar) with saved allocation view
- Auth callback update: `state` param controls post-auth redirect (`rita` → RITA, `fno` → FnO)
- `sessionStorage` migration for JWT across all dashboard JS
- Disclaimer update on `dashboard/index.html`

### Out of Scope
- Hedge analysis over the saved portfolio (Feature 27)
- Multiple portfolios per user
- Portfolio sharing, versioning, or history
- Mobile PWA portfolio view
- Real brokerage account sync

---

## Portfolio Data Model

**Holdings** — stored as a JSON array in `user_portfolios.holdings`:

```json
[
  { "instrument_id": "NIFTY",     "allocation_pct": 40 },
  { "instrument_id": "BANKNIFTY", "allocation_pct": 30 },
  { "instrument_id": "ASML",      "allocation_pct": 20 },
  { "instrument_id": "NVIDIA",    "allocation_pct": 10 }
]
```

- `allocation_pct` values must sum to 100 (validated in the service layer; API returns 422 if not)
- Available instruments are those returned by `GET /api/v1/experience/rita/geography-overview` (same set as the RITA Overview page; ATHER excluded)
- `name` is optional free-text; defaults to `"My Portfolio"` if blank

---

## Portfolio Builder UI — RITA App

Follows the pattern of the DS app scenario page:

1. Instrument grid — one card per active instrument (NIFTY, BANKNIFTY, ASML, NVIDIA)  
   Each card: instrument name, flag/exchange badge, % numeric input  
2. Allocation bar — live progress bar showing total % distributed (green = 100%, orange = over/under)  
3. "Save Portfolio" button — enabled only when allocations sum to 100%  
   - If JWT present in `sessionStorage` → `POST /api/v1/user-portfolio` directly  
   - If no JWT → redirect to `/auth/google/login?state=rita`; after callback, token stored and POST re-attempted  
4. Success state — "Portfolio saved" confirmation + summary of allocations  
5. If user already has a saved portfolio → pre-populate the sliders with existing allocations on section load

---

## FnO Auth Gate — Entire App

The entire FnO app (`fno.html`) requires Google sign-in:

- On `fno.html` load: read `sessionStorage('rita_token')`
- If absent/expired: render a full-page auth overlay — "Sign in with Google to continue" + button → `/auth/google/login?state=fno`
- After Google callback with `state=fno`: redirect to `/dashboard/fno.html?token=…`; JS reads token, stores in `sessionStorage`, strips from URL
- All FnO sections (Dashboard, Positions, Greeks, Hedge, Manoeuvre, Equity Hedge, My Portfolio) are protected by this gate

---

## FnO Sidebar — My Portfolio Nav Item

"My Portfolio" is added as a new nav item at the **bottom of the FnO sidebar**, after "Equity Hedge":

```
Dashboard
Positions
Greeks / Margin
Payoff
Stress
Risk-Reward
Hedge Radar
Manoeuvre
Equity Hedge
─────────────
My Portfolio    ← new
```

The section (`sec-my-portfolio`) displays:
- Allocation summary cards — one per instrument (name, flag, allocation %)
- Empty state with link to RITA builder if no portfolio exists
- Placeholder card: "Hedge recommendations coming soon" (greyed out) — reserved for Feature 27

---

## Full Codebase Change List

### New files
| File | Purpose |
|---|---|
| `src/rita/models/user_portfolio_key.py` | ORM — bridge table |
| `src/rita/models/user_portfolio.py` | ORM — portfolio data |
| `src/rita/schemas/user_portfolio.py` | Pydantic schemas |
| `src/rita/repositories/user_portfolio_key.py` | Repository |
| `src/rita/repositories/user_portfolio.py` | Repository |
| `src/rita/services/user_portfolio_service.py` | Business logic |
| `alembic/versions/<hash>_add_user_portfolio_tables.py` | DB migration |
| `src/rita/api/v1/workflow/user_portfolio.py` | Workflow-tier API |
| `src/rita/api/experience/user_portfolio.py` | Experience-tier API |
| `dashboard/js/rita/my-portfolio.js` | RITA portfolio builder module |
| `dashboard/js/fno/my-portfolio.js` | FnO portfolio display module |

### Modified files
| File | Change |
|---|---|
| `alembic/env.py` | Import two new models |
| `src/rita/main.py` | Import two new models; register two new routers |
| `src/rita/api/v1/auth.py` | Add `state` param to login; state-driven redirect on callback |
| `dashboard/index.html` | Update disclaimer text |
| `dashboard/rita.html` | Add `sec-my-portfolio` section + "My Portfolio" nav item |
| `dashboard/js/rita/nav.js` | Register `'my-portfolio'` loader |
| `dashboard/js/rita/main.js` | Token ingestion from `?token=` URL param → sessionStorage |
| `dashboard/fno.html` | Add auth overlay + `sec-my-portfolio` section + "My Portfolio" nav item |
| `dashboard/js/fno/main.js` | Auth gate on load; token ingestion from `?token=` URL param |
| `dashboard/js/fno/nav.js` | Register `'my-portfolio'` loader |
| Any rita/fno JS with `localStorage('rita_token')` | Migrate to `sessionStorage` |

**Total: 11 new files, ~11 modified files**

---

## Phases

### Phase 1 — Backend: DB Models, Repositories, Service

**Goal:** Establish the isolated data layer for user portfolios.

| Deliverable | Description |
|---|---|
| `src/rita/models/user_portfolio_key.py` | `UserPortfolioKeyModel` — `key_id UUID PK`, `user_id FK→users.id`, `created_at` |
| `src/rita/models/user_portfolio.py` | `UserPortfolioModel` — `portfolio_id UUID PK`, `key_id FK`, `name`, `holdings JSON`, `created_at`, `updated_at`, `is_active` |
| `src/rita/schemas/user_portfolio.py` | `HoldingItem(instrument_id, allocation_pct)`, `UserPortfolioCreate(name?, holdings)`, `UserPortfolioOut` |
| `src/rita/repositories/user_portfolio_key.py` | `find_or_create(user_id, db)` |
| `src/rita/repositories/user_portfolio.py` | `find_active_by_key_id(key_id)` |
| `src/rita/services/user_portfolio_service.py` | `save()` soft-deletes old + inserts new; `get()` |
| Alembic migration | Creates both tables; inspector-guarded |
| `alembic/env.py` + `main.py` | Import new models |

**Acceptance Criteria:**
- [ ] `alembic upgrade head` succeeds without error
- [ ] `SELECT * FROM user_portfolios` shows no email column
- [ ] Calling `save()` twice for same user → only one `is_active=true` row
- [ ] `get(user_id)` returns only that user's active portfolio

---

### Phase 2 — Backend: API Endpoints + Auth State Param

**Goal:** Expose portfolio save/get and update auth callback for state-driven redirects.

**Blocked on:** Phase 1

| Deliverable | Description |
|---|---|
| `src/rita/api/v1/workflow/user_portfolio.py` | `POST /api/v1/user-portfolio`, `GET /api/v1/user-portfolio` — both JWT-required |
| `src/rita/api/experience/user_portfolio.py` | `GET /api/v1/experience/user-portfolio` — JWT-required, read-only |
| `src/rita/api/v1/auth.py` | `state` param on login; callback redirects to `index.html` (rita/default) or `fno.html` (fno) |
| `main.py` | Register both new routers |

**Acceptance Criteria:**
- [ ] `POST /api/v1/user-portfolio` without JWT → 401; with valid JWT + sum=100 → 201
- [ ] Holdings not summing to 100 → 422
- [ ] `GET /api/v1/user-portfolio` → user's active portfolio or 404
- [ ] `/auth/google/login?state=fno` callback → `fno.html?token=…`
- [ ] `/auth/google/login?state=rita` callback → `index.html?token=…`

---

### Phase 3 — RITA Frontend: Portfolio Builder

**Goal:** Users can build and save their % allocation portfolio from within RITA.

**Blocked on:** Phase 2

| Deliverable | Description |
|---|---|
| `dashboard/js/rita/my-portfolio.js` | `loadMyPortfolio()`, `savePortfolio()`, `renderAllocationBuilder()`, `renderSavedPortfolio()` |
| `rita.html` | `sec-my-portfolio` section + "My Portfolio" nav item |
| `nav.js` | Register `'my-portfolio'` loader |
| `main.js` | Token ingestion: `?token=` → sessionStorage → strip URL |
| localStorage migration | Migrate any `localStorage('rita_token')` → `sessionStorage` |
| `index.html` | Update disclaimer text |

**Acceptance Criteria:**
- [ ] Instrument cards render for all active instruments from geography-overview (no ATHER)
- [ ] Allocation bar green at 100%, orange otherwise; Save button disabled when not 100%
- [ ] Unauthenticated save → Google redirect with `state=rita`; on return, portfolio saves automatically
- [ ] Returning authenticated user sees saved allocations pre-loaded
- [ ] Disclaimer updated on home page

---

### Phase 4 — FnO Frontend: Auth Gate + My Portfolio Section

**Goal:** FnO is fully auth-gated; logged-in users see their saved portfolio in a new sidebar section.

**Blocked on:** Phase 3

| Deliverable | Description |
|---|---|
| `fno.html` | Full-app auth overlay + `sec-my-portfolio` section + "My Portfolio" nav item (bottom of sidebar, after Equity Hedge) |
| `dashboard/js/fno/my-portfolio.js` | `loadMyPortfolio()`, `renderPortfolio(data)` — allocation cards + "Hedge coming soon" placeholder |
| `fno/main.js` | Auth gate on load; token ingestion from `?token=` URL param |
| `fno/nav.js` | Register `'my-portfolio'` loader |
| localStorage migration | Migrate any `localStorage` token refs in fno JS → `sessionStorage` |

**Acceptance Criteria:**
- [ ] `fno.html` without token → full-page auth overlay
- [ ] `state=fno` callback → `fno.html?token=…` → stored in sessionStorage, stripped from URL
- [ ] "My Portfolio" appears at bottom of FnO sidebar after "Equity Hedge"
- [ ] My Portfolio section shows allocation cards per instrument
- [ ] Empty state with RITA builder link when no portfolio exists
- [ ] No JWT in localStorage or cookies anywhere in fno JS

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 2 | Phase 1 |
| Phase 3 | Phase 2 |
| Phase 4 | Phase 3 |

---

## Definition of Done

- [ ] All phases complete with acceptance criteria checked
- [ ] `Spec_DB.md` updated — two new tables documented
- [ ] `Spec_RITA_App.md` updated — new endpoints, auth `state` param, new UI sections
- [ ] `Spec_JS_Code.md` updated — `my-portfolio.js` added for both rita/ and fno/
- [ ] `alembic upgrade head` runs clean in dev and prod
- [ ] `SELECT * FROM user_portfolios` shows no email or PII
- [ ] No JWT in `localStorage` or cookies in any dashboard JS
- [ ] Disclaimer updated on `index.html`
- [ ] Session committed to git
