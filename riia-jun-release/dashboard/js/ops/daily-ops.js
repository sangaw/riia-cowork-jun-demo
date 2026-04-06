// ── Daily Ops ─────────────────────────────────────────────────────────────────
import { apiFetch } from './api.js';

export async function loadDailyOps() {
  const d = await apiFetch('/api/v1/portfolio/man-daily-status');
  if (!d) {
    document.getElementById('dops-kpi-strip').innerHTML =
      '<div class="kpi"><div class="kpi-ey">Status</div><div class="kpi-val danger">Unavailable</div></div>';
    return;
  }

  const months = d.active_months || [];
  const ss     = d.snapshot_status || {};

  // ── KPI strip ──
  const snappedToday  = months.filter(m => ss[m] && ss[m].snapshotted_today).length;
  const totalMonths   = months.length;
  const actionsToday  = d.actions_today || 0;
  const lastActionTs  = d.last_action_ts ? d.last_action_ts.replace('T',' ').replace('Z','') : '—';
  const statusClass   = snappedToday === totalMonths && totalMonths > 0 ? 'ok' : totalMonths > 0 ? 'warn' : 'ops';

  document.getElementById('dops-kpi-strip').innerHTML = `
    <div class="kpi">
      <div class="kpi-ey">Today's Snapshots</div>
      <div class="kpi-val ${statusClass}">${snappedToday} / ${totalMonths}</div>
      <div class="kpi-sub">${d.today || '—'}</div>
    </div>
    <div class="kpi">
      <div class="kpi-ey">Active Months</div>
      <div class="kpi-val">${months.join(' · ') || '—'}</div>
      <div class="kpi-sub">from live positions</div>
    </div>
    <div class="kpi">
      <div class="kpi-ey">Actions Today</div>
      <div class="kpi-val ${actionsToday > 0 ? 'ok' : ''}">${actionsToday}</div>
      <div class="kpi-sub">drag-drop events logged</div>
    </div>
    <div class="kpi">
      <div class="kpi-ey">Last Action</div>
      <div class="kpi-val" style="font-size:13px;">${lastActionTs}</div>
      <div class="kpi-sub">UTC</div>
    </div>`;

  // ── Per-month cards ──
  const cardsHtml = months.length ? months.map(m => {
    const s        = ss[m] || {};
    const snapped  = s.snapshotted_today;
    const hasSaved = s.groups_saved;
    const badge    = snapped
      ? '<span class="badge ok">✓ Snapped</span>'
      : '<span class="badge warn">⚠ Pending</span>';
    const groupsBadge = hasSaved
      ? '<span class="badge ok">Groups saved</span>'
      : '<span class="badge neutral">No groups</span>';
    return `
      <div class="card" style="margin-bottom:8px;">
        <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-bottom:1px solid var(--bdr);">
          <div style="font-size:13px;font-weight:600;">${m} 2026</div>
          <div style="display:flex;gap:5px;align-items:center;">${badge}${groupsBadge}</div>
        </div>
        <div style="padding:10px 12px;display:flex;gap:16px;flex-wrap:wrap;">
          <div class="sb"><div class="sb-l">Last snapshot</div><div class="sb-v">${s.last_date || '—'}</div></div>
          <div class="sb"><div class="sb-l">Lots today</div><div class="sb-v">${s.lot_count || 0}</div></div>
          <div style="margin-left:auto;">
            <button class="btn-sm" onclick="triggerSnapshot('${m}')" title="Run server-side snapshot now">
              ▶ Run Snapshot
            </button>
          </div>
        </div>
      </div>`;
  }).join('') : '<div style="font-size:12px;color:var(--t3);padding:8px 0;">No active months found — load positions in FnO dashboard first.</div>';

  document.getElementById('dops-month-cards').innerHTML = cardsHtml;

  // ── Notes ──
  const notes = d.recent_notes || [];
  document.getElementById('dops-notes').innerHTML = notes.length
    ? notes.slice().reverse().map(n => `
        <div style="padding:8px 10px;border-radius:5px;background:var(--bg2);margin-bottom:5px;">
          <div style="font-size:9px;font-family:var(--fm);color:var(--t3);margin-bottom:3px;">
            ${n.date} · ${n.month} · ${(n.ts||'').replace('T',' ').replace('Z','')} UTC
          </div>
          <div style="font-size:12px;color:var(--t1);">${n.notes || '<em style="color:var(--t4)">no note</em>'}</div>
        </div>`).join('')
    : '<div style="font-size:12px;color:var(--t3);padding:8px 0;">No session notes yet.</div>';

  // ── History table ──
  const rows = d.recent_snapshots || [];
  document.getElementById('dops-history-tbody').innerHTML = rows.length
    ? rows.slice().reverse().map(r => `
        <tr>
          <td>${r.date || '—'}</td>
          <td><span class="badge neutral">${r.month || '—'}</span></td>
          <td style="font-family:var(--fm);">${r.nifty_spot ? Number(r.nifty_spot).toLocaleString('en-IN',{minimumFractionDigits:2}) : '—'}</td>
          <td>${r.lot_count || '—'}</td>
        </tr>`).join('')
    : '<tr><td colspan="4" style="text-align:center;color:var(--t3);">No snapshot history yet.</td></tr>';
}

export async function triggerSnapshot(month) {
  const btn = event.target;
  btn.disabled = true; btn.textContent = 'Running…';
  try {
    const res = await fetch('/api/v1/portfolio/man-daily-snapshot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ month }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      btn.textContent = '✓ Done';
      setTimeout(() => loadDailyOps(), 600);
    } else {
      btn.textContent = data.reason || 'Skipped';
      btn.disabled = false;
    }
  } catch(e) {
    btn.textContent = 'Error';
    btn.disabled = false;
  }
}
