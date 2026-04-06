// ── Scenarios ──────────────────────────────────────────────
import { api } from './api.js';
import { setEl } from './utils.js';
import { mkChart, chartOpts, C } from './charts.js';
import { loadHealth, loadProgress } from './health.js';

export function setScenarioPeriod(from, to) {
  document.getElementById('inp-bt-from').value = from;
  document.getElementById('inp-bt-to').value = to;
}

export async function loadScenarios() {
  // Show last backtest results on page load if available
  try {
    const perf  = await api('/api/v1/performance-summary');
    const daily = await api('/api/v1/backtest-daily');
    if (perf && typeof perf === 'object' && Object.keys(perf).length) renderScenarioResults(perf, daily);
  } catch (_) {}
}

export async function runScenarioBacktest() {
  const from = document.getElementById('inp-bt-from').value;
  const to   = document.getElementById('inp-bt-to').value;
  if (!from || !to)   { alert('Select both start and end dates.'); return; }
  if (from >= to)     { alert('Start date must be before end date.'); return; }

  const btn     = document.getElementById('btn-scenario');
  const spinner = document.getElementById('scenario-spinner');
  const badge   = document.getElementById('scenario-status');
  btn.disabled = true; btn.textContent = '⏳ Running…';
  spinner.style.display = '';
  badge.className = 'badge run'; badge.textContent = 'Running';
  setEl('scenario-result', '');

  try {
    await api('/api/v1/period',   'POST', { start: from, end: to });
    await api('/api/v1/backtest', 'POST', {});
    const [perf, daily] = await Promise.all([
      api('/api/v1/performance-summary'),
      api('/api/v1/backtest-daily'),
    ]);
    badge.className = 'badge ok'; badge.textContent = 'Done';
    renderScenarioResults(perf, daily, from, to);
    loadProgress(); loadHealth();
  } catch (e) {
    badge.className = 'badge err'; badge.textContent = 'Error';
    setEl('scenario-result', `<div class="result-panel"><div style="color:var(--danger);font-size:12px">Error: ${e.message}</div></div>`);
  } finally {
    btn.disabled = false; btn.textContent = '▶ Run Backtest';
    spinner.style.display = 'none';
  }
}

export function renderScenarioResults(perf, daily, from, to) {
  if (!perf || typeof perf !== 'object' || !Object.keys(perf).length) { setEl('scenario-result', '<div class="empty">No results.</div>'); return; }
  // perf is a flat dict {metric: value} from /api/v1/performance-summary
  const m = {};
  Object.entries(perf).forEach(([k, v]) => { m[k] = parseFloat(v); });

  const sharpe  = m.sharpe_ratio      != null ? m.sharpe_ratio.toFixed(3)            : '—';
  const mdd     = m.max_drawdown_pct  != null ? m.max_drawdown_pct.toFixed(2) + '%'  : '—';
  const ret     = m.portfolio_total_return_pct != null ? m.portfolio_total_return_pct.toFixed(2) + '%' : '—';
  const bnh     = m.benchmark_total_return_pct != null ? m.benchmark_total_return_pct.toFixed(2) + '%' : '—';
  const cagr    = m.portfolio_cagr_pct != null ? m.portfolio_cagr_pct.toFixed(2) + '%' : '—';
  const trades  = m.total_trades      != null ? m.total_trades                       : '—';
  const wr      = m.win_rate_pct      != null ? m.win_rate_pct.toFixed(1) + '%'      : '—';
  const days    = m.total_days        != null ? m.total_days                          : '—';
  const sharpeCls = parseFloat(m.sharpe_ratio) >= 1.0 ? 'pos' : 'neu';
  const mddCls    = Math.abs(parseFloat(m.max_drawdown_pct)) <= 5 ? 'pos' : 'warn';
  const label = (from && to) ? `${from} → ${to}` : 'Last backtest';

  let html = `
    <div class="card-hdr" style="margin-bottom:10px">
      <span class="card-title">Results — ${label}</span>
      <span class="badge ok" style="margin-left:8px">${days} days</span>
    </div>
    <div class="kpi-row-4" style="margin-bottom:14px">
      <div class="kpi"><div class="kpi-label">Sharpe Ratio</div><div class="kpi-value ${sharpeCls}">${sharpe}</div><div class="kpi-delta">target ≥ 1.0</div></div>
      <div class="kpi"><div class="kpi-label">Max Drawdown</div><div class="kpi-value ${mddCls}">${mdd}</div><div class="kpi-delta">target &lt; 10%</div></div>
      <div class="kpi"><div class="kpi-label">Portfolio Return</div><div class="kpi-value neu">${ret}</div><div class="kpi-delta">B&amp;H ${bnh}</div></div>
      <div class="kpi"><div class="kpi-label">CAGR</div><div class="kpi-value neu">${cagr}</div><div class="kpi-delta">${trades} trades · WR ${wr}</div></div>
    </div>`;

  if (daily && daily.length) {
    const labels = daily.map(r => r.date);
    const portVals = daily.map(r => r.portfolio_value != null ? ((parseFloat(r.portfolio_value) - 1) * 100).toFixed(2) : null);
    const bnhVals  = daily.map(r => r.benchmark_value  != null ? ((parseFloat(r.benchmark_value)  - 1) * 100).toFixed(2) : null);
    html += `<div class="chart-wrap"><div class="chart-title">Cumulative Return — RITA vs Buy &amp; Hold</div>
      <div class="chart-box"><canvas id="chart-scenario-returns"></canvas></div></div>`;
    setEl('scenario-result', html);
    mkChart('chart-scenario-returns', {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'RITA',      data: portVals, borderColor: C.build,  backgroundColor: 'rgba(26,107,60,0.07)', fill: true,  pointRadius: 0, borderWidth: 2 },
          { label: 'Nifty B&H', data: bnhVals,  borderColor: C.warn,   backgroundColor: 'transparent',          fill: false, pointRadius: 0, borderWidth: 1.5, borderDash: [4,3] },
        ],
      },
      options: chartOpts('Return (%)', v => v + '%', labels),
    });
  } else {
    setEl('scenario-result', html);
  }
}
