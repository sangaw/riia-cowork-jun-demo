// ── Health / Status ────────────────────────────────────────
import { api } from './api.js';
import { fmt, fmtPct, setEl } from './utils.js';
import { mkChart, C } from './charts.js';

export async function loadHealth() {
  try {
    const d = await api('/health');
    const dot = document.getElementById('status-dot');
    const txt = document.getElementById('status-text');
    dot.className = 'status-dot ok';
    txt.textContent = d.model_exists ? 'Model loaded' : 'API online';

    // Sidebar footer
    setEl('sb-model-info', d.model_exists
      ? `Model: ${d.model_age_days}d old`
      : 'Model: not trained');

    // Model status card
    const mb = d.model_exists ? '<span class="badge ok">Loaded</span>' : '<span class="badge warn">Not Found</span>';
    setEl('model-badge', d.model_exists ? 'Loaded' : 'Not Found');
    document.getElementById('model-badge').className = 'badge ' + (d.model_exists ? 'ok' : 'warn');
    setEl('model-details', `
      <div style="display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--t2)">
        <div style="display:flex;justify-content:space-between"><span>Model file</span><span class="badge ${d.model_exists ? 'ok' : 'err'}">${d.model_exists ? 'Present' : 'Missing'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Age</span><span style="font-family:var(--fm)">${d.model_age_days != null ? d.model_age_days + ' days' : '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Last run</span><span style="font-family:var(--fm);font-size:11px">${d.last_pipeline_run || '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>CSV loaded</span><span class="badge ${d.csv_loaded ? 'ok' : 'err'}">${d.csv_loaded ? 'Yes' : 'No'}</span></div>
      </div>
    `);

    // Data freshness
    const fresh = d.data_freshness || {};
    const daysOld = fresh.days_since_latest;
    const freshOk = daysOld != null && daysOld < 30;
    document.getElementById('data-badge').className = 'badge ' + (freshOk ? 'ok' : 'warn');
    setEl('data-badge', freshOk ? 'Fresh' : (daysOld != null ? daysOld + 'd old' : '—'));
    setEl('data-details', `
      <div style="display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--t2)">
        <div style="display:flex;justify-content:space-between"><span>Latest date</span><span style="font-family:var(--fm)">${fresh.latest_date || '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Days old</span><span style="font-family:var(--fm)">${daysOld != null ? daysOld : '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Status</span><span class="badge ${freshOk ? 'ok' : 'warn'}">${fresh.status || '—'}</span></div>
      </div>
    `);

    // Sharpe trend sparkline
    if (d.sharpe_trend_last5 && d.sharpe_trend_last5.length > 1) {
      document.getElementById('sharpe-trend-wrap').style.display = '';
      requestAnimationFrame(() => mkChart('chart-sharpe-trend', {
        type: 'line',
        data: {
          labels: d.sharpe_trend_last5.map((_, i) => 'R' + (i + 1)),
          datasets: [{
            data: d.sharpe_trend_last5,
            borderColor: C.run,
            backgroundColor: 'rgba(0,86,184,0.08)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: C.run,
            borderWidth: 2,
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: 'rgba(0,0,0,.04)' } },
            y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(3) } }
          }
        }
      }));
    }
  } catch (e) {
    const dot = document.getElementById('status-dot');
    dot.className = 'status-dot err';
    document.getElementById('status-text').textContent = 'API offline';
  }
}

export async function loadMetrics() {
  try {
    const [d, prog] = await Promise.all([api('/api/v1/metrics/summary'), api('/progress').catch(() => ({}))]);
    const t = d.training || {};
    if (t.latest_backtest_sharpe) {
      const sharpe = t.latest_backtest_sharpe;
      const mdd = t.latest_backtest_mdd_pct;
      const cagr = t.latest_backtest_cagr_pct;
      setEl('kpi-sharpe', fmt(sharpe, 3));
      document.getElementById('kpi-sharpe').className = 'kpi-value ' + (sharpe >= 1 ? 'pos' : 'neg');
      setEl('kpi-mdd', fmtPct(mdd));
      document.getElementById('kpi-mdd').className = 'kpi-value ' + (Math.abs(mdd) < 10 ? 'pos' : 'neg');
      setEl('kpi-cagr', fmtPct(cagr));
      setEl('kpi-days', t.rounds ? t.rounds + ' rounds' : '—');
    }
    // Constraints
    if (t.latest_constraints_met != null) {
      const met = t.latest_constraints_met;
      document.getElementById('constraints-badge').className = 'badge ' + (met ? 'ok' : 'err');
      setEl('constraints-badge', met ? 'All Met' : 'Not Met');
      setEl('constraints-details', `
        <div style="display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--t2)">
          <div style="display:flex;justify-content:space-between"><span>Sharpe ≥ 1.0</span><span class="badge ${t.latest_backtest_sharpe >= 1 ? 'ok' : 'err'}">${t.latest_backtest_sharpe >= 1 ? 'Met' : 'Not Met'}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Max DD &lt; 10%</span><span class="badge ${Math.abs(t.latest_backtest_mdd_pct) < 10 ? 'ok' : 'err'}">${Math.abs(t.latest_backtest_mdd_pct) < 10 ? 'Met' : 'Not Met'}</span></div>
          <div style="display:flex;justify-content:space-between"><span>CAGR</span><span style="font-family:var(--fm)">${fmtPct(t.latest_backtest_cagr_pct)}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Training rounds</span><span style="font-family:var(--fm)">${t.rounds || '—'}</span></div>
        </div>
      `);
    }
  } catch (e) {
    console.warn('metrics error', e);
  }
}

