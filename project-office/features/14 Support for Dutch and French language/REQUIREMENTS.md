# Feature 14 — Dutch and French Language Support (i18n)

**Status:** Requirements Draft  
**Date:** 2026-05-19  
**Owner:** San G  
**Approach:** /enhance multi-agent orchestration

---

## 1. Problem Statement

RITA's dashboard and mobile app are English-only. Users who prefer Dutch or French have no way to view UI labels in their language. This feature adds a three-language capsule (EN / NL / FR) to every page. Selecting a language instantly re-labels all static UI text — navigation, KPI labels, button text, section headings — without a page reload. The selection persists across sessions via `localStorage`.

---

## 2. Scope

**In scope:**
- Language capsule control (EN / NL / FR pill buttons) on all five dashboard pages and the mobile app
- Translations for: navigation labels, section headings, KPI card labels, button text, table column headers, status badge text, placeholder text, chart axis labels (where set by JS)
- Shared `i18n.js` module added to `dashboard/js/shared/` with `t(key)`, `setLanguage(lang)`, `getLanguage()`, `applyTranslations()`
- Three locale files: `dashboard/js/locales/en.js`, `nl.js`, `fr.js`
- Language choice persisted in `localStorage('ritaLanguage')`, default `'en'`
- Mobile app (`mobileapp/index.html`): inline i18n (no external modules — single-file constraint), same capsule pattern
- All five HTML files: `index.html`, `rita.html`, `fno.html`, `ops.html`, `ds.html` get `data-i18n` attributes on static text nodes and include the language capsule

**Out of scope:**
- Backend API responses — all data returned from the server (prices, instrument names, dates, status values from DB) remains as-is
- Chart data values and tick labels that come from API responses
- Error messages originating from the Python backend
- Right-to-left layout (neither Dutch nor French requires RTL)
- Machine translation of free-form commentary or chat responses
- Translating PDF/CSV exports

---

## 3. User Flow

```
Any dashboard page (rita.html / fno.html / ops.html / ds.html / index.html)
│
├─ User sees language capsule in top-right of header: [ EN | NL | FR ]
│   Active language is highlighted (accent fill, white text)
│
├─ User clicks "NL"
│   → setLanguage('nl') called
│   → localStorage('ritaLanguage') = 'nl'
│   → applyTranslations() iterates all [data-i18n] elements, replaces textContent
│   → Capsule highlights NL button
│
└─ User reloads page / navigates to another dashboard page
    → getLanguage() reads localStorage → 'nl'
    → applyTranslations() runs on DOMContentLoaded
    → Page loads in Dutch immediately
```

Mobile app (mobileapp/index.html):
```
Home screen (s0)
│
├─ Language capsule row below greeting: [ EN | NL | FR ]
│
├─ User taps "FR"
│   → setLanguage('fr'), localStorage persisted
│   → applyTranslations() runs — all screen labels update
│
└─ User swipes to any screen — labels remain in French
```

---

## 4. Architecture

### 4.1 Shared i18n Module — `dashboard/js/shared/i18n.js`

New shared module. Loaded by each page's `main.js`. No dependencies on other shared modules.

```js
// Exports
export function t(key)               // Returns translated string for current language; falls back to 'en' if key missing
export function setLanguage(lang)    // Sets active language ('en'|'nl'|'fr'), persists to localStorage, calls applyTranslations()
export function getLanguage()        // Returns current language from localStorage, default 'en'
export function applyTranslations()  // Iterates document.querySelectorAll('[data-i18n]'), sets textContent = t(element.dataset.i18n)
                                     // Also handles [data-i18n-placeholder] → sets element.placeholder
                                     // Also handles [data-i18n-title] → sets element.title
```

### 4.2 Locale Files — `dashboard/js/locales/`

Three ES module files, each a plain `export default { key: "string" }` object.

```
dashboard/js/locales/
├── en.js   ← English (source of truth for all keys)
├── nl.js   ← Dutch
└── fr.js   ← French
```

`i18n.js` imports all three statically and selects based on active language. No dynamic imports — avoids async complication in the module tree.

### 4.3 HTML Markup Convention

Static text nodes that must be translated get a `data-i18n="key"` attribute on their immediate container element.

```html
<!-- Before -->
<span class="nav-label">Market Signals</span>

<!-- After -->
<span class="nav-label" data-i18n="nav.market_signals">Market Signals</span>
```

