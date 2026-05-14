// ── Technical Analysis ─────────────────────────────────────
import { api } from './api.js';
import { setEl } from './utils.js';
import { mkChart, destroyChart, C } from './charts.js';

function _getInstrument() {
  return (localStorage.getItem('ritaInstrument') || 'NIFTY').toUpperCase();
}

function _stateClass(state) {
  if (state === 'bullish' || state === 'up')   return 'pos';
  if (state === 'bearish' || state === 'down') return 'neg';
  return 'neu';
}

function _renderCommentary(data) {
  const el = document.getElementById('ta-commentary');
  if (!el) return;

  const summaryHtml = data.signal_summary.length
    ? data.signal_summary.map(item =>
        `<span class="kpi-pill ${_stateClass(item.state)}" style="margin-right:10px;font-size:13px;padding:4px 10px">
          <strong>${item.label}</strong> ${item.value}
        </span>`
      ).join('')
    : '';

  el.innerHTML = `
    <div style="font-size:13px;color:#555;margin-bottom:10px">${data.instrument}</div>
    <div style="font-size:15px;line-height:1.6;margin-bottom:12px">${data.commentary}</div>
    <div>${summaryHtml}</div>
  `;
}

export async function loadTechnicalAnalysis() {
  const inst = _getInstrument();

  // ── Commentary panel ────────────────────────────────────
  try {
    const commentary = await api(`/api/experience/rita/technical-commentary?instrument=${inst}`);
    if (commentary) {
      _renderCommentary(commentary);
    } else {
      setEl('ta-commentary', '—');
    }
  } catch (e) {
    setEl('ta-commentary', '—');
  }

  // ── Chart data ───────────────────────────────────────────
  let rows = [];
  try {
    rows = await api(`/api/v1/market-signals?instrument=${inst}&timeframe=daily&periods=90`);
  } catch (e) {
    rows = [];
  }

  if (!rows || !rows.length) return;

  const dates = rows.map(r => r.date);

  // x-axis tick formatter (daily → MM-DD)
  const _xFmt   = v => typeof v === 'string' ? v.slice(5) : v;
  const _xTicks = 12;

  // ── Price + Volume chart ──────────────────────────────────
  try {
    mkChart('chart-ta-pv', {
      type: 'bar',
      data: {
        labels: dates,
        datasets: [
          { type: 'line', label: 'Close', data: rows.map(r => r.Close),
            borderColor: C.run, backgroundColor: 'transparent',
            pointRadius: 0, borderWidth: 2, yAxisID: 'yPrice', order: 1 },
          { type: 'bar', label: 'Volume', data: rows.map(r => r.Volume),
            backgroundColor: 'rgba(0,86,184,0.18)', borderWidth: 0,
            yAxisID: 'yVol', order: 2 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { size: 11 } } } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: _xTicks, callback: _xFmt, font: { family: C.mono, size: 10 } } },
          yPrice: { position: 'left',  grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(0), font: { family: C.mono, size: 10 } } },
          yVol:   { position: 'right', grid: { display: false }, ticks: { callback: v => v >= 1e7 ? (v/1e7).toFixed(0)+'Cr' : v >= 1e5 ? (v/1e5).toFixed(0)+'L' : v, font: { family: C.mono, size: 10 } } },
        }
      }
    });
  } catch (e) { /* chart render failed silently */ }

  // ── ATR% chart ────────────────────────────────────────────
  try {
    const atrPctData = rows.map(r => {
      const a = parseFloat(r.atr_14), c = parseFloat(r.Close);
      return (!isNaN(a) && !isNaN(c) && c) ? +(a / c * 100).toFixed(3) : null;
    });
    mkChart('chart-ta-atr', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'ATR%', data: atrPctData,
            borderColor: C.warn, backgroundColor: 'rgba(146,72,10,0.07)',
            fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          annotation: { annotations: {
            hiLine: { type: 'line', yMin: 1.5, yMax: 1.5, borderColor: 'rgba(155,28,28,0.55)', borderWidth: 1, borderDash: [4,3] },
            loLine: { type: 'line', yMin: 0.8, yMax: 0.8, borderColor: 'rgba(26,107,60,0.45)',  borderWidth: 1, borderDash: [4,3] },
          }}
        },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: _xTicks, callback: _xFmt, font: { family: C.mono, size: 10 } } },
          y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(1)+'%', font: { family: C.mono, size: 10 } } }
        }
      }
    });
  } catch (e) { /* chart render failed silently */ }

  // ── RSI-14 chart ──────────────────────────────────────────
  try {
    mkChart('chart-ta-rsi', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'RSI-14', data: rows.map(r => r.rsi_14),
            borderColor: C.run, backgroundColor: 'rgba(0,86,184,0.06)',
            fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          annotation: { annotations: {
            ob:  { type: 'line', yMin: 70, yMax: 70, borderColor: C.danger,               borderWidth: 1, borderDash: [4,3] },
            obz: { type: 'line', yMin: 60, yMax: 60, borderColor: 'rgba(180,40,40,0.4)',  borderWidth: 1, borderDash: [2,4] },
            os:  { type: 'line', yMin: 30, yMax: 30, borderColor: C.build,                borderWidth: 1, borderDash: [4,3] },
            osz: { type: 'line', yMin: 40, yMax: 40, borderColor: 'rgba(26,107,60,0.4)',  borderWidth: 1, borderDash: [2,4] },
          }}
        },
        scales: {
          x: { grid: { color: 'rgba(0,0,0,.03)' }, ticks: { maxTicksLimit: _xTicks, callback: _xFmt, font: { family: C.mono, size: 10 } } },
          y: { min: 0, max: 100, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v, font: { family: C.mono, size: 10 } } }
        }
      }
    });
  } catch (e) { /* chart render failed silently */ }
}
