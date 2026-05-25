// ── Strategy Comparison (Card 5 — Learnings) ─────────────────────────────────
// Runs 5 rule-based strategies against any instrument/year and renders a
// 7-panel Chart.js performance dashboard + summary table + AI commentary.
import { api } from './api.js';
import { apiFetch } from '../shared/api.js';
import { mkChart, C } from './charts.js';

// ── Module state ──────────────────────────────────────────────────────────────
let _scInstrument = 'NIFTY';
let _scYear = 2025;
const _INSTRUMENTS = [
  'NIFTY', 'BANKNIFTY', 'NVIDIA', 'ASML', 'AEX',
  'ASRNL', 'ATO', 'DJI', 'IXIC', 'RELIANCE', 'SBIN',
];
const _STRATEGY_COLORS = {
  'Buy and Hold':        C.run,
  'Value Investing':     C.build,
  'Momentum Investing':  C.warn,
  'Swing Trading':       C.mon,
  'Support-Resistance':  C.danger,
};

// ── Public API ────────────────────────────────────────────────────────────────

export async function loadStrategyComparison() {
  _renderPills();
  _renderYearToggle();
  await _fetchAndRender();
  _fireCommentary();
}

export function scSelectInstrument(id) {
  _scInstrument = id;
  document.querySelectorAll('.sc-pill').forEach(el => {
    el.classList.toggle('geo-kpi-active', el.dataset.id === id);
  });
  _fetchAndRender();
  _fireCommentary();
}

export function scSelectYear(year) {
  _scYear = Number(year);
  document.querySelectorAll('.sc-year-btn').forEach(el => {
    el.classList.toggle('sc-year-active', Number(el.dataset.year) === _scYear);
  });
  _fetchAndRender();
}

// ── Internal helpers ──────────────────────────────────────────────────────────

function _renderPills() {
  const container = document.getElementById('sc-pills');
  if (!container) return;
  container.innerHTML = _INSTRUMENTS.map(id => {
    const active = id === _scInstrument ? ' geo-kpi-active' : '';
    return `<button class="sc-pill geo-kpi${active}" data-id="${id}" onclick="scSelectInstrument('${id}')" style="padding:4px 12px;font-size:12px;font-weight:600;border-radius:100px;border:1.5px solid transparent;background:var(--surface2);cursor:pointer">${id}</button>`;
  }).join('');
}

function _renderYearToggle() {
  document.querySelectorAll('.sc-year-btn').forEach(el => {
    el.classList.toggle('sc-year-active', Number(el.dataset.year) === _scYear);
  });
}

async function _fetchAndRender() {
  const url = `/api/v1/experience/rita/strategy-comparison?instrument=${_scInstrument}&year=${_scYear}`;
  const data = await apiFetch(url);

  if (!data || data.error || !data.dates || data.dates.length === 0) {
    const msg = (data && data.error) ? data.error : 'No data available for this year.';
    _showError(msg);
    return;
  }

  _renderEquityCurve(data);
  _renderTotalReturns(data);
  _renderSharpe(data);
  _renderDrawdown(data);
  _renderFrequency(data);
  _renderAccuracy(data);
  _renderFinalValue(data);
  _renderSummaryTable(data);
}

function _showError(msg) {
  const ids = [
    'chart-sc-portfolio-growth', 'chart-sc-total-returns', 'chart-sc-sharpe',
    'chart-sc-drawdown', 'chart-sc-frequency', 'chart-sc-accuracy', 'chart-sc-final-value',
  ];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      const wrap = el.parentElement;
      if (wrap) wrap.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--t3);font-size:13px">${msg}</div>`;
    }
  });
  const tbl = document.getElementById('sc-summary-table');
  if (tbl) tbl.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--t3)">—</td></tr>`;
}

function _xFmt(v) {
  return typeof v === 'string' ? v.slice(5) : v;
}

function _datasets(data) {
  return (data.strategies || []).map(s => ({
    label: s.name,
    data: s.equity,
    borderColor: _STRATEGY_COLORS[s.name] || s.color || '#888',
    backgroundColor: 'transparent',
    fill: false,
    tension: 0.2,
    pointRadius: 0,
    borderWidth: 2,
  }));
}

function _renderEquityCurve(data) {
  mkChart('chart-sc-portfolio-growth', {
    type: 'line',
    data: { labels: data.dates, datasets: _datasets(data) },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { font: { size: 11 } } } },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 10, callback: _xFmt, font: { size: 10 } } },
        y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: { size: 10 }, callback: v => '$' + v.toFixed(0) } },
      },
    },
  });
}

