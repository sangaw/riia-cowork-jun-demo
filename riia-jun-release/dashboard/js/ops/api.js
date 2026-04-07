// ── API helper ────────────────────────────────────────────────────────────────
// window.RITA_API_BASE can be set by the host page to point at a non-origin
// API server (e.g. staging). Defaults to '' = same origin.
export const apiBase = () => (window.RITA_API_BASE || '').replace(/\/$/, '');

export async function apiFetch(url) {
  try {
    const r = await fetch(apiBase() + url);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}
