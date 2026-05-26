# Feature 17 — Mobile Device UI (Gateway + Auto-Redirect)

**Status:** Requirements Draft
**Date:** 2026-05-26
**Owner:** San G
**Approach:** /enhance multi-agent orchestration

---

## 1. Problem Statement

RITA has 5 desktop dashboards (RITA, FnO, Ops, Data Science, Invest Game) and a fully-built
mobile PWA at `/mobileapp`. However, there is **zero mobile detection** anywhere in the stack:

- The root `/` redirects all users — mobile or desktop — to `/dashboard`
- Mobile users who land on any desktop dashboard get a full desktop layout that does not fit their screen
- There is no signposted path from a mobile browser to the existing PWA
- Users must know `/mobileapp` exists and type it manually

The mobile PWA covers RITA core (signals, portfolio, market, goal, strategy) and the Invest
onboarding flow. Ops, FnO, and Data Science do not have mobile-optimised equivalents yet.

**Goal:** When a mobile device is detected, route the user to a purpose-built gateway page at
`/mobile` that clearly lists all apps, marks which are mobile-ready, and links desktop-only apps
with an explicit "open anyway" escape hatch.

---

## 2. Approach Selected — Option C: Mobile Gateway Page

Three options were evaluated:

| Option | Summary | Verdict |
|---|---|---|
| A | Root redirect + JS snippet on every dashboard | Simple but bounces mobile users to PWA with no context for Ops/FnO/DS |
| B | Responsive CSS on all 5 dashboards | Correct long-term; ~15,000 lines of CSS rework — not this sprint |
| **C** | **Mobile gateway hub at `/mobile`** | **Selected — honest UX, low risk, extensible** |

Option C adds a dedicated `/mobile` landing page that acts as a hub. Mobile users are routed
there automatically; the page clearly communicates which apps are mobile-ready and which are
desktop-only (with an escape hatch to open them anyway).

---

## 3. Scope

### In Scope

| Surface | Change |
|---|---|
| `src/rita/main.py` | Root `/` detects User-Agent → mobile → `/mobile`, desktop → `/dashboard`. New `/mobile` route serving `gateway.html`. |
| `riia-jun-release/mobileapp/gateway.html` | New gateway hub page (single HTML file, same design tokens as `index.html`) |
| `dashboard/rita.html` | Mobile-detect JS snippet in `<head>` |
| `dashboard/fno.html` | Mobile-detect JS snippet in `<head>` |
| `dashboard/ops.html` | Mobile-detect JS snippet in `<head>` |
| `dashboard/ds.html` | Mobile-detect JS snippet in `<head>` |
| `dashboard/investgame.html` | Mobile-detect JS snippet in `<head>` |
| `project-office/specs/Spec_Mobile_App.md` | Add Gateway section documenting `/mobile` route and detection logic |

### Out of Scope

- Making Ops, FnO, or Data Science dashboards responsive (Option B — future sprint)
- Adding new screens to the mobile PWA
- Tablet-specific layouts
- Native Android/iOS app packaging

---

## 4. Detailed Requirements

### 4.1 Server-Side Detection (`main.py`)

**R-S1:** The root `/` route must inspect the `User-Agent` request header.
- If the UA matches any of: `Android`, `iPhone`, `iPod`, `BlackBerry`, `IEMobile`, `Opera Mini` → redirect `302` to `/mobile`
- Otherwise → redirect `302` to `/dashboard` (current behaviour unchanged)

**R-S2:** A new `GET /mobile` route must serve `mobileapp/gateway.html` as a `FileResponse`.

**R-S3:** Detection regex must be case-insensitive. Pattern: `Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini`.

**R-S4:** The `/mobile` route must be registered **before** the `/mobileapp` static mount in `main.py` to avoid being shadowed.

---

### 4.2 Client-Side Detection Snippet (each desktop dashboard)

Each of the 5 desktop HTML files must include the following snippet as the **first `<script>` tag inside `<head>`**, before any other scripts:

```html
<script>
(function(){
  var p = new URLSearchParams(location.search);
  if (p.get('desktop') === '1') { sessionStorage.setItem('mobileBypass','1'); return; }
  if (sessionStorage.getItem('mobileBypass') === '1') return;
  var mobile = /Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  var narrow = window.innerWidth < 768 && window.matchMedia('(pointer:coarse)').matches;
  if (mobile || narrow) location.replace('/mobile?from=APPNAME');
})();
</script>
```

`APPNAME` values per file:

| File | APPNAME value |
|---|---|
| `rita.html` | `rita` |
| `fno.html` | `fno` |
| `ops.html` | `ops` |
| `ds.html` | `ds` |
| `investgame.html` | `investgame` |