function _hBar(id, label, values, names, colors, tickCb) {
  mkChart(id, {
    type: 'bar',
    data: { labels: names, datasets: [{ label, data: values, backgroundColor: colors, borderRadius: 3 }] },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { font: { size: 10 }, callback: tickCb } },
        y: { ticks: { font: { size: 10 } } },
      },
    },
  });
}

function _renderTotalReturns(data) {
  const names = (data.summary || []).map(s => s.name);
  _hBar('chart-sc-total-returns', 'Total Return %',
    names.map(n => (data.summary.find(s => s.name === n)?.total_return_pct || 0)),
    names, names.map(n => _STRATEGY_COLORS[n] || '#888'),
    v => v.toFixed(1) + '%');
}

function _renderSharpe(data) {
  const names = (data.summary || []).map(s => s.name);
  _hBar('chart-sc-sharpe', 'Sharpe Ratio',
    names.map(n => (data.summary.find(s => s.name === n)?.sharpe || 0)),
    names, names.map(n => _STRATEGY_COLORS[n] || '#888'),
    v => v.toFixed(2));
}

function _renderDrawdown(data) {
  const names = (data.summary || []).map(s => s.name);
  _hBar('chart-sc-drawdown', 'Max Drawdown %',
    names.map(n => (data.summary.find(s => s.name === n)?.max_drawdown_pct || 0)),
    names, names.map(n => _STRATEGY_COLORS[n] || '#888'),
    v => v.toFixed(1) + '%');
}

function _renderFrequency(data) {
  const names = (data.summary || []).map(s => s.name);
  _hBar('chart-sc-frequency', 'Number of Trades',
    names.map(n => (data.summary.find(s => s.name === n)?.n_trades || 0)),
    names, names.map(n => _STRATEGY_COLORS[n] || '#888'),
    v => v);
}

function _renderAccuracy(data) {
  const names = (data.summary || []).map(s => s.name);
  _hBar('chart-sc-accuracy', 'Win Rate %',
    names.map(n => (data.summary.find(s => s.name === n)?.win_rate_pct || 0)),
    names, names.map(n => _STRATEGY_COLORS[n] || '#888'),
    v => v + '%');
}

function _renderFinalValue(data) {
  const names = (data.summary || []).map(s => s.name);
  _hBar('chart-sc-final-value', 'Final Portfolio Value ($)',
    names.map(n => (data.summary.find(s => s.name === n)?.final_value || 0)),
    names, names.map(n => _STRATEGY_COLORS[n] || '#888'),
    v => '$' + v.toFixed(0));
}

function _renderSummaryTable(data) {
  const tbody = document.getElementById('sc-summary-table');
  if (!tbody) return;
  tbody.innerHTML = (data.summary || []).map(s => {
    const ret = (s.total_return_pct || 0).toFixed(2);
    const sharpe = (s.sharpe || 0).toFixed(2);
    const mdd = (s.max_drawdown_pct || 0).toFixed(2);
    const wr = (s.win_rate_pct || 0).toFixed(1);
    const fv = (s.final_value || 0).toFixed(2);
    const retColor = s.total_return_pct >= 0 ? 'var(--build)' : 'var(--danger)';
    const dot = _STRATEGY_COLORS[s.name] || '#888';
    return `<tr>
      <td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${dot};margin-right:6px;vertical-align:middle"></span>${s.name}</td>
      <td style="color:${retColor}">${ret}%</td>
      <td>${sharpe}</td>
      <td>${mdd}%</td>
      <td>${s.n_trades || 0}</td>
      <td>${wr}%</td>
      <td>$${fv}</td>
    </tr>`;
  }).join('');
}

async function _fireCommentary() {
  const titleEl = document.getElementById('sc-commentary-title');
  const textEl = document.getElementById('sc-commentary-text');
  const box = document.getElementById('sc-commentary-box');
  if (!textEl) return;
  if (titleEl) titleEl.textContent = 'Generating commentary…';
  if (box) box.style.display = 'block';
  textEl.textContent = '—';
  try {
    const res = await api('/api/v1/commentary', 'POST', {
      app: 'rita',
      page: 'strategy-comparison',
      instrument: _scInstrument,
    });
    if (res && res.commentary) {
      textEl.textContent = res.commentary;
      if (titleEl) titleEl.textContent = 'AI Commentary';
    }
  } catch (_) {
    textEl.textContent = '—';
    if (titleEl) titleEl.textContent = 'Commentary unavailable';
  }
}
