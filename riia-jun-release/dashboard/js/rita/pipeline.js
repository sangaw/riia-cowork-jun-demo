// ── Pipeline result renderers ──────────────────────────────
import { badge, setEl } from './utils.js';
import { mkChart, C } from './charts.js';

export function renderGoalResult(containerId, d) {
  const r = d.result || d;
  const fv = (v, dec=1, sfx='') => (v != null && !isNaN(parseFloat(v))) ? parseFloat(v).toFixed(dec) + sfx : '—';
  const feasCls = {conservative:'ok', realistic:'ok', ambitious:'warn', unrealistic:'err'};
  const cls = feasCls[r.feasibility] || 'neu';

  const metrics = [
    {label:'Target Return',      value: fv(r.target_return_pct, 1, '%')},
    {label:'Time Horizon',       value: `${r.time_horizon_days ?? '—'}d (${fv(r.years, 2)}yr)`},
    {label:'Risk Tolerance',     value: r.risk_tolerance ? r.risk_tolerance.charAt(0).toUpperCase()+r.risk_tolerance.slice(1) : '—'},
    {label:'Annualized Target',  value: fv(r.annualized_target_pct, 2, '%')},
    {label:'Req. Monthly Ret.',  value: fv(r.required_monthly_return_pct, 3, '%')},
    {label:'Feasibility',        value: r.feasibility || '—', badge: cls},
    {label:'Suggested Target',   value: fv(r.suggested_realistic_target_pct, 1, '%')},
    {label:'Last 12m Return',    value: fv(r.last_12m_return_pct, 1, '%')},
  ];

  const mkMetric = m => `<div style="background:var(--surface);border:1.5px solid var(--border);border-radius:var(--r);padding:8px 12px">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--t3);margin-bottom:3px;white-space:nowrap">${m.label}</div>
    ${m.badge ? `<span class="badge ${m.badge}" style="font-size:11px;padding:2px 7px">${m.value}</span>` :
      `<div style="font-family:var(--fm);font-size:15px;font-weight:500;color:var(--text)">${m.value}</div>`}
  </div>`;

  let html = `<div class="result-panel">
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px">
      <div class="result-title" style="margin-bottom:0">Step ${d.step || 1} — ${d.name || 'Financial Goal'} <span class="badge ok">Done</span></div>
      ${r.feasibility_note ? `<span style="font-size:11px;color:var(--t3)">${r.feasibility_note}</span>` : ''}
    </div>
    <div style="display:grid;grid-template-columns:repeat(8,1fr);gap:6px;margin-bottom:10px">${metrics.map(mkMetric).join('')}</div>`;

  // 15-year annual returns chart
  if (r.yearly_returns && r.yearly_returns.length) {
    html += `<div class="chart-wrap" style="margin:0"><div class="chart-title">Nifty 50 Annual Returns — Last ${r.yearly_returns.length} Years
      <span style="font-weight:400;color:var(--t3);font-size:11px"> · <span style="color:var(--run)">─</span> Target <span style="color:var(--build)">─</span> Suggested</span>
    </div><div class="chart-box" style="height:200px"><canvas id="chart-goal-returns"></canvas></div></div>`;
  }
  html += '</div>';
  setEl(containerId, html);

  if (r.yearly_returns && r.yearly_returns.length) {
    const labels = r.yearly_returns.map(y => y.year);
    const vals   = r.yearly_returns.map(y => y.return_pct);
    mkChart('chart-goal-returns', {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Annual Return %', data: vals,
          backgroundColor: vals.map(v => v >= 0 ? 'rgba(26,107,60,0.55)' : 'rgba(155,28,28,0.55)'),
          borderColor:     vals.map(v => v >= 0 ? 'rgba(26,107,60,0.9)'  : 'rgba(155,28,28,0.9)'),
          borderWidth: 1.5 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          annotation: { annotations: {
            target:    { type:'line', yMin: r.target_return_pct,               yMax: r.target_return_pct,               borderColor: C.run,   borderWidth:1.5, borderDash:[5,3], label:{content:'Target',    display:true, position:'end', font:{size:10}} },
            suggested: { type:'line', yMin: r.suggested_realistic_target_pct,  yMax: r.suggested_realistic_target_pct,  borderColor: C.build, borderWidth:1.5, borderDash:[5,3], label:{content:'Suggested', display:true, position:'end', font:{size:10}} },
          }}
        },
        scales: {
          x: { grid:{display:false}, ticks:{font:{family:C.mono,size:10}} },
          y: { grid:{color:'rgba(0,0,0,.04)'}, ticks:{callback:v=>v.toFixed(0)+'%', font:{family:C.mono,size:10}} }
        }
      }
    });
  }
}

