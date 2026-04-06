// ── API loader ────────────────────────────────────────────────────────────────
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

// API key — set to match PORTFOLIO_API_KEY env var if configured.
// Leave empty string for local dev where the env var is not set.
export const RITA_API_KEY = '';

export async function initApp() {
  try {
    const resp = await fetch('/api/v1/portfolio/summary',
      RITA_API_KEY ? { headers: { 'X-API-Key': RITA_API_KEY } } : {});
    if (!resp.ok) throw new Error(`API ${resp.status}`);
    const d = await resp.json();

    state.marketData      = d.market || {};
    state.positions       = d.positions || [];
    buildExpiryPills();
    state.greeksData      = d.greeks || [];
    state.closedPositions = d.closed_positions || [];
    state.realizedPnl     = d.realized_pnl || 0;
    state.portDelta       = d.net_delta || {};
    state.netGreeks       = d.net_greeks || {};
    state.scenarioLevels  = d.scenario_levels || {};
    state.marginData      = d.margin || {};
    state.stressData      = d.stress || [];
    state.payoffData      = d.payoff || {};
    state.hedgeQuality    = d.hedge_quality || {};

    // Update sidebar
    const asOf = d.as_of || '';
    document.getElementById('sidebar-as-of').textContent = asOf ? `As of ${asOf}` : '';
    const nClose = (state.marketData.NIFTY || {}).close;
    const bClose = (state.marketData.BANKNIFTY || {}).close;
    if (nClose) document.getElementById('spot-nifty').textContent =
      `NIFTY  ${nClose.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    if (bClose) document.getElementById('spot-banknifty').textContent =
      `BNKN  ${bClose.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  } catch (e) {
    console.error('Portfolio API error:', e);
    document.getElementById('sidebar-as-of').textContent = 'API error — check server';
  }

  // Render all sections
  saveToday();
  syncPriceHistory().then(() => { renderScenarios(); renderDailyProgress(); });
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

export async function checkStatus() {
  try {
    const r = await fetch('/health');
    const d = await r.json();
    document.getElementById('sdot').className = d.status === 'ok' ? 'status-dot ok' : 'status-dot';
    document.getElementById('stxt').textContent = d.status === 'ok' ? 'API online' : 'API error';
  } catch {
    document.getElementById('sdot').className = 'status-dot';
    document.getElementById('stxt').textContent = 'API offline';
  }
}