**R-C1:** The snippet must run synchronously before the DOM renders to prevent flash of desktop layout.

**R-C2:** `?desktop=1` query param must set `sessionStorage.mobileBypass = '1'` and abort the redirect. This persists for the browser tab session — the user is not redirected again.

**R-C3:** The snippet must use `location.replace()` (not `location.href`) so the desktop dashboard does not appear in browser history.

**R-C4:** Detection uses **both** UA string and `(pointer:coarse)` + narrow viewport — this avoids false-positives on narrow desktop browser windows.

---

### 4.3 Gateway Page (`mobileapp/gateway.html`)

Single self-contained HTML file. No external JS dependencies. Uses the same CSS design tokens as `mobileapp/index.html` and `dashboard/index.html`.

#### 4.3.1 Layout

```
┌──────────────────────────────────────────┐
│  [RITA logo]        RIIA Platform        │
├──────────────────────────────────────────┤
│                                          │
│  Choose your app                         │
│  Optimised views for your device         │
│                                          │
│  ┌──────────────────┐ ┌────────────────┐ │
│  │ ● MOBILE READY   │ │ ● MOBILE READY │ │
│  │                  │ │                │ │
│  │  RITA Trading    │ │  Invest Game   │ │
│  │  Signals, port-  │ │  Paper trade   │ │
│  │  folio & regime  │ │  & learn       │ │
│  │                  │ │                │ │
│  │  [Open App →]    │ │  [Open App →]  │ │
│  └──────────────────┘ └────────────────┘ │
│                                          │
│  ┌──────────────────┐ ┌────────────────┐ │
│  │ ⚠ DESKTOP ONLY   │ │ ⚠ DESKTOP ONLY │ │
│  │                  │ │                │ │
│  │  FnO Portfolio   │ │  Ops Dashboard │ │
│  │  Greeks & P&L    │ │  Agent runs &  │ │
│  │  analysis        │ │  system health │ │
│  │                  │ │                │ │
│  │  [Open anyway ↗] │ │  [Open anyway] │ │
│  └──────────────────┘ └────────────────┘ │
│                                          │
│  ┌──────────────────────────────────────┐ │
│  │ ⚠ DESKTOP ONLY                       │ │
│  │  Data Science — model metrics, SHAP  │ │
│  │  [Open anyway ↗]                     │ │
│  └──────────────────────────────────────┘ │
│                                          │
│  ─────────────────────────────────────── │
│  View full desktop site ↗                │
└──────────────────────────────────────────┘
```

#### 4.3.2 App Cards

**R-G1: RITA Trading card**
- Badge: `MOBILE READY` (green — `--build` colour)
- Title: RITA Trading
- Description: RL-powered Nifty 50 signals, portfolio tracker & regime overview
- CTA button: `Open App →`
- Link: `/mobileapp`
- Accent bar: green (`--build`)

**R-G2: Invest Game card**
- Badge: `MOBILE READY` (green)
- Title: Invest Game
- Description: Paper-trade ASML & NVIDIA. Learn to invest alongside the AI.
- CTA button: `Open App →`
- Link: `/onboarding`
- Accent bar: green (`--build`)

**R-G3: FnO Portfolio card**
- Badge: `DESKTOP ONLY` (amber — `--warn` colour)
- Title: FnO Portfolio
- Description: Options Greeks, position management & P&L analysis. Best on a large screen.
- CTA link: `Open anyway ↗`
- Link: `/dashboard/fno.html?desktop=1`
- Accent bar: amber (`--warn`)
- Muted card styling (lower contrast body text)

**R-G4: Ops Dashboard card**
- Badge: `DESKTOP ONLY` (amber)
- Title: Ops Dashboard
- Description: Agent build runs, system health & API metrics. Best on a large screen.
- CTA link: `Open anyway ↗`
- Link: `/dashboard/ops.html?desktop=1`
- Accent bar: amber

**R-G5: Data Science card**
- Badge: `DESKTOP ONLY` (amber)
- Title: Data Science
- Description: Model training metrics, SHAP explainability & drift detection. Best on a large screen.
- CTA link: `Open anyway ↗`
- Link: `/dashboard/ds.html?desktop=1`
- Accent bar: amber

**R-G6: "View full desktop site" footer link**
- Plain text link at the bottom: `View full desktop site ↗`
- Link: `/dashboard?desktop=1`
- Allows users who prefer desktop on mobile to bypass all redirects

#### 4.3.3 Visual Design Rules

