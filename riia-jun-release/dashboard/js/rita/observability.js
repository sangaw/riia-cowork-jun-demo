// ── Observability ──────────────────────────────────────────
import { api } from './api.js';
import { badge, setEl } from './utils.js';

export async function loadObservability() {
  try {
    const [metrics, drift, stepLog] = await Promise.all([
      api('/metrics').catch(() => ({})),
      api('/api/v1/drift').catch(() => null),
      api('/api/v1/step-log').catch(() => []),
    ]);

    // Drift report
    if (drift) {
      const h = (drift.health && (drift.health.overall || drift.health)) || 'unknown';
      document.getElementById('drift-badge').className = 'badge ' + (h === 'ok' ? 'ok' : h === 'warn' ? 'warn' : 'err');
      setEl('drift-badge', h.toUpperCase());
      const r = drift.report || {};
      setEl('drift-details', `
        <div style="display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--t2)">
          ${Object.entries(r).filter(([k, v]) => v && typeof v === 'object' && v.status).map(([k, v]) => `
            <div style="display:flex;justify-content:space-between;gap:8px">
              <span>${k.replace(/_/g, ' ')}</span>
              <span class="badge ${v.status === 'ok' ? 'ok' : 'warn'}">${v.status}</span>
            </div>`).join('')}
        </div>`);
    }

    // API stats
    const a = metrics.api_requests || {};
    setEl('api-stats', `
      <div style="display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--t2)">
        <div style="display:flex;justify-content:space-between"><span>Total requests</span><span style="font-family:var(--fm)">${a.total_requests || '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Avg latency</span><span style="font-family:var(--fm)">${a.avg_duration_ms ? Math.round(a.avg_duration_ms) + ' ms' : '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Error rate</span><span style="font-family:var(--fm)">${a.error_rate != null ? (a.error_rate * 100).toFixed(1) + '%' : '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Requests today</span><span style="font-family:var(--fm)">${a.requests_today || '—'}</span></div>
      </div>`);

    // Pipeline stats
    const p = metrics.pipeline || {};
    setEl('pipeline-stats', `
      <div style="display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--t2)">
        <div style="display:flex;justify-content:space-between"><span>Total logged</span><span style="font-family:var(--fm)">${p.total_logged_steps || '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Completed</span><span style="font-family:var(--fm)">${p.completed_steps || '—'}</span></div>
        <div style="display:flex;justify-content:space-between"><span>Failed</span><span class="badge ${p.failed_steps ? 'err' : 'ok'}">${p.failed_steps || 0}</span></div>
      </div>`);

    // Step log table
    if (stepLog && stepLog.length) {
      const recent = stepLog.slice(-30).reverse();
      setEl('step-log-wrap', `
        <table>
          <thead><tr><th>Step</th><th>Name</th><th>Status</th><th>Started</th><th>Duration (s)</th><th>Summary</th></tr></thead>
          <tbody>${recent.map(r => `
            <tr>
              <td class="td-mono">${r.step_num || '—'}</td>
              <td>${r.step_name || '—'}</td>
              <td>${badge(r.status)}</td>
              <td class="td-mono" style="font-size:11px">${(r.started_at || '').slice(0, 19)}</td>
              <td class="td-mono">${r.duration_secs != null ? parseFloat(r.duration_secs).toFixed(2) : '—'}</td>
              <td style="font-size:11px;color:var(--t3)">${r.summary || '—'}</td>
            </tr>`).join('')}
          </tbody>
        </table>`);
    } else {
      setEl('step-log-wrap', '<div class="empty">No step log entries found.</div>');
    }
  } catch (e) {
    console.warn('observability error', e);
    setEl('step-log-wrap', `<div class="empty">Error loading observability data: ${e.message}</div>`);
  }
}
