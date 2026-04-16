// ── Trade Journal ──────────────────────────────────────────
import { api } from './api.js';
import { setEl } from './utils.js';
import { mkChart, chartOpts, C } from './charts.js';

export const TJ_PHASE = {
  Train:      { color: '#1565C0', bg: 'rgba(21,101,192,0.13)',  rowBg: '#E3F2FD' },
  Validation: { color: '#6A1B9A', bg: 'rgba(106,27,154,0.13)', rowBg: '#F3E5F5' },
  Backtest:   { color: '#2E7D32', bg: 'rgba(46,125,50,0.15)',   rowBg: '#E8F5E9' },
};
let _tjRows = [];  // cached for snapshot

export async function loadTrades() {
  try {
    const [rows, history] = await Promise.all([
      api('/api/v1/risk-timeline?phase=all'),
      api('/api/v1/training-history').catch(() => []),
    ]);
    if (!rows || !rows.length) {
      setEl('trades-table-wrap', '<div class="empty">No data — run pipeline first.</div>');
      return;
    }
    _tjRows = rows;
    document.getElementById('btn-tj-download').style.display = '';

    // ── Phase KPI strip ─────────────────────────────────────────────────────
    // Backtest phase: from risk-timeline rows
    const btRows = rows.filter(r => r.phase === 'Backtest');
    const kpiCards = [];

    // Train + Validation: synthesised from training-history records
    const runs = Array.isArray(history) ? history : [];
    if (runs.length) {
      // Latest training run for Train summary
      const latest = runs[0]; // history is newest-first
      const cfgTr = TJ_PHASE['Train'];
      const cfgVa = TJ_PHASE['Validation'];
      const _fv = v => (v != null && !isNaN(parseFloat(v))) ? parseFloat(v).toFixed(2) + '%' : '—';
      const _fs = v => (v != null && !isNaN(parseFloat(v))) ? parseFloat(v).toFixed(3) : '—';
      kpiCards.push(`<div style="border:1px solid ${cfgTr.color};border-radius:7px;padding:12px 14px;background:${cfgTr.bg}">
        <div style="font-weight:700;color:${cfgTr.color};margin-bottom:8px;font-size:12px">Train</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:11px">
          <div><span style="color:var(--t3)">Rounds</span><div style="font-weight:600">${runs.length}</div></div>
          <div><span style="color:var(--t3)">Algorithm</span><div style="font-weight:600">${latest.algorithm || 'DDQN'}</div></div>
          <div><span style="color:var(--t3)">Timesteps</span><div style="font-weight:600">${latest.timesteps ? (latest.timesteps/1000).toFixed(0)+'k' : '—'}</div></div>
          <div><span style="color:var(--t3)">Model ver</span><div style="font-weight:600">${latest.model_version || '—'}</div></div>
        </div>
      </div>`);
      kpiCards.push(`<div style="border:1px solid ${cfgVa.color};border-radius:7px;padding:12px 14px;background:${cfgVa.bg}">
        <div style="font-weight:700;color:${cfgVa.color};margin-bottom:8px;font-size:12px">Validation (latest run)</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:11px">
          <div><span style="color:var(--t3)">Sharpe</span><div style="font-weight:600">${_fs(latest.backtest_sharpe)}</div></div>
          <div><span style="color:var(--t3)">Max DD</span><div style="font-weight:600">${_fv(latest.backtest_mdd_pct)}</div></div>
          <div><span style="color:var(--t3)">Return</span><div style="font-weight:600">${_fv(latest.backtest_return_pct)}</div></div>
          <div><span style="color:var(--t3)">Status</span><div style="font-weight:600">${latest.status || '—'}</div></div>
        </div>
      </div>`);
    }

    // Backtest KPI card from risk-timeline rows
    if (btRows.length) {
      const cfg = TJ_PHASE['Backtest'];
      const cashDays = btRows.filter(r => parseFloat(r.allocation||0) === 0).length;
      const halfDays = btRows.filter(r => parseFloat(r.allocation||0) === 0.5).length;
      const fullDays = btRows.filter(r => parseFloat(r.allocation||0) === 1.0).length;
      const maxDD = Math.min(...btRows.map(r => parseFloat(r.current_drawdown_pct||0)));
      kpiCards.push(`<div style="border:1px solid ${cfg.color};border-radius:7px;padding:12px 14px;background:${cfg.bg}">
        <div style="font-weight:700;color:${cfg.color};margin-bottom:8px;font-size:12px">Backtest</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:11px">
          <div><span style="color:var(--t3)">Days</span><div style="font-weight:600">${btRows.length}</div></div>
          <div><span style="color:var(--t3)">Max DD</span><div style="font-weight:600">${maxDD.toFixed(2)}%</div></div>
          <div><span style="color:var(--t3)">Cash</span><div style="font-weight:600">${cashDays}d</div></div>
          <div><span style="color:var(--t3)">Half / Full</span><div style="font-weight:600">${halfDays}d / ${fullDays}d</div></div>
        </div>
      </div>`);
    }

    setEl('trades-kpi-strip', kpiCards.join(''));

    // ── Chart — one dataset per phase, string labels (no time adapter needed) ─
    const allDates = rows.map(r => r.date);
    const phaseByDate = {};
    rows.forEach(r => { phaseByDate[r.date] = r.phase; });

    const phases = Object.keys(TJ_PHASE);
    const datasets = phases.map(ph => {
      const cfg = TJ_PHASE[ph] || {};
      return {
        label: ph,
        data: rows.map(r => r.phase === ph && r.allocation != null ? parseFloat(r.allocation) * 100 : null),
        borderColor: cfg.color,
        backgroundColor: cfg.color,
        fill: false, stepped: false, pointRadius: 0, borderWidth: 2, spanGaps: false, tension: 0.3,
      };
    }).filter(d => d.data.some(v => v != null));

    mkChart('chart-allocation', {
      type: 'line',
      data: { labels: allDates, datasets },
      options: {
        ...chartOpts('Allocation (%)', v => v + '%', allDates),
        scales: {
          x: { ticks: { maxTicksLimit: 24, font: { family: C.mono, size: 10 } }, grid: { color: 'rgba(0,0,0,.04)' } },
          y: { min: 0, max: 110, ticks: { callback: v => v + '%', font: { family: C.mono, size: 10 } }, grid: { color: 'rgba(0,0,0,.04)' } },
        },
      },
    });

    // ── Table — all rows, color-coded by phase ─────────────────────────────
    setEl('trades-table-wrap', `
      <table>
        <thead><tr>
          <th>Date</th><th>Phase</th><th>Allocation</th>
          <th>Portfolio (norm)</th><th>Drawdown %</th><th>Regime</th>
        </tr></thead>
        <tbody>${rows.map(r => {
          const cfg = TJ_PHASE[r.phase] || {};
          const portPct = r.portfolio_value_norm != null ? ((parseFloat(r.portfolio_value_norm) - 1) * 100).toFixed(2) + '%' : '—';
          const dd = r.current_drawdown_pct != null ? parseFloat(r.current_drawdown_pct).toFixed(2) + '%' : '—';
          const ddColor = parseFloat(r.current_drawdown_pct||0) < -5 ? 'color:#9B1C1C;font-weight:600' : '';
          return `<tr>
            <td class="td-mono">${r.date || '—'}</td>
            <td><span style="font-size:10px;font-weight:700;color:${cfg.color || ''}">${r.phase || '—'}</span></td>
            <td>${allocBadge(r.allocation)}</td>
            <td class="td-mono">${portPct}</td>
            <td class="td-mono" style="${ddColor}">${dd}</td>
            <td style="font-size:11px;color:var(--t3)">${r.regime || '—'}</td>
          </tr>`;
        }).join('')}
        </tbody>
      </table>`);
  } catch (e) {
    setEl('trades-table-wrap', '<div class="empty">Error loading trade data.</div>');
  }
}

export function downloadTradeJournal() {
  if (!_tjRows.length) return;
  const cols = ['date','phase','allocation','portfolio_value_norm','current_drawdown_pct','regime'];
  const header = cols.join(',');
  const body = _tjRows.map(r => cols.map(c => r[c] ?? '').join(',')).join('\n');
  const ts = new Date().toISOString().slice(0,19).replace(/[-:T]/g, c => c === 'T' ? '_' : c);
  const blob = new Blob([header + '\n' + body], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `trade_journal_${ts}.csv`;
  a.click();
}

export function allocBadge(v) {
  if (v == null) return '<span class="badge neu">—</span>';
  const pct = parseFloat(v) * 100;
  if (pct === 0) return '<span class="badge warn">HOLD 0%</span>';
  if (pct === 50) return '<span class="badge run">HALF 50%</span>';
  if (pct >= 99) return '<span class="badge ok">FULL 100%</span>';
  return `<span class="badge neu">${pct.toFixed(0)}%</span>`;
}