**R-G7:** Mobile-ready cards: full CTA button with solid green background (`--build`), white text.
**R-G8:** Desktop-only cards: text link with `↗` icon, amber colour (`--warn`), no filled button.
**R-G9:** 2-column card grid on screens ≥ 400 px; single column below 400 px.
**R-G10:** Cards use the same surface/border/shadow tokens as `index.html`.
**R-G11:** Page uses `--bg: #F5F3EE` background — matches PWA home screen.
**R-G12:** No external JS. No API calls. Page must render fully offline.
**R-G13:** Topbar shows RITA logo (left) + centred subtitle `RIIA Platform` (monospace, uppercase, muted).

---

### 4.4 Spec Update

**R-SP1:** `Spec_Mobile_App.md` must be updated in the same commit to document:
- The `/mobile` route and `gateway.html`
- The client-side detection snippet (standard pattern, copy-paste for new dashboards)
- The `?desktop=1` escape hatch convention

---

## 5. Detection Logic Summary

| Layer | Where | What it catches |
|---|---|---|
| Server UA check | `main.py` `/` | Users hitting the root URL on mobile |
| Client JS snippet | Each dashboard `<head>` | Users with bookmarked direct dashboard URLs |
| `?desktop=1` | All "Open anyway" links | Power users choosing desktop on mobile |
| `sessionStorage` | Client | Prevents redirect loop within a tab session |

---

## 6. Files Changed

| File | Action | Notes |
|---|---|---|
| `src/rita/main.py` | Modify | UA detection in `root()`, new `/mobile` route |
| `mobileapp/gateway.html` | **Create** | New gateway hub page |
| `dashboard/rita.html` | Modify | Add detection snippet to `<head>` |
| `dashboard/fno.html` | Modify | Add detection snippet to `<head>` |
| `dashboard/ops.html` | Modify | Add detection snippet to `<head>` |
| `dashboard/ds.html` | Modify | Add detection snippet to `<head>` |
| `dashboard/investgame.html` | Modify | Add detection snippet to `<head>` |
| `project-office/specs/Spec_Mobile_App.md` | Modify | Add Gateway + detection pattern section |

---

## 7. Definition of Done

| # | Check | Pass criteria |
|---|---|---|
| DoD-1 | Root redirect — desktop UA | `curl -H "User-Agent: Mozilla/5.0 (Macintosh)"` to `/` → 302 to `/dashboard` |
| DoD-2 | Root redirect — mobile UA | `curl -H "User-Agent: Mozilla/5.0 (Android)"` to `/` → 302 to `/mobile` |
| DoD-3 | `/mobile` route serves gateway | `GET /mobile` returns 200 with `gateway.html` content |
| DoD-4 | Gateway renders offline | Open `gateway.html` via `file://` — all 5 app cards visible, no JS errors |
| DoD-5 | RITA card links to PWA | Tap/click "Open App →" → navigates to `/mobileapp` |
| DoD-6 | Invest card links to onboarding | Tap/click "Open App →" → navigates to `/onboarding` |
| DoD-7 | Desktop-only cards link with escape | FnO/Ops/DS "Open anyway" links include `?desktop=1` |
| DoD-8 | Escape hatch works | Visit `/dashboard/rita.html?desktop=1` on mobile → stays on page, no redirect |
| DoD-9 | Session bypass persists | After escape hatch, navigate to `/dashboard/fno.html` in same tab → no redirect |
| DoD-10 | JS snippet present in all 5 dashboards | Grep confirms snippet in each file |
| DoD-11 | Spec_Mobile_App.md updated | Gateway section and detection pattern documented |
| DoD-12 | No regressions on desktop | Desktop browser: root `/` still goes to `/dashboard` |

---

## 8. Implementation Phases

| Phase | Agent | Tasks | Est. effort |
|---|---|---|---|
| Phase 1 | Engineer | `main.py`: UA detection + `/mobile` route | 30 min |
| Phase 2 | Engineer | Create `mobileapp/gateway.html` | 60 min |
| Phase 3 | Engineer | Add JS snippet to all 5 dashboard HTML files | 30 min |
| Phase 4 | Engineer | Update `Spec_Mobile_App.md` | 15 min |
| Phase 5 | QA | Verify all 12 DoD checks; browser test on real mobile UA | 30 min |

---

## 9. Notes / Decisions

- **2026-05-26:** Feature created. Option C selected over Option A (no context for non-RITA apps) and Option B (too much rework this sprint).
- **iPad / tablet:** Excluded from mobile detection intentionally. `pointer:coarse` + `innerWidth < 768` keeps tablets on the desktop path unless they have a known mobile UA string.
- **`investgame_v2.html`:** Not included in this feature — it is an experimental file not yet linked from the main nav. Add detection snippet when it is promoted.
- **Future work:** When Ops/FnO/DS get responsive CSS (Option B), update their gateway cards from `DESKTOP ONLY` to `MOBILE READY` and change the link target accordingly.