- `textContent` of the element is set by `applyTranslations()` at runtime.
- The hardcoded English text in HTML serves as a visible fallback if JS hasn't loaded yet.
- For `<input>` placeholders: use `data-i18n-placeholder="key"` — `applyTranslations()` sets `.placeholder`.
- For `title` tooltip text: use `data-i18n-title="key"` — `applyTranslations()` sets `.title`.
- **Do not** add `data-i18n` to elements whose text is set entirely by JS (e.g., API-driven KPI values). Those use `t(key)` inline in the JS render function instead.

### 4.4 JS-rendered Labels

JS modules that build HTML strings (e.g., `health.js`, `trades.js`, `positions.js`) must import `t` and use it for static label text:

```js
import { t } from '../shared/i18n.js';

// Instead of:
setEl('kpi-sharpe-label', `<span class="label">Sharpe Ratio</span>`);

// Use:
setEl('kpi-sharpe-label', `<span class="label">${t('kpi.sharpe_ratio')}</span>`);
```

### 4.5 Language Capsule HTML Component

Each page's header area gets one capsule. Common CSS class — add to `dashboard/css/responsive.css`.

```html
<div class="lang-capsule" id="lang-capsule">
  <button class="lang-btn" onclick="setLanguage('en')" data-lang="en">EN</button>
  <button class="lang-btn" onclick="setLanguage('nl')" data-lang="nl">NL</button>
  <button class="lang-btn" onclick="setLanguage('fr')" data-lang="fr">FR</button>
</div>
```

Active state CSS — applied by `setLanguage()` toggling a class on the active button:

```css
.lang-capsule {
  display: inline-flex;
  border: 1px solid var(--border);
  border-radius: 20px;
  overflow: hidden;
  gap: 0;
}
.lang-btn {
  padding: 4px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  background: transparent;
  color: var(--text);
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.lang-btn.active {
  background: var(--build);
  color: #fff;
}
```

`setLanguage()` must:
1. Remove `.active` from all `.lang-btn` elements
2. Add `.active` to the button matching the new language (`[data-lang="${lang}"]`)
3. Persist to localStorage
4. Call `applyTranslations()`

`window.setLanguage` must be exposed (ES module constraint — same pattern as all other `onclick` handlers in the project).

### 4.6 Mobile App (Single-File Constraint)

`mobileapp/index.html` is a self-contained single file — no ES module imports. i18n must be implemented inline:

- Locale dictionaries as plain JS objects in a `<script>` block
- `t(key)`, `setLanguage(lang)`, `applyTranslations()` defined as plain functions (no modules)
- Language capsule added to the Home screen (s0) below the greeting
- Same `data-i18n` attribute convention on all screen labels

---

## 5. Translation Key Inventory

Keys are dot-namespaced by area. English values are the source of truth.

### 5.1 Navigation

| Key | EN | NL | FR |
|---|---|---|---|
| `nav.plan` | Plan | Plannen | Planifier |
| `nav.backtest` | Backtest | Backtest | Backtest |
| `nav.analyse` | Analyse | Analyseren | Analyser |
| `nav.monitor` | Monitor | Bewaken | Surveiller |
| `nav.agentic_ai` | Agentic AI | Agentische AI | IA Agentique |
| `nav.market_signals` | Market Signals | Marktsignalen | Signaux Marché |
| `nav.technical_analysis` | Technical Analysis | Technische Analyse | Analyse Technique |
| `nav.performance` | Performance | Prestaties | Performance |
| `nav.trades` | Trade Journal | Handelslogboek | Journal des Trades |
| `nav.risk` | Risk | Risico | Risque |
| `nav.training` | Training | Training | Entraînement |
| `nav.observability` | Observability | Observeerbaarheid | Observabilité |
| `nav.chat` | Chat | Chat | Chat |
| `nav.overview` | Overview | Overzicht | Vue d'ensemble |
| `nav.positions` | Positions | Posities | Positions |
| `nav.greeks` | Greeks | Grieken | Grecques |
| `nav.margin` | Margin | Marge | Marge |
| `nav.payoff` | Payoff | Uitbetaling | Gain |
| `nav.stress` | Stress Test | Stresstest | Test de Stress |
| `nav.hedge` | Hedge Radar | Hedge Radar | Radar de Couverture |

### 5.2 KPI Labels (Common)

