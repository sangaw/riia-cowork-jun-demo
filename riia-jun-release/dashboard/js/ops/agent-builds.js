// ── Agent Builds ──────────────────────────────────────────────────────────────
import { apiFetch } from './api.js';

const ROLES = ['pm', 'architect', 'engineer', 'qa', 'techwriter'];
const ROLE_LABEL = { pm: 'PM', architect: 'Architect', engineer: 'Engineer', qa: 'QA', techwriter: 'TechWriter' };
const PALETTE = ['#6B2FA0', '#0056B8', '#1A6B3C', '#92480A', '#BE185D'];

// Chart instances — destroy before recreating to avoid Canvas reuse errors
let _chartGrounding = null;
let _chartTokens    = null;

/* ── Helpers ──────────────────────────────────────────────────────────────── */

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function pct(v) { return v != null ? Math.round(v * 100) + '%' : '—'; }

function fmtRunId(id) {
  if (!id || id === 'sample') return id;
  const m = id.match(/^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})$/);
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}` : id;
}

function roleColour(i, alpha = 1) {
  const hex = PALETTE[i % PALETTE.length];
  if (alpha === 1) return hex;
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function statusBadge(s) {
  if (s === 'pass')               return '<span class="badge ok">Pass</span>';
  if (s === 'pass_with_warnings') return '<span class="badge warn">Warnings</span>';
  return '<span class="badge danger">Fail</span>';
}

function panel(id, title, html) {
  return `<div class="ab-panel" id="ab-panel-${id}">
    <div class="c-ey"><div class="ey-d" style="background:var(--accelerate)"></div>${title}</div>
    ${html}
  </div>`;
}

function chartOpts({ yMax, yLabel = '', suffix = '' }) {
  const cs = getComputedStyle(document.documentElement);
  const gridCol   = cs.getPropertyValue('--border').trim()  || '#E4E0D8';
  const tickCol   = cs.getPropertyValue('--t3').trim()      || '#8C877A';
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: tickCol, font: { size: 11 }, boxWidth: 10 } },
      tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y}${suffix}` } }
    },
    scales: {
      x: { ticks: { color: tickCol, font: { size: 10 } }, grid: { color: gridCol } },
      y: {
        ticks: { color: tickCol, font: { size: 10 }, callback: v => v + suffix },
        grid:  { color: gridCol },
        ...(yMax != null ? { max: yMax } : {}),
        title: { display: !!yLabel, text: yLabel, color: tickCol, font: { size: 10 } }
      }
    }
  };
}

/* ── Panel 1: Run History ─────────────────────────────────────────────────── */

