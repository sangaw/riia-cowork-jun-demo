// ── Functional KPI Sparklines ─────────────────────────────────────────────────

const KPI_DEFS = [
  { key: 'training_success_rate_pct', label: 'Training Success Rate', unit: '%' },
  { key: 'chat_low_confidence_pct',   label: 'Chat Low Confidence',   unit: '%' },
  { key: 'experience_error_pct',      label: 'Experience Error Rate', unit: '%' },
  { key: 'error_rate_pct',            label: 'API Error Rate',        unit: '%' },
  { key: 'p95_latency_ms',            label: 'P95 Latency',           unit: 'ms' },
];

function sparklineSVG(values, width = 200, height = 40) {
  if (!values || values.length === 0) return '';
  const max = Math.max(...values, 1);
  const pts = values.map((v, i) => {
    const x = values.length > 1 ? (i / (values.length - 1)) * width : width / 2;
    const y = height - (v / max) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return `<svg width="${width}" height="${height}" style="display:block;">
    <polyline points="${pts}" fill="none" stroke="#6366f1" stroke-width="1.5"/>
  </svg>`;
}

export async function loadFunctionalKPIs() {
  const container = document.getElementById('functional-kpis-container');

  try {
    const res = await fetch('/ops/metrics/functional-kpis.json');
    const data = res.ok ? await res.json() : null;

    if (!data || !data.series) {
      if (container) container.innerHTML = '<div class="empty">KPI data unavailable</div>';
      return;
    }

    const cards = KPI_DEFS.map(def => {
      const values = Array.isArray(data.series[def.key]) ? data.series[def.key] : [];
      const lastVal = values.length > 0 ? values[values.length - 1] : null;
      const allZero = values.every(v => v === 0);

      const svg = (!allZero && values.length > 0) ? sparklineSVG(values) : '';
      const valDisplay = lastVal != null ? `${Number(lastVal).toFixed(1)}${def.unit}` : '—';
      const noData = allZero || values.length === 0;

      return `<div style="background:var(--c2,#1e293b);border-radius:6px;padding:12px 14px;min-width:180px;flex:1;">
        <div style="font-size:11px;color:var(--t3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">${def.label}</div>
        <div style="font-size:20px;font-weight:600;font-family:var(--fm);color:var(--t1,#f1f5f9);margin-bottom:8px">${valDisplay}</div>
        ${noData ? '<div class="empty" style="font-size:11px">No data</div>' : svg}
      </div>`;
    });

    if (container) {
      container.style.display = 'flex';
      container.style.flexWrap = 'wrap';
      container.style.gap = '12px';
      container.innerHTML = cards.join('');
    }
  } catch (e) {
    console.error('[RITA] loadFunctionalKPIs failed', e);
    if (container) container.innerHTML = '<div class="empty">KPI data unavailable</div>';
  }
}
