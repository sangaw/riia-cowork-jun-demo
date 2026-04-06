// ── Formatting utilities ──────────────────────────────────────────────────────

export function fmt(v, decimals=2) {
  if (v == null || v === '' || isNaN(Number(v))) return '—';
  return Number(v).toFixed(decimals);
}

export function badge(text, cls) {
  return `<span class="badge ${cls}">${text}</span>`;
}

export function stepName(num) {
  const names = {1:'Set Goal',2:'Market Analysis',3:'Strategy',4:'Train Model',
                 5:'Set Period',6:'Backtest',7:'Results',8:'Update Goal'};
  return names[num] || ('Step ' + num);
}
