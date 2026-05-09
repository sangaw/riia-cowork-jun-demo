/* AgentOps Dashboard — data loader + panel renderers */

const ROLES = ['pm', 'architect', 'engineer', 'qa', 'techwriter'];

/* ── State ─────────────────────────────────────────── */
let metrics = null;
let runs    = [];   // full run JSON objects, sorted by run_id asc

/* ── Boot ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  await loadData();
  renderAll();
});

/* ── Data loading ─────────────────────────────────────── */
async function loadData() {
  try {
    const res = await fetch('metrics.json');
    metrics = await res.json();
  } catch (e) {
    console.error('metrics.json load failed', e);
    metrics = { per_role: {}, per_app: {}, grounding_trend: [], failure_modes: {}, skill_version_history: [] };
  }

  // derive run IDs from grounding_trend (avoids needing a directory listing)
  const runIds = (metrics.grounding_trend || []).map(r => r.run_id);
  // also try run-sample if no real runs yet
  if (runIds.length === 0) runIds.push('sample');

  for (const id of runIds) {
    const path = id === 'sample' ? 'run-sample.json' : `runs/run-${id}.json`;
    try {
      const r = await fetch(path);
      if (r.ok) runs.push(await r.json());
    } catch (_) { /* skip missing */ }
  }
  runs.sort((a, b) => a.run_id.localeCompare(b.run_id));
}

/* ── Render all panels ────────────────────────────────── */
function renderAll() {
  renderRunHistory();
  renderScorecards();
  renderGroundingChart();
  renderFailureHeatmap();
  renderTokenChart();
  renderSkillVersions();
}

