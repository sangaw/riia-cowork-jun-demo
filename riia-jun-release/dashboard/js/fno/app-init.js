// ── FnO App Initialisation — extracted from fno/api.js god module ─────────────
// FC-IMP verified exports:
//   apiBase       — fno/api.js re-exports from shared/api.js ✓
//   RITA_API_KEY  — declared in fno/api.js ✓
//   state         — fno/state.js export const state ✓
//   buildExpiryPills — fno/nav.js export function buildExpiryPills ✓
//   renderDashboard, renderDailyProgress — fno/dashboard.js ✓
//   renderPositionsKpis, renderPositionsTable — fno/positions.js ✓
//   renderMarginKpis, updateMarginSections, renderMarginTables, renderClosedPositions — fno/margin.js ✓
//   renderGreeksCards, renderGreeksTable, updateRiskSections — fno/greeks.js ✓
//   renderStressScenarios — fno/stress.js ✓
//   renderPayoffChart — fno/payoff.js ✓
//   saveToday, syncPriceHistory, renderScenarios — fno/rr.js ✓
//   renderHedgeRadar — fno/hedge.js ✓
//   initManoeuvre — fno/manoeuvre.js ✓

import { apiBase, RITA_API_KEY } from './api.js';
import { state } from './state.js';
import { buildExpiryPills } from './nav.js';
import {
  renderDashboard,
  renderDailyProgress,
} from './dashboard.js';
import { renderPositionsKpis, renderPositionsTable } from './positions.js';
import {
  renderMarginKpis,
  updateMarginSections,
  renderMarginTables,
  renderClosedPositions,
} from './margin.js';
import { renderGreeksCards, renderGreeksTable, updateRiskSections } from './greeks.js';
import { renderStressScenarios } from './stress.js';
import { renderPayoffChart } from './payoff.js';
import { saveToday, syncPriceHistory, renderScenarios } from './rr.js';
import { renderHedgeRadar } from './hedge.js';
import { initManoeuvre } from './manoeuvre.js';

// window.RITA_API_BASE can be set by the host page to point at a non-origin
// API server (e.g. staging). Defaults to '' = same origin.

export async function initApp(mode = 'mock') {
  state.analyticsMode = mode;

  // Disable toggle during load
  const chk = document.getElementById('analytics-mode-chk');
  if (chk) chk.disabled = true;

  const url = apiBase() + `/api/v1/experience/fno/portfolio-analytics?mode=${mode}`;
  const headers = RITA_API_KEY ? { 'X-API-Key': RITA_API_KEY } : {};

  // Add JWT for real mode
  if (mode === 'real') {
    const token = sessionStorage.getItem('auth_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let rawResp = null;
  try {
    rawResp = await fetch(url, { headers });
  } catch (e) {
    console.error('Portfolio analytics fetch failed:', e);
    document.getElementById('sidebar-as-of').textContent = 'API error — check server';
    if (chk) chk.disabled = false;
    _renderAll();
    return;
  }

  if (!rawResp.ok) {
    if (mode === 'real') {
      const errEl = document.getElementById('analytics-mode-error');
      if (rawResp.status === 401) {
        if (errEl) { errEl.textContent = 'Login required for Real mode'; errEl.style.display = ''; }
        if (chk) { chk.checked = false; chk.disabled = false; }
        return initApp('mock');
      } else if (rawResp.status === 404) {
        if (errEl) { errEl.textContent = 'No portfolio configured'; errEl.style.display = ''; }
        if (chk) { chk.checked = false; chk.disabled = false; }
        return initApp('mock');
      }
    }
    console.error('Portfolio analytics API error:', rawResp.status);
    document.getElementById('sidebar-as-of').textContent = 'API error — check server';
    if (chk) chk.disabled = false;
    _renderAll();
    return;
  }

  let data;
  try {
    data = await rawResp.json();
  } catch (e) {
    console.error('Portfolio analytics JSON parse error:', e);
    document.getElementById('sidebar-as-of').textContent = 'API error — check server';
    if (chk) chk.disabled = false;
    _renderAll();
    return;
  }

  // Map all 13 response fields to state
  state.portfolioMeta    = data.portfolio_meta    || {};
  state.marketData       = data.market            || {};
  state.positions        = data.positions         || [];
  state.greeksData       = data.greeks            || [];
  state.netGreeks        = data.net_greeks        || {};
  state.portDelta        = data.net_delta         || {};
  state.scenarioLevels   = data.scenario_levels   || {};
  state.payoffData       = data.payoff            || {};
  state.stressData       = data.stress            || [];
  state.hedgeQuality     = data.hedge_quality     || {};
  state.closedPositions  = data.closed_positions  || [];
  state.realizedPnl      = data.realized_pnl      || 0;
  state.marginData       = data.margin            || {};

  // Update sidebar as-of timestamp
  const asOf = data.portfolio_meta?.updated_at || '—';
  const asOfEl = document.getElementById('sidebar-as-of');
  if (asOfEl) asOfEl.textContent = asOf !== '—' ? `Updated ${asOf}` : '';

  // Re-enable toggle
  if (chk) chk.disabled = false;

  buildExpiryPills();
  _renderAll();
  saveToday();
  syncPriceHistory().then(() => { renderScenarios(); renderDailyProgress(); });
}

function _renderAll() {
  renderDashboard();
  renderPositionsKpis();
  renderPositionsTable();
  renderClosedPositions();
  renderMarginKpis();
  updateMarginSections();
  renderMarginTables();
  updateRiskSections();
  renderGreeksCards();
  renderGreeksTable();
  renderStressScenarios();
  renderScenarios();
  renderPayoffChart();
  renderHedgeRadar();
  initManoeuvre();
}

// Backward-compat shim — main.js imports fetchPositions for the Paper/Live toggle.
// Delegates to initApp so the single-fetch architecture is preserved.
export async function fetchPositions() {
  return initApp(state.analyticsMode);
}

export async function checkStatus() {
  try {
    const r = await fetch(apiBase() + '/health');
    const d = await r.json();
    document.getElementById('sdot').className = d.status === 'ok' ? 'status-dot ok' : 'status-dot';
    document.getElementById('stxt').textContent = d.status === 'ok' ? 'API online' : 'API error';
  } catch {
    document.getElementById('sdot').className = 'status-dot';
    document.getElementById('stxt').textContent = 'API offline';
  }
}