export function renderMarketResult(containerId, d) {
  const r = d.result || d;
  const fv = (v, dec=2) => (v != null && !isNaN(parseFloat(v))) ? parseFloat(v).toFixed(dec) : '—';
  const trendCls = {uptrend:'ok', sideways:'neu', downtrend:'err'};
  const macdCls  = {bullish:'ok', bearish:'err'};
  const rsiCls   = {overbought:'err', oversold:'ok', neutral:'neu'};
  const bbCls    = {near_upper_band:'err', near_lower_band:'ok', middle:'neu'};
  const sentCls  = {complacent:'ok', neutral:'neu', fearful:'err'};

  const mkRow = (label, value, note='') => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border);font-size:12px">
      <span style="color:var(--t3)">${label}</span>
      <span style="font-family:var(--fm);color:var(--text)">${value}${note ? ` <span style="color:var(--t4);font-size:10px">${note}</span>` : ''}</span>
    </div>`;
  const mkSection = (title, color, rows) => `
    <div style="background:var(--surface);border:1.5px solid var(--border);border-radius:var(--r);padding:12px 14px">
      <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:${color};margin-bottom:8px">${title}</div>
      ${rows}
    </div>`;

  const html = `<div class="result-panel">
    <div class="result-title">Step ${d.step||2} — ${d.name||'Market Analysis'} <span class="badge ok">Done</span></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px">
      ${mkSection('Trend &amp; Sentiment', 'var(--run)',
        mkRow('Date', r.date||'—') +
        mkRow('Close', r.close != null ? r.close.toLocaleString('en-IN') : '—') +
        mkRow('Trend', `<span class="badge ${trendCls[r.trend]||'neu'}">${r.trend||'—'}</span>`) +
        mkRow('Trend Score', fv(r.trend_score, 3), '(-1 bear → +1 bull)') +
        mkRow('Sentiment', `<span class="badge ${sentCls[r.sentiment_proxy]||'neu'}">${r.sentiment_proxy||'—'}</span>`)
      )}
      ${mkSection('RSI', 'var(--warn)',
        mkRow('RSI-14', fv(r.rsi_14, 2)) +
        mkRow('Signal', `<span class="badge ${rsiCls[r.rsi_signal]||'neu'}">${r.rsi_signal||'—'}</span>`) +
        mkRow('Range', '40–60 neutral zone', '') +
        mkRow('Overbought / Oversold', '&gt;70 / &lt;30')
      )}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
      ${mkSection('MACD', 'var(--build)',
        mkRow('MACD Line', fv(r.macd, 4)) +
        mkRow('Signal Line', fv(r.macd_signal_line, 4)) +
        mkRow('Signal', `<span class="badge ${macdCls[r.macd_signal]||'neu'}">${r.macd_signal||'—'}</span>`)
      )}
      ${mkSection('Bollinger Bands', 'var(--t2)',
        mkRow('BB %B', fv(r.bb_pct_b, 3)) +
        mkRow('Position', `<span class="badge ${bbCls[r.bb_position]||'neu'}">${(r.bb_position||'—').replace(/_/g,' ')}</span>`)
      )}
      ${mkSection('ATR', 'var(--mon)',
        mkRow('ATR-14', fv(r.atr_14, 2)) +
        mkRow('ATR Percentile', fv(r.atr_percentile, 3), '0=low · 1=high vol') +
        mkRow('EMA 5 / 13 / 26', `${fv(r.ema_5,0)} / ${fv(r.ema_13,0)} / ${fv(r.ema_26,0)}`)
      )}
    </div>
  </div>`;
  setEl(containerId, html);
}

export function renderStepResult(containerId, d) {
  const result = d.result || d;
  const rows = Object.entries(result).filter(([, v]) => typeof v !== 'object' || v === null);
  const nested = Object.entries(result).filter(([, v]) => typeof v === 'object' && v !== null);
  setEl(containerId, `
    <div class="result-panel">
      <div class="result-title">Step ${d.step || ''} — ${d.name || 'Result'} ${badge(d.status || 'ok')}</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:6px">
        ${rows.map(([k, v]) => `
          <div style="display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px solid var(--border);font-size:12px">
            <span style="color:var(--t3)">${k.replace(/_/g, ' ')}</span>
            <span style="font-family:var(--fm);color:var(--text)">${v != null ? String(v).slice(0, 60) : '—'}</span>
          </div>`).join('')}
      </div>
      ${nested.length ? `<details style="margin-top:10px"><summary style="font-size:11px;color:var(--t3);cursor:pointer">Nested data (${nested.length} keys)</summary><pre style="font-size:10px;color:var(--t3);margin-top:8px;white-space:pre-wrap">${JSON.stringify(Object.fromEntries(nested), null, 2)}</pre></details>` : ''}
    </div>`);
}
