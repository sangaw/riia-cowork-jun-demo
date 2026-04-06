// ── Utility ────────────────────────────────────────────────
export const fmt = (v, d = 2) => v == null || v === '' ? '—' : parseFloat(v).toFixed(d);
export const fmtPct = v => v == null ? '—' : parseFloat(v).toFixed(2) + '%';
export const fmtMs = v => v == null ? '—' : Math.round(v) + ' ms';

export function badge(status) {
  const map = { ok: 'ok', warn: 'warn', alert: 'err', error: 'err', run: 'run', running: 'run' };
  const cls = map[(status || '').toLowerCase()] || 'neu';
  return `<span class="badge ${cls}">${status || '—'}</span>`;
}

export function setEl(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

export function appendResult(containerId, html) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = html;
}
