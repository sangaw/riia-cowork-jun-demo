// ── API helper ────────────────────────────────────────────────────────────────

export async function apiFetch(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}