| Key | EN | NL | FR |
|---|---|---|---|
| `kpi.sharpe_ratio` | Sharpe Ratio | Sharpe Ratio | Ratio de Sharpe |
| `kpi.win_rate` | Win Rate | Winstpercentage | Taux de Gain |
| `kpi.total_return` | Total Return | Totaal Rendement | Rendement Total |
| `kpi.max_drawdown` | Max Drawdown | Max. Verlies | Perte Max. |
| `kpi.pnl` | P&L | W&V | P&P |
| `kpi.volatility` | Volatility | Volatiliteit | Volatilité |
| `kpi.alpha` | Alpha | Alpha | Alpha |
| `kpi.beta` | Beta | Beta | Bêta |
| `kpi.ytd_return` | YTD Return | Rendement JTD | Rendement YTD |
| `kpi.confidence` | Confidence | Betrouwbaarheid | Confiance |
| `kpi.regime` | Regime | Regime | Régime |
| `kpi.signal` | Signal | Signaal | Signal |
| `kpi.model_version` | Model Version | Modelversie | Version Modèle |
| `kpi.training_rounds` | Rounds | Rondes | Tours |
| `kpi.timesteps` | Timesteps | Tijdstappen | Pas de Temps |

### 5.3 Button Labels

| Key | EN | NL | FR |
|---|---|---|---|
| `btn.run_goal` | Run Goal | Doel Uitvoeren | Exécuter l'Objectif |
| `btn.run_market` | Run Market | Markt Uitvoeren | Exécuter le Marché |
| `btn.run_strategy` | Run Strategy | Strategie Uitvoeren | Exécuter la Stratégie |
| `btn.run_pipeline` | Run Full Pipeline | Volledig Pipeline | Pipeline Complet |
| `btn.run_backtest` | Run Backtest | Backtest Starten | Lancer le Backtest |
| `btn.download` | Download | Downloaden | Télécharger |
| `btn.refresh` | Refresh | Vernieuwen | Actualiser |
| `btn.save` | Save | Opslaan | Enregistrer |
| `btn.reset` | Reset | Herstellen | Réinitialiser |
| `btn.approve` | Approve | Goedkeuren | Approuver |
| `btn.reject` | Reject | Afwijzen | Rejeter |
| `btn.send` | Send | Sturen | Envoyer |
| `btn.step` | Step | Stap | Étape |
| `btn.add` | Add | Toevoegen | Ajouter |

### 5.4 Status / Badge Labels

| Key | EN | NL | FR |
|---|---|---|---|
| `status.active` | Active | Actief | Actif |
| `status.paused` | Paused | Gepauzeerd | En Pause |
| `status.running` | Running | Actief | En Cours |
| `status.complete` | Complete | Voltooid | Terminé |
| `status.failed` | Failed | Mislukt | Échoué |
| `status.pending` | Pending | In Behandeling | En Attente |
| `status.live` | Live | Live | En Direct |
| `status.paper` | Paper | Papier | Papier |
| `status.bullish` | Bullish | Bullish | Haussier |
| `status.bearish` | Bearish | Bearish | Baissier |
| `status.neutral` | Neutral | Neutraal | Neutre |

### 5.5 Section Headings & Labels (Selected — full list in locale files)

| Key | EN | NL | FR |
|---|---|---|---|
| `heading.financial_goal` | Financial Goal | Financieel Doel | Objectif Financier |
| `heading.market_analysis` | Market Analysis | Marktanalyse | Analyse du Marché |
| `heading.strategy` | Strategy | Strategie | Stratégie |
| `heading.trade_journal` | Trade Journal | Handelslogboek | Journal des Trades |
| `heading.model_explain` | Model Explainability | Modelverklaring | Explicabilité du Modèle |
| `heading.live_risk` | Live Risk | Huidig Risico | Risque en Direct |
| `heading.agent_panel` | Agent Panel | Agentenpaneel | Panneau d'Agents |
| `heading.ai_compliance` | AI Compliance | AI-naleving | Conformité IA |
| `heading.portfolio` | Portfolio | Portefeuille | Portefeuille |
| `heading.open_positions` | Open Positions | Open Posities | Positions Ouvertes |

### 5.6 Mobile App Screens

| Key | EN | NL | FR |
|---|---|---|---|
| `mobile.home` | Home | Start | Accueil |
| `mobile.goal` | Goal | Doel | Objectif |
| `mobile.market` | Market | Markt | Marché |
| `mobile.signal_hero` | Signal | Signaal | Signal |
| `mobile.strategy` | Strategy | Strategie | Stratégie |
| `mobile.today` | Today | Vandaag | Aujourd'hui |
| `mobile.overview` | Overview | Overzicht | Vue d'ensemble |
| `mobile.market_feed` | Market Feed | Marktfeed | Flux de Marché |
| `mobile.portfolio` | Portfolio | Portefeuille | Portefeuille |
| `mobile.live_toggle` | Live | Live | En Direct |
| `mobile.greeting` | Good morning | Goedemorgen | Bonjour |

