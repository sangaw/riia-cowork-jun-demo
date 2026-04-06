// ── Positions section ─────────────────────────────────────────────────────────
import { state } from './state.js';
import { fmt, fmtPnl, pnlClass } from './utils.js';

export function renderPositionsKpis() {
  const byExp = (und, exp) => state.positions.filter(p => (und === 'ALL' || p.und === und) && p.exp === exp && (state.currentExpiry === 'ALL' || p.exp === state.currentExpiry)).reduce((s, p) => s + p.pnl, 0);
  const cntExp = (und, exp) => state.positions.filter(p => (und === 'ALL' || p.und === und) && p.exp === exp && (state.currentExpiry === 'ALL' || p.exp === state.currentExpiry)).length;
  if (state.currentUnd === 'ALL') {
    document.getElementById('pos-kpis').className = 'kpi-row c4';
    document.getElementById('pos-kpis').innerHTML = `
      <div class="kpi"><div class="kpi-label">NIFTY APR</div><div class="kpi-value ${pnlClass(byExp('NIFTY','APR'))}">${fmtPnl(byExp('NIFTY','APR'))}</div><div class="kpi-sub">${cntExp('NIFTY','APR')} positions</div></div>
      <div class="kpi"><div class="kpi-label">NIFTY MAY</div><div class="kpi-value ${pnlClass(byExp('NIFTY','MAY'))}">${fmtPnl(byExp('NIFTY','MAY'))}</div><div class="kpi-sub">${cntExp('NIFTY','MAY')} positions</div></div>
      <div class="kpi"><div class="kpi-label">BANKNIFTY APR</div><div class="kpi-value ${pnlClass(byExp('BANKNIFTY','APR'))}">${fmtPnl(byExp('BANKNIFTY','APR'))}</div><div class="kpi-sub">${cntExp('BANKNIFTY','APR')} positions</div></div>
      <div class="kpi"><div class="kpi-label">BANKNIFTY MAY</div><div class="kpi-value ${pnlClass(byExp('BANKNIFTY','MAY'))}">${fmtPnl(byExp('BANKNIFTY','MAY'))}</div><div class="kpi-sub">${cntExp('BANKNIFTY','MAY')} positions</div></div>`;
  } else if (state.currentUnd === 'NIFTY') {
    const apr = byExp('NIFTY', 'APR'), may = byExp('NIFTY', 'MAY'), tot = apr + may;
    document.getElementById('pos-kpis').className = 'kpi-row c4';
    document.getElementById('pos-kpis').innerHTML = `
      <div class="kpi"><div class="kpi-label">NIFTY APR</div><div class="kpi-value ${pnlClass(apr)}">${fmtPnl(apr)}</div><div class="kpi-sub">${cntExp('NIFTY','APR')} positions</div></div>
      <div class="kpi"><div class="kpi-label">NIFTY MAY</div><div class="kpi-value ${pnlClass(may)}">${fmtPnl(may)}</div><div class="kpi-sub">${cntExp('NIFTY','MAY')} positions</div></div>
      <div class="kpi"><div class="kpi-label">Net Unrealized</div><div class="kpi-value ${pnlClass(tot)}">${fmtPnl(tot)}</div><div class="kpi-sub">NIFTY total</div></div>
      <div class="kpi"><div class="kpi-label">Realized</div><div class="kpi-value pos">${fmtPnl(state.realizedPnl)}</div><div class="kpi-sub pos">${state.closedPositions.length} closed trades</div></div>`;
  } else {
    const apr = byExp('BANKNIFTY', 'APR'), may = byExp('BANKNIFTY', 'MAY'), tot = apr + may;
    document.getElementById('pos-kpis').className = 'kpi-row c4';
    document.getElementById('pos-kpis').innerHTML = `
      <div class="kpi"><div class="kpi-label">BANKNIFTY APR</div><div class="kpi-value ${pnlClass(apr)}">${fmtPnl(apr)}</div><div class="kpi-sub">${cntExp('BANKNIFTY','APR')} positions</div></div>
      <div class="kpi"><div class="kpi-label">BANKNIFTY MAY</div><div class="kpi-value ${pnlClass(may)}">${fmtPnl(may)}</div><div class="kpi-sub">${cntExp('BANKNIFTY','MAY')} positions</div></div>
      <div class="kpi"><div class="kpi-label">Net Unrealized</div><div class="kpi-value ${pnlClass(tot)}">${fmtPnl(tot)}</div><div class="kpi-sub">BANKNIFTY total</div></div>
      <div class="kpi"><div class="kpi-label">Realized</div><div class="kpi-value">₹0</div><div class="kpi-sub">No closed BANKNIFTY trades</div></div>`;
  }
}

export function renderPositionsTable() {
  // Build HQS lookup: instrument → scored position
  const hqsMap = {};
  ((state.hedgeQuality.positions) || []).forEach(h => { hqsMap[h.instrument] = h; });

  const filtered = state.positions.filter(p => {
    if (state.currentUnd !== 'ALL' && p.und !== state.currentUnd) return false;
    if (state.currentExpiry !== 'ALL' && p.exp !== state.currentExpiry) return false;
    if (state.currentPosFilter === 'ALL') return true;
    return p.type === state.currentPosFilter;
  });
  document.getElementById('pos-tbody').innerHTML = filtered.map(p => {
    const chgClass = p.chg >= 0 ? 'pos' : 'neg';
    // HQS badge — only for long options
    let hqsCell = '<td></td>';
    if (p.type !== 'FUT' && p.side === 'Long') {
      const h = hqsMap[p.instrument];
      if (h) {
        const icon = { green: '🟢', yellow: '🟡', red: '🔴' }[h.hqs_tier];
        hqsCell = `<td><span class="hqs-badge ${h.hqs_tier}">${icon} ${h.hqs}</span></td>`;
      }
    }
    return `<tr>
      <td>${p.full}</td>
      <td><span class="exp-badge ${p.exp.toLowerCase()}">${p.exp}</span></td>
      <td><span class="inst-badge ${p.type.toLowerCase()}">${p.type}</span></td>
      <td class="val">${p.strike}</td>
      <td><span class="side-badge ${p.side.toLowerCase()}">${p.side}</span></td>
      <td class="val">${fmt(p.qty)}</td>
      <td class="val">${p.type === 'FUT' ? '₹' + fmt(p.avg) : p.avg.toFixed(2)}</td>
      <td class="val">${p.type === 'FUT' ? '₹' + fmt(p.ltp) : p.ltp.toFixed(2)}</td>
      <td class="${chgClass} val">${p.chg >= 0 ? '+' : ''}${p.chg.toFixed(2)}%</td>
      <td class="${pnlClass(p.pnl)}">${fmtPnl(p.pnl)}</td>
      ${hqsCell}
    </tr>`;
  }).join('');
  const total = filtered.reduce((s, p) => s + p.pnl, 0);
  document.getElementById('pos-count-lbl').textContent = `${filtered.length} position${filtered.length !== 1 ? 's' : ''}`;
  const el = document.getElementById('pos-total');
  el.textContent = fmtPnl(total);
  el.className = `val ${pnlClass(total)}`;
}

export function filterPos(f, btn) {
  state.currentPosFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderPositionsTable();
}