export async function loadPerfSummary() {
  try {
    const d = await api('/api/v1/performance-summary');
    const stale = d._run_instrument_id && d._active_instrument_id &&
                  d._run_instrument_id !== d._active_instrument_id;
    if (stale) {
      // Output files belong to a different instrument — show blanks
      ['kpi-return','kpi-cagr','kpi-sharpe','kpi-mdd','kpi-winrate'].forEach(id => {
        setEl(id, '—');
        const el = document.getElementById(id);
        if (el) el.className = 'kpi-value';
      });
      setEl('kpi-bnh', 'No backtest yet');
      setEl('kpi-cagr-bnh', '');
      setEl('kpi-days', 'Run pipeline');
      return;
    }
    // No completed backtest data yet — leave KPIs set by loadMetrics() untouched
    if (d.portfolio_total_return_pct == null) return;

    setEl('kpi-return', fmtPct(d.portfolio_total_return_pct));
    document.getElementById('kpi-return').className = 'kpi-value ' + (parseFloat(d.portfolio_total_return_pct) > 0 ? 'pos' : 'neg');
    setEl('kpi-bnh', `vs B&H ${fmtPct(d.benchmark_total_return_pct)}`);
    setEl('kpi-cagr', fmtPct(d.portfolio_cagr_pct));
    setEl('kpi-cagr-bnh', `B&H ${fmtPct(d.benchmark_cagr_pct)}`);
    setEl('kpi-sharpe', fmt(d.sharpe_ratio, 3));
    document.getElementById('kpi-sharpe').className = 'kpi-value ' + (parseFloat(d.sharpe_ratio) >= 1 ? 'pos' : 'neg');
    setEl('kpi-mdd', fmtPct(d.max_drawdown_pct));
    document.getElementById('kpi-mdd').className = 'kpi-value ' + (Math.abs(parseFloat(d.max_drawdown_pct)) < 10 ? 'pos' : 'neg');
    setEl('kpi-winrate', fmtPct(d.win_rate_pct));
    setEl('kpi-days', `${d.total_days} days`);

    // Re-render constraints using the same performance data that drives the KPIs.
    // loadMetrics() may use a different (stale) source — performance-summary wins.
    const sharpe = parseFloat(d.sharpe_ratio);
    const mdd    = parseFloat(d.max_drawdown_pct);
    const cagr   = parseFloat(d.portfolio_cagr_pct);
    const sharpeOk = !isNaN(sharpe) && sharpe >= 1;
    const mddOk    = !isNaN(mdd)    && Math.abs(mdd) < 10;
    const allMet   = sharpeOk && mddOk;
    if (document.getElementById('constraints-badge')) {
      document.getElementById('constraints-badge').className = 'badge ' + (allMet ? 'ok' : 'err');
      setEl('constraints-badge', allMet ? 'All Met' : 'Not Met');
      setEl('constraints-details', `
        <div style="display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--t2)">
          <div style="display:flex;justify-content:space-between"><span>Sharpe ≥ 1.0</span><span class="badge ${sharpeOk ? 'ok' : 'err'}">${sharpeOk ? 'Met' : 'Not Met'}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Max DD &lt; 10%</span><span class="badge ${mddOk ? 'ok' : 'err'}">${mddOk ? 'Met' : 'Not Met'}</span></div>
          <div style="display:flex;justify-content:space-between"><span>CAGR</span><span style="font-family:var(--fm)">${fmtPct(isNaN(cagr) ? null : cagr)}</span></div>
          <div style="display:flex;justify-content:space-between"><span>Total days</span><span style="font-family:var(--fm)">${d.total_days || '—'}</span></div>
        </div>
      `);
    }
  } catch (e) { /* performance data not yet available */ }
}

export async function loadDrift() {
  try {
    const d = await api('/api/v1/drift');
    const h = d.health || 'unknown';
    const cls = h === 'ok' ? 'ok' : h === 'warn' ? 'warn' : 'err';
    const alerts = [];
    const r = d.report || {};
    if (r.sharpe_drift) alerts.push({ cls: r.sharpe_drift.status === 'ok' ? 'ok' : 'warn', msg: 'Sharpe drift: ' + r.sharpe_drift.message, tag: r.sharpe_drift.status });
    if (r.return_degradation) alerts.push({ cls: r.return_degradation.status === 'ok' ? 'ok' : 'warn', msg: 'Return trend: ' + r.return_degradation.message, tag: r.return_degradation.status });
    if (r.data_freshness) alerts.push({ cls: r.data_freshness.status === 'ok' ? 'ok' : 'warn', msg: 'Data: ' + r.data_freshness.message, tag: r.data_freshness.status });
    if (r.pipeline_health) alerts.push({ cls: r.pipeline_health.status === 'ok' ? 'ok' : 'warn', msg: 'Pipeline: ' + r.pipeline_health.message, tag: r.pipeline_health.status });

    setEl('home-alerts', alerts.length ? `
      <div class="alert-strip">
        ${alerts.map(a => `
          <div class="alert-row ${a.cls}">
            <span class="alert-icon">${a.cls === 'ok' ? '✓' : '⚠'}</span>
            <span class="alert-msg">${a.msg}</span>
            <span class="alert-tag">${a.tag}</span>
          </div>
        `).join('')}
      </div>` : '');
  } catch (e) { }
}

export async function loadProgress() {
  try {
    const d = await api('/progress');
    const steps = d.steps || [];
    steps.forEach((s, i) => {
      const el = document.getElementById('seg-' + (i + 1));
      if (el) {
        el.classList.remove('done', 'active');
        if (s.status === 'completed') el.classList.add('done');
        else if (s.status === 'in_progress') el.classList.add('active');
      }
    });
  } catch (e) { }
}
