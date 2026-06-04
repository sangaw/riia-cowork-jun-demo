// ── Stress scenarios ──────────────────────────────────────────────────────────
import { t } from '../shared/i18n.js';
import { state } from './state.js';
import { fmtPnl, pnlClass } from './utils.js';

export function computeFilteredStress() {
  const filtered = state.greeksData.filter(g =>
    (state.currentUnd === 'ALL' || g.und === state.currentUnd) &&
    (state.currentExpiry === 'ALL' || g.exp === state.currentExpiry)
  );
  const moves = [-0.04, -0.02, 0.0, 0.02, 0.04];
  const niftySpot = (state.marketData.NIFTY || {}).close || 0;
  return moves.map(move => {
    let totalPnl = 0;
    filtered.forEach(g => {
      const spot = (state.marketData[g.und] || {}).close || 0;
      totalPnl += g.delta * spot * move;
    });
    return {
      move_pct:    move * 100,
      move_label:  (move > 0 ? '+' : '') + (move * 100).toFixed(0) + '%',
      nifty_level: niftySpot ? Math.round(niftySpot * (1 + move)) : null,
      pnl:         Math.round(totalPnl),
    };
  });
}

export function renderStressScenarios() {
  document.getElementById('stress-row').innerHTML = computeFilteredStress().map(s => {
    const isFlat = s.move_pct === 0;
    const niftyLbl = s.nifty_level ? `~${s.nifty_level.toLocaleString('en-IN')}` : '—';
    return `<div class="scenario-card${isFlat ? ' flat' : ''}">
      <div class="scenario-move">${isFlat ? t('stress.flat') : s.move_label}</div>
      <div class="scenario-nifty">${niftyLbl}</div>
      <div class="scenario-pnl ${pnlClass(s.pnl)}">${fmtPnl(s.pnl)}</div>
    </div>`;
  }).join('');
  renderAnalyticsStress();
}

// ── Historical event stress (F30 Phase 3 — analytics state) ──────────────────
function renderAnalyticsStress() {
  const rows = state.stressData;
  if (!rows?.length) return;
  const el = document.getElementById('stress-events-row');
  if (!el) return;

  el.innerHTML = `
    <div style="font-size:11px;font-weight:700;color:var(--t2);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px">Historical Event Scenarios</div>
    <div class="tbl-wrap">
      <table class="table table-sm mb-0">
        <thead><tr>
          <th>Event</th>
          <th>Move %</th>
          <th>Portfolio P&amp;L (EUR)</th>
          <th>Hedged P&amp;L (EUR)</th>
        </tr></thead>
        <tbody>
          ${rows.map(r => {
            const moveCls = (r.move_pct || 0) >= 0 ? 'pos' : 'neg';
            const moveStr = (r.move_pct || 0) >= 0 ? '+' + r.move_pct : r.move_pct;
            const pPnlCls = (r.portfolio_pnl_eur || 0) >= 0 ? 'pos' : 'neg';
            const hPnlCls = (r.hedged_pnl_eur   || 0) >= 0 ? 'pos' : 'neg';
            const fmt = v => v != null ? (v >= 0 ? '+€' : '−€') + Math.abs(v).toLocaleString('en-EU', { maximumFractionDigits: 0 }) : '—';
            return `<tr>
              <td style="padding:5px 10px;font-size:12px">${r.label ?? '—'}</td>
              <td class="${moveCls}" style="padding:5px 10px;font-size:12px;font-family:'IBM Plex Mono',monospace">${moveStr}%</td>
              <td class="${pPnlCls}" style="padding:5px 10px;font-size:12px;font-family:'IBM Plex Mono',monospace">${fmt(r.portfolio_pnl_eur)}</td>
              <td class="${hPnlCls}" style="padding:5px 10px;font-size:12px;font-family:'IBM Plex Mono',monospace">${fmt(r.hedged_pnl_eur)}</td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>`;
}
