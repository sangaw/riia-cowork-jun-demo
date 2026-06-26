// ── Agent Performance (Feature 32) ──────────────────────────
// Per-agent KPI cards + table for the 7 investment-workflow agents.
import { api } from './api.js';
import { setEl, badge, fmtPct } from './utils.js';

// outcome_match_rate is a 0–1 fraction (or null). fmtPct appends '%' without
// scaling, so multiply by 100 first; null → '—'.
function fmtRate(rate) {
  return rate == null ? '—' : fmtPct(rate * 100);
}

// trend_vs_prior_30d is a signed 0–1 ratio (or null) → signed percent string.
function fmtTrend(trend) {
  if (trend == null) return '—';
  const pct = (trend * 100).toFixed(1);
  const sign = trend > 0 ? '+' : '';
  return `${sign}${pct}%`;
}

export async function loadAgentPerformance() {
  try {
    const data = await api('/api/v1/experience/rita/agent-performance');
    const agents = (data && data.agents) || [];

    const cards = agents.map(a => `
      <div class="kpi-card">
        <div class="kpi-label">${a.agent_name}</div>
        <div class="kpi-value">${a.invocation_count_30d}</div>
        <div class="kpi-sub">invocations (30d) · ${badge(a.gap_status)}</div>
      </div>`).join('');
    setEl('agent-perf-cards', cards || '—');

    const rows = agents.map(a => `
      <tr>
        <td>${a.agent_name}</td>
        <td>${badge(a.gap_status)}</td>
        <td>${a.invocation_count_30d}</td>
        <td>${fmtRate(a.outcome_match_rate)}</td>
        <td>${fmtTrend(a.trend_vs_prior_30d)}</td>
      </tr>`).join('');
    setEl('agent-perf-table', rows || '—');

    setEl('agent-perf-updated', new Date().toLocaleString());
  } catch (e) {
    setEl('agent-perf-cards', '—');
    setEl('agent-perf-table', '—');
  }
}
