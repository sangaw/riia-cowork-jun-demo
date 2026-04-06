// ── Performance charts ─────────────────────────────────────
import { api } from './api.js';
import { fmt, fmtPct, setEl } from './utils.js';
import { mkChart, chartOpts, C } from './charts.js';

export async function loadPerformance() {
  try {
    await loadPerfSummaryFull();
    const rows = await api('/api/v1/backtest-daily');
    if (!rows || !rows.length) {
      setEl('sec-performance', document.getElementById('sec-performance').innerHTML);
      return;
    }
    const dates = rows.map(r => r.date);
    const port = rows.map(r => ((r.portfolio_value || 1) - 1) * 100);
    const bench = rows.map(r => ((r.benchmark_value || 1) - 1) * 100);
    const alloc = rows.map(r => r.allocation);

    // Compute drawdown
    let peak = 1;
    const dd = rows.map(r => {
      const v = r.portfolio_value || 1;
      if (v > peak) peak = v;
      return peak > 0 ? ((v - peak) / peak) * 100 : 0;
    });

    mkChart('chart-returns', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'RITA', data: port, borderColor: C.run, backgroundColor: 'rgba(0,86,184,0.07)', fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2 },
          { label: 'Buy & Hold', data: bench, borderColor: C.warn, borderDash: [4, 3], fill: false, tension: 0.2, pointRadius: 0, borderWidth: 1.5 },
        ]
      },
      options: chartOpts('Returns (%)', v => v.toFixed(1) + '%', dates),
    });

    mkChart('chart-drawdown', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{ label: 'Drawdown', data: dd, borderColor: C.danger, backgroundColor: 'rgba(155,28,28,0.10)', fill: true, tension: 0.2, pointRadius: 0, borderWidth: 1.5 }]
      },
      options: chartOpts('Drawdown (%)', v => v.toFixed(2) + '%', dates),
    });

  } catch (e) {
    console.warn('performance load error', e);
  }
}

export async function loadPerfSummaryFull() {
  try {
    const d = await api('/api/v1/performance-summary');
    setEl('p-return', fmtPct(d.portfolio_total_return_pct));
    document.getElementById('p-return').className = 'kpi-value ' + (parseFloat(d.portfolio_total_return_pct) > 0 ? 'pos' : 'neg');
    setEl('p-return-bnh', 'B&H ' + fmtPct(d.benchmark_total_return_pct));
    setEl('p-cagr', fmtPct(d.portfolio_cagr_pct));
    setEl('p-cagr-bnh', 'B&H ' + fmtPct(d.benchmark_cagr_pct));
    setEl('p-sharpe', fmt(d.sharpe_ratio, 3));
    document.getElementById('p-sharpe').className = 'kpi-value ' + (parseFloat(d.sharpe_ratio) >= 1 ? 'pos' : 'neg');
    setEl('p-mdd', fmtPct(d.max_drawdown_pct));
    document.getElementById('p-mdd').className = 'kpi-value ' + (Math.abs(parseFloat(d.max_drawdown_pct)) < 10 ? 'pos' : 'neg');
    setEl('p-vol', fmtPct(d.annual_volatility_pct));
    setEl('p-wr', fmtPct(d.win_rate_pct));
    setEl('p-days', d.total_days + ' days');
    const met = String(d.constraints_met).toLowerCase() === 'true';
    setEl('p-constraints', met ? '<span class="badge ok">All Met</span>' : '<span class="badge err">Not Met</span>');
  } catch (e) { }
}