function renderRunHistory(runs) {
  if (!runs.length) {
    return panel('runs', 'Pipeline Run History', '<div class="empty">No run data found</div>');
  }
  const rows = runs.map(r => {
    const agents = r.agents || [];
    const warns  = agents.filter(a => a.status === 'pass_with_warnings').length;
    const fails  = agents.filter(a => a.status === 'fail').length;
    const flagCol = fails ? `<span class="badge danger">${fails} failed</span>` :
                    warns ? `<span class="badge warn">${warns} warned</span>` :
                    `<span class="badge ok">Clean</span>`;
    return `<tr>
      <td style="font-family:var(--fm);white-space:nowrap">${fmtRunId(r.run_id)}</td>
      <td><span class="badge neutral" style="text-transform:uppercase">${esc(r.app)}</span></td>
      <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--t3)" title="${esc(r.request)}">${esc(r.request ?? '—')}</td>
      <td>${statusBadge(r.overall_status)}</td>
      <td>${flagCol}</td>
      <td style="font-family:var(--fm)">${r.duration_minutes ?? '—'} min</td>
      <td style="font-family:var(--fm);color:var(--t3);font-size:10px">${esc(r.branch ?? '—')}</td>
    </tr>`;
  }).join('');
  const tbl = `<div class="tbl-wrap"><table>
    <thead><tr>
      <th>Run ID</th><th>App</th><th>Request</th><th>Status</th><th>Agents</th><th>Duration</th><th>Branch</th>
    </tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
  return panel('runs', 'Pipeline Run History', tbl);
}

/* ── Panel 2: Agent Scorecards ───────────────────────────────────────────── */

function renderScorecards(m) {
  const pr = m.per_role || {};
  if (!Object.keys(pr).length) {
    return panel('scorecards', 'Agent Scorecards', '<div class="empty">No metrics data</div>');
  }
  const cards = ROLES.map(role => {
    const d = pr[role];
    if (!d) return '';
    const barW = Math.round((d.avg_adherence_score ?? 0) * 100);
    const fprOk = (d.first_pass_rate ?? 0) >= 1;
    return `<div class="ab-sc">
      <div class="ab-sc-role">${ROLE_LABEL[role]}</div>
      <div class="ab-sc-row">
        <span class="ab-sc-lbl">Adherence</span>
        <span class="ab-sc-val">
          <span class="ab-bar-wrap"><span class="ab-bar" style="width:${barW}%"></span></span>
          &nbsp;${pct(d.avg_adherence_score)}
        </span>
      </div>
      <div class="ab-sc-row">
        <span class="ab-sc-lbl">1st pass</span>
        <span class="ab-sc-val" style="color:var(${fprOk ? '--ok' : '--warn'})">${pct(d.first_pass_rate)}</span>
      </div>
      <div class="ab-sc-row">
        <span class="ab-sc-lbl">Avg tokens</span>
        <span class="ab-sc-val">${d.avg_token_cost?.toLocaleString() ?? '—'}</span>
      </div>
      <div class="ab-sc-row">
        <span class="ab-sc-lbl">Runs</span>
        <span class="ab-sc-val">${d.run_count ?? '—'}</span>
      </div>
    </div>`;
  }).join('');
  return panel('scorecards', 'Agent Scorecards', `<div class="ab-sc-grid">${cards}</div>`);
}

/* ── Panel 3: Grounding Score Trend ─────────────────────────────────────── */

function renderGroundingPanel(m) {
  return panel('grounding', 'Grounding Score Trend',
    `<div class="ab-chart-wrap"><canvas id="ab-chart-grounding"></canvas></div>`);
}

function mountGroundingChart(m) {
  const trend  = m.grounding_trend ?? [];
  const labels = trend.map(r => fmtRunId(r.run_id));
  const data   = trend.map(r => +(r.grounding_score * 100).toFixed(1));
  if (_chartGrounding) { _chartGrounding.destroy(); _chartGrounding = null; }
  const ctx = document.getElementById('ab-chart-grounding');
  if (!ctx) return;
  _chartGrounding = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '% Grounding Checks Passed',
        data,
        borderColor: '#6B2FA0',
        backgroundColor: 'rgba(107,47,160,0.10)',
        pointBackgroundColor: '#6B2FA0',
        fill: true,
        tension: 0.35,
      }]
    },
    options: chartOpts({ yMax: 100, yLabel: '%', suffix: '%' })
  });
}

/* ── Panel 4: Failure Heatmap ────────────────────────────────────────────── */

function renderFailureHeatmap(m) {
  const fm = m.failure_modes || {};
  const fcodes = Object.keys(fm);
  if (!fcodes.length) {
    return panel('failures', 'Failure Mode Heatmap', '<div class="empty">No failure modes recorded</div>');
  }
  const headerCells = ROLES.map(r => `<th>${ROLE_LABEL[r]}</th>`).join('');
  const bodyRows = fcodes.map(code => {
    const entry = fm[code];
    const cells = ROLES.map(role => {
      const count = entry.by_role?.[role] ?? 0;
      const cls   = count === 0 ? 'heat-0' : count === 1 ? 'heat-1' : count <= 2 ? 'heat-2' : 'heat-3';
      return `<td class="${cls}">${count || '—'}</td>`;
    }).join('');
    return `<tr><th style="text-align:left;padding-right:12px;white-space:nowrap;font-family:var(--fm);font-size:10px;color:var(--accelerate)">${esc(code)}</th>${cells}</tr>`;
  }).join('');
  const tbl = `<div class="tbl-wrap"><table class="ab-heatmap">
    <thead><tr><th style="text-align:left">Failure Code</th>${headerCells}</tr></thead>
    <tbody>${bodyRows}</tbody>
  </table></div>`;
  return panel('failures', 'Failure Mode Heatmap', tbl);
}

/* ── Panel 5: Token Cost Trend ───────────────────────────────────────────── */

function renderTokenPanel(runs) {
  return panel('tokens', 'Token Cost Trend',
    `<div class="ab-chart-wrap"><canvas id="ab-chart-tokens"></canvas></div>`);
}

function mountTokenChart(runs) {
  const labels   = runs.map(r => fmtRunId(r.run_id));
  const datasets = ROLES.map((role, i) => ({
    label: ROLE_LABEL[role],
    data: runs.map(r => (r.agents ?? []).find(a => a.role === role)?.token_estimate ?? 0),
    borderColor: roleColour(i),
    backgroundColor: roleColour(i, 0.08),
    fill: false,
    tension: 0.3,
    pointRadius: 4,
  }));
  if (_chartTokens) { _chartTokens.destroy(); _chartTokens = null; }
  const ctx = document.getElementById('ab-chart-tokens');
  if (!ctx) return;
  _chartTokens = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: chartOpts({ yLabel: 'Tokens' })
  });
}

/* ── Panel 6: Skill Version History ─────────────────────────────────────── */

function renderSkillVersions(m) {
  const hist = m.skill_version_history ?? [];
  if (!hist.length) {
    return panel('skills', 'Skill File Versions', '<div class="empty">No skill history</div>');
  }
  const rows = hist.map(s => {
    const commits = (s.recent_commits ?? []).slice(0, 2)
      .map(c => `<code style="font-size:10px;font-family:var(--fm);color:var(--t3)">${esc(c)}</code>`)
      .join('<br>');
    return `<tr>
      <td style="font-family:var(--fm);font-size:10px;color:var(--accelerate)">${esc(s.skill_file)}</td>
      <td style="font-family:var(--fm);font-size:11px">${esc(s.last_updated ?? '—')}</td>
      <td>${commits || '<span style="color:var(--t4)">—</span>'}</td>
    </tr>`;
  }).join('');
  const tbl = `<div class="tbl-wrap"><table>
    <thead><tr><th>Skill File</th><th>Last Updated</th><th>Recent Commits</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
  return panel('skills', 'Skill File Versions', tbl);
}

/* ── Main loader ─────────────────────────────────────────────────────────── */

export async function loadAgentBuilds() {
  const grid = document.getElementById('ab-grid');
  if (!grid) return;
  grid.innerHTML = '<div class="loading">Loading…</div>';

  try {
    const data = await apiFetch('/api/experience/ops/agent-builds');
    const runs = data.runs;
    const m = data.metrics;

    if (!data) {
      grid.innerHTML = '<div class="empty">Could not load agent-ops metrics</div>';
      return;
    }

    // Render HTML panels (charts need canvas in DOM first)
    grid.innerHTML = [
      renderRunHistory(runs),
      renderScorecards(m),
      renderGroundingPanel(m),
      renderFailureHeatmap(m),
      renderTokenPanel(runs),
      renderSkillVersions(m),
    ].join('');

    // Mount Chart.js after DOM is ready
    if (window.Chart) {
      mountGroundingChart(m);
      mountTokenChart(runs);
    }
  } catch (e) {
    grid.innerHTML = '<div class="empty">Could not load agent-ops metrics</div>';
  }
}