/* ── Panel 1: Run History ─────────────────────────────── */
function renderRunHistory() {
  const el = document.getElementById('runs-table-container');
  if (!runs.length) { el.innerHTML = '<p class="ao-loading">No run data found.</p>'; return; }

  const rows = runs.map(r => {
    const badge = statusBadge(r.overall_status);
    const agents = r.agents || [];
    const warns  = agents.filter(a => a.status === 'pass_with_warnings').length;
    const fails  = agents.filter(a => a.status === 'fail').length;
    const flagCol = fails  ? `<span style="color:var(--fail)">${fails} failed</span>` :
                    warns  ? `<span style="color:var(--warn)">${warns} warned</span>` :
                    `<span style="color:var(--pass)">Clean</span>`;
    return `<tr>
      <td>${fmtRunId(r.run_id)}</td>
      <td><span class="badge badge-pass" style="text-transform:uppercase;font-size:10px">${r.app}</span></td>
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(r.request)}">${esc(r.request)}</td>
      <td>${badge}</td>
      <td>${flagCol}</td>
      <td>${r.duration_minutes ?? '—'} min</td>
      <td style="font-size:12px;color:var(--text-muted)">${esc(r.branch ?? '—')}</td>
    </tr>`;
  }).join('');

  el.innerHTML = `<table class="ao-table">
    <thead><tr>
      <th>Run ID</th><th>App</th><th>Request</th><th>Status</th><th>Agents</th><th>Duration</th><th>Branch</th>
    </tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

/* ── Panel 2: Agent Scorecards ────────────────────────── */
function renderScorecards() {
  const el = document.getElementById('scorecards-container');
  const pr = metrics?.per_role ?? {};
  if (!Object.keys(pr).length) { el.innerHTML = '<p class="ao-loading">No metrics data.</p>'; return; }

  const cards = ROLES.map(role => {
    const d = pr[role];
    if (!d) return '';
    const adh  = pct(d.avg_adherence_score);
    const fpr  = pct(d.first_pass_rate);
    const tok  = d.avg_token_cost?.toLocaleString() ?? '—';
    const barW = Math.round((d.avg_adherence_score ?? 0) * 100);
    return `<div class="ao-scorecard">
      <div class="ao-scorecard-role">${role}</div>
      <div class="ao-scorecard-row">
        <span class="ao-scorecard-label">Adherence</span>
        <span class="ao-scorecard-value">
          <span class="ao-bar-wrap"><span class="ao-bar" style="width:${barW}%"></span></span>
          &nbsp;${adh}
        </span>
      </div>
      <div class="ao-scorecard-row">
        <span class="ao-scorecard-label">First-pass rate</span>
        <span class="ao-scorecard-value" style="color:${d.first_pass_rate < 1 ? 'var(--warn)' : 'var(--pass)'}">${fpr}</span>
      </div>
      <div class="ao-scorecard-row">
        <span class="ao-scorecard-label">Avg tokens</span>
        <span class="ao-scorecard-value">${tok}</span>
      </div>
      <div class="ao-scorecard-row">
        <span class="ao-scorecard-label">Runs</span>
        <span class="ao-scorecard-value">${d.run_count ?? '—'}</span>
      </div>
    </div>`;
  }).join('');

  el.innerHTML = cards || '<p class="ao-loading">No role data.</p>';
}

/* ── Panel 3: Grounding Score Trend ───────────────────── */
function renderGroundingChart() {
  const trend = metrics?.grounding_trend ?? [];
  const labels = trend.map(r => fmtRunId(r.run_id));
  const data   = trend.map(r => +(r.grounding_score * 100).toFixed(1));

  new Chart(document.getElementById('chart-grounding'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '% Grounding Checks Passed',
        data,
        borderColor: '#6c8ef5',
        backgroundColor: 'rgba(108,142,245,0.12)',
        pointBackgroundColor: '#6c8ef5',
        fill: true,
        tension: 0.35,
      }]
    },
    options: chartOpts({ yMax: 100, yLabel: '%', suffix: '%' })
  });
}

/* ── Panel 4: Failure Heatmap — see increment 3 ──────── */
function renderFailureHeatmap() {
  const el = document.getElementById('failures-container');
  const fm = metrics?.failure_modes ?? {};
  const fcodes = Object.keys(fm);

  if (!fcodes.length) {
    el.innerHTML = '<p class="ao-loading">No failure modes recorded.</p>';
    return;
  }

  const headerCells = ROLES.map(r => `<th>${r}</th>`).join('');
  const bodyRows = fcodes.map(code => {
    const entry = fm[code];
    const cells = ROLES.map(role => {
      const count = entry.by_role?.[role] ?? 0;
      const cls   = count === 0 ? 'heat-0' : count === 1 ? 'heat-1' : count <= 2 ? 'heat-2' : 'heat-3';
      return `<td class="${cls}">${count || '—'}</td>`;
    }).join('');
    const anchor = code.toLowerCase().replace(/\s+/g, '-');
    const link = `<a href="failure-catalog.md#${anchor}" target="_blank" style="color:var(--accent);text-decoration:none">${esc(code)}</a>`;
    return `<tr><th style="text-align:left;padding-right:20px">${link}</th>${cells}</tr>`;
  }).join('');

  el.innerHTML = `<table class="ao-table ao-heatmap">
    <thead><tr><th>Failure Code</th>${headerCells}</tr></thead>
    <tbody>${bodyRows}</tbody>
  </table>`;
}

/* ── Panel 5: Token Cost Trend ────────────────────────── */
function renderTokenChart() {
  const labels   = runs.map(r => fmtRunId(r.run_id));
  const datasets = ROLES.map((role, i) => ({
    label: role,
    data: runs.map(r => (r.agents ?? []).find(a => a.role === role)?.token_estimate ?? 0),
    borderColor: roleColour(i),
    backgroundColor: roleColour(i, 0.08),
    fill: false,
    tension: 0.3,
    pointRadius: 4,
  }));

  new Chart(document.getElementById('chart-tokens'), {
    type: 'line',
    data: { labels, datasets },
    options: chartOpts({ yLabel: 'Tokens' })
  });
}

/* ── Panel 6: Skill Version History ───────────────────── */
function renderSkillVersions() {
  const el   = document.getElementById('skills-container');
  const hist = metrics?.skill_version_history ?? [];
  if (!hist.length) { el.innerHTML = '<p class="ao-loading">No skill history.</p>'; return; }

  const rows = hist.map(s => {
    const commits = (s.recent_commits ?? []).slice(0, 2).map(c => `<code style="font-size:11px">${esc(c)}</code>`).join('<br>');
    return `<tr>
      <td style="font-size:12px;color:var(--accent)">${esc(s.skill_file)}</td>
      <td>${esc(s.last_updated ?? '—')}</td>
      <td>${commits || '<span style="color:var(--text-muted)">—</span>'}</td>
    </tr>`;
  }).join('');

  el.innerHTML = `<table class="ao-table">
    <thead><tr><th>Skill File</th><th>Last Updated</th><th>Recent Commits</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

/* ── Helpers ──────────────────────────────────────────── */
function statusBadge(s) {
  if (s === 'pass')               return '<span class="badge badge-pass">Pass</span>';
  if (s === 'pass_with_warnings') return '<span class="badge badge-warn">Warnings</span>';
  return '<span class="badge badge-fail">Fail</span>';
}

function fmtRunId(id) {
  if (!id || id === 'sample') return id;
  // "20260430-1415" → "2026-04-30 14:15"
  const m = id.match(/^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})$/);
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}` : id;
}

function pct(val) { return val != null ? (val * 100).toFixed(0) + '%' : '—'; }
function esc(s)   { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

const PALETTE = ['#6c8ef5','#34d399','#fbbf24','#f87171','#a78bfa'];
function roleColour(i, alpha = 1) {
  const hex = PALETTE[i % PALETTE.length];
  if (alpha === 1) return hex;
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function chartOpts({ yMax, yLabel = '', suffix = '' }) {
  return {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { labels: { color: '#8892a4', font: { size: 12 } } },
      tooltip: {
        callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y}${suffix}` }
      }
    },
    scales: {
      x: { ticks: { color: '#8892a4' }, grid: { color: '#2e3350' } },
      y: {
        ticks: { color: '#8892a4', callback: v => v + suffix },
        grid:  { color: '#2e3350' },
        ...(yMax != null ? { max: yMax } : {}),
        title: { display: !!yLabel, text: yLabel, color: '#8892a4' }
      }
    }
  };
}
