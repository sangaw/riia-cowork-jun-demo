// ── ASML Equity Hedge Scenarios ────────────────────────────────────────────────
import { state } from './state.js';
import { apiBase } from './api.js';

const RITA_API_KEY = '';

let _portfolioChart = null;
let _payoffChart = null;

function _fmtEur(v) {
  return '€' + Number(v).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export async function loadEquityHedge(forceRefresh = false) {
  if (state.equityHedgeData && !forceRefresh) {
    renderEquityHedge(state.equityHedgeData);
    return;
  }
  const loadEl = document.getElementById('eh-loading');
  const resEl  = document.getElementById('eh-results');
  if (loadEl) { loadEl.textContent = 'Loading…'; loadEl.style.display = 'flex'; }
  if (resEl)  resEl.style.display = 'none';

  const instrument = (document.getElementById('eh-instrument')?.value || 'ASML').trim().toUpperCase();
  const nShares    = parseInt(document.getElementById('eh-n-shares')?.value || '10', 10);
  const startDate  = document.getElementById('eh-start-date')?.value || '2025-01-01';
  const endDate    = document.getElementById('eh-end-date')?.value   || '2025-01-31';

  try {
    const headers = { 'Content-Type': 'application/json', ...(RITA_API_KEY ? { 'X-API-Key': RITA_API_KEY } : {}) };
    const resp = await fetch(apiBase() + '/api/v1/portfolio/equity-hedge-scenarios', {
      method: 'POST',
      headers,
      body: JSON.stringify({ instrument, n_shares: nShares, start_date: startDate, end_date: endDate }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    state.equityHedgeData = data;
    if (loadEl) loadEl.style.display = 'none';
    if (resEl)  resEl.style.display = 'block';
    renderEquityHedge(data);
  } catch (e) {
    if (loadEl) { loadEl.textContent = 'Error: ' + e.message; loadEl.style.display = 'flex'; }
    if (resEl)  resEl.style.display = 'none';
  }
}

export function renderEquityHedge(data) {
  const p   = data.portfolio;
  const hs  = data.hedge_scenarios;
  const mb  = hs.mild_bearish;
  const sb  = hs.strong_bearish;
  const pc  = hs.payoff_curves;

  // KPIs
  const retClass = p.return_pct >= 0 ? 'pos' : 'neg';
  const setKpi = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
  setKpi('eh-kpi-start-price', `<div class="kpi-value">${_fmtEur(p.start_price)}</div>`);
  setKpi('eh-kpi-end-price',   `<div class="kpi-value">${_fmtEur(p.end_price)}</div>`);
  setKpi('eh-kpi-return',      `<div class="kpi-value ${retClass}">${p.return_pct >= 0 ? '+' : ''}${p.return_pct.toFixed(2)}%</div>`);
  setKpi('eh-kpi-vol',         `<div class="kpi-value">${p.vol_30d_pct.toFixed(1)}%</div>`);

  // Covered Call card
  const setEl = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
  setEl('eh-cc-strike',    mb.strike_label);
  setEl('eh-cc-premium',   _fmtEur(mb.total_premium_eur));
  setEl('eh-cc-max-value', _fmtEur(mb.max_value_eur));
  setEl('eh-cc-breakeven', _fmtEur(mb.breakeven_price));
  setEl('eh-cc-desc',      mb.description);

  // Protective Put card
  setEl('eh-pp-strike',    sb.strike_label);
  setEl('eh-pp-premium',   _fmtEur(sb.total_premium_eur));
  setEl('eh-pp-floor',     _fmtEur(sb.floor_value_eur));
  setEl('eh-pp-breakeven', _fmtEur(sb.breakeven_price));
  setEl('eh-pp-desc',      sb.description);

  // Portfolio value chart
  if (_portfolioChart) { _portfolioChart.destroy(); _portfolioChart = null; }
  const portCtx = document.getElementById('eh-portfolio-chart');
  if (portCtx) {
    requestAnimationFrame(() => {
      _portfolioChart = new Chart(portCtx, {
        type: 'line',
        data: {
          labels: p.daily.map(d => d.date),
          datasets: [{
            label: `ASML × ${(document.getElementById('eh-n-shares')?.value || '10')} shares`,
            data: p.daily.map(d => d.value),
            borderColor: 'var(--p04)', backgroundColor: 'rgba(107,47,160,0.08)',
            borderWidth: 2, pointRadius: 2, tension: 0.3, fill: true,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { family: 'IBM Plex Mono', size: 10 }, maxTicksLimit: 8 } },
            y: { grid: { color: 'rgba(0,0,0,.05)' }, ticks: { font: { family: 'IBM Plex Mono', size: 10 }, callback: v => _fmtEur(v) } },
          },
        },
      });
    });
  }

  // Payoff comparison chart
  if (_payoffChart) { _payoffChart.destroy(); _payoffChart = null; }
  const payCtx = document.getElementById('eh-payoff-chart');
  if (payCtx) {
    requestAnimationFrame(() => {
      const xLabels = pc.price_range.map(v => _fmtEur(v));
      _payoffChart = new Chart(payCtx, {
        type: 'line',
        data: {
          labels: xLabels,
          datasets: [
            { label: 'Unhedged',       data: pc.unhedged,       borderColor: 'var(--p02)', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.2 },
            { label: 'Covered Call',   data: pc.covered_call,   borderColor: 'var(--p01)', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.2 },
            { label: 'Protective Put', data: pc.protective_put, borderColor: 'var(--neg)', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 0, tension: 0.2 },
            { label: 'Break-even',     data: Array(xLabels.length).fill(0), borderColor: 'rgba(0,0,0,0.2)', borderWidth: 1, borderDash: [4,3], pointRadius: 0, fill: false },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { position: 'top', labels: { font: { family: 'IBM Plex Mono', size: 11 }, boxWidth: 10 } },
            tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${_fmtEur(ctx.raw)}` } },
          },
          scales: {
            x: { grid: { display: false }, title: { display: true, text: 'ASML price at expiry', font: { family: 'IBM Plex Mono', size: 10 } }, ticks: { font: { family: 'IBM Plex Mono', size: 9 }, maxTicksLimit: 10 } },
            y: { grid: { color: 'rgba(0,0,0,.05)' }, ticks: { font: { family: 'IBM Plex Mono', size: 10 }, callback: v => _fmtEur(v) } },
          },
        },
      });
    });
  }
}