---

## 6. Files to Change

| File | Change |
|---|---|
| `dashboard/js/shared/i18n.js` | **NEW** — i18n module (`t`, `setLanguage`, `getLanguage`, `applyTranslations`) |
| `dashboard/js/locales/en.js` | **NEW** — English locale dictionary |
| `dashboard/js/locales/nl.js` | **NEW** — Dutch locale dictionary |
| `dashboard/js/locales/fr.js` | **NEW** — French locale dictionary |
| `dashboard/css/responsive.css` | Add `.lang-capsule` and `.lang-btn` styles |
| `dashboard/index.html` | Add capsule to header; `data-i18n` on nav tile labels |
| `dashboard/rita.html` | Add capsule to header; `data-i18n` on all static labels |
| `dashboard/fno.html` | Add capsule to header; `data-i18n` on all static labels |
| `dashboard/ops.html` | Add capsule to header; `data-i18n` on all static labels |
| `dashboard/ds.html` | Add capsule to header; `data-i18n` on all static labels |
| `dashboard/js/rita/main.js` | Import `i18n.js`; call `applyTranslations()` on load; expose `window.setLanguage` |
| `dashboard/js/fno/main.js` | Same |
| `dashboard/js/ops/main.js` | Same |
| `dashboard/js/ds/main.js` | Same |
| `dashboard/js/rita/*.js` (selected) | Import `t`; use in JS-rendered label strings (health, trades, risk, market-signals) |
| `dashboard/js/fno/*.js` (selected) | Import `t`; use in JS-rendered label strings (positions, dashboard, margin) |
| `dashboard/js/ops/*.js` (selected) | Import `t`; use in JS-rendered label strings (overview, agent-builds, daily-ops) |
| `riia-jun-release/mobileapp/index.html` | Inline locale dicts + i18n functions; add capsule to Home screen (s0); `data-i18n` on all 10 screen labels |

**Spec files to update in the same commit:**
- `project-office/specs/Spec_JS_Code.md` — add `shared/i18n.js` row to shared modules table; note `data-i18n` convention
- `project-office/specs/Spec_HTML_Code.md` — note language capsule placement per page
- `project-office/specs/Spec_Mobile_App.md` — note inline i18n pattern and capsule location

---

## 7. Implementation Phases

### Phase 1 — Infrastructure + Capsule (PM + Architect + Engineer)
- Create `i18n.js`, locale files, CSS styles
- Wire capsule into each page's `main.js`
- Add `data-i18n` to HTML static elements (nav, section headings, major button labels)
- Mobile app inline implementation
- **DoD:** Clicking NL/FR capsule on any page relabels nav + section headings. Reload retains choice.

### Phase 2 — JS-rendered Labels (Engineer + QA)
- Add `t()` calls to all JS modules that render HTML strings containing static label text
- **DoD:** KPI card labels, table column headers, and status badges all translate when language is switched, including after a section reload.

---

## 8. Acceptance Criteria

- [ ] Language capsule is visible on all six pages (index, rita, fno, ops, ds, mobile) in the header/top area
- [ ] Clicking EN, NL, or FR immediately relabels all static text on the current page without a page reload
- [ ] Active language button is visually highlighted (accent fill)
- [ ] Language choice persists: reload the page → labels are still in the last selected language
- [ ] Navigate from rita.html to fno.html → labels are already in the selected language on page load
- [ ] English fallback: if a translation key is missing in NL or FR, `t()` returns the English string (no blank labels)
- [ ] API-sourced values (prices, instrument names, dates) are unaffected by language switch
- [ ] Mobile app: capsule on Home screen; all 10 screens relabel correctly on language switch
- [ ] No regressions on existing JS functionality after i18n module import is added to `main.js` files
- [ ] Spec files updated in the same commit

---

## 9. Non-Goals / Future Work

- Server-side language detection (Accept-Language header)
- Additional languages (German, Hindi, etc.)
- Translating backend API error messages
- Automatic translation of the RITA Chat assistant responses
- Locale-aware number formatting (e.g., `1.234,56` Dutch style) — out of scope for this feature; current `fmt()` formatters unchanged
