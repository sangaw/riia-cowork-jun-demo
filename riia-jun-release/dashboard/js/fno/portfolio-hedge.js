// ── Portfolio Hedge Wizard — Feature 28 Phase 3 ────────────────────────────────
// 2-tab flow: Discover (holdings + σ scenarios) → Hedge (coverage dial + payoff simulator)
// Hedge tab restores the original hedge table + coverage dial + payoff simulator.
// API: GET /api/v1/experience/fno/portfolio-hedge?coverage=N&duration=D  (JWT)

import { apiFetch } from './api.js';
import { isLocalDev, ensureDevToken } from '../shared/dev-auth.js';

// ── Constants ─────────────────────────────────────────────────────────────────
const _TAB_ORDER = ['discover', 'hedge'];

const _DURATION_MONTHS = { '1m': 1, '3m': 3, '1y': 12 };
const _DURATION_LABEL  = { '1m': 'Immediate (1M)', '3m': 'Near Term (3M)', '1y': 'Short Term (1Y)' };

// F&O eligibility — mirrors backend, used for client-side fallback
const _FNO_ELIGIBLE = new Set([
  'RELIANCE','TATAMOTOR','TCS','INFY','HDFCBANK','WIPRO','BAJFINANCE',
  'TATASTEEL','SBIN','ICICIBANK','KOTAKBANK','AXISBANK','SUNPHARMA','HCLTECH','LT',
  'ONGC','NTPC','POWERGRID','BPCL',
]);

// ── State ─────────────────────────────────────────────────────────────────────
const _state = {
  tab:          'discover',
  duration:     '1y',
  coverage:     50,
  holdings:     [],    // [{instrument_id, allocation_pct}] from user-portfolio
  instruments:  {},    // id → {return_1y_pct, risk_score, daily_return_pct, region}
  apiHedge:     null,  // PortfolioHedgeResponse | null
  selections:   {},    // id → 'put_buy' | 'call_sell'
  hedgeChecked: new Set(),
  totalValueEur: null,  // float | null — from saved portfolio or user input
  reached:      new Set(['discover']),
  _portfolioName: '',
};

let _scenarioTab = 'pp';  // 'pp' | 'ps' | 'collar'
let _payoffChart = null;

// ── DOM helpers ───────────────────────────────────────────────────────────────
function _show(id) { const el = document.getElementById(id); if (el) el.style.display = ''; }
function _hide(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; }
function _setText(id, txt) { const el = document.getElementById(id); if (el) el.textContent = txt; }

function _riskDots(r) {
  return Array.from({ length: 5 }, (_, i) =>
    `<span style="font-size:11px;color:${i < r ? '#BE185D' : 'rgba(0,0,0,.15)'}">●</span>`
  ).join('');
}

function _fmtPct(v) {
  const c = v > 0.5 ? '#16a34a' : v < -0.5 ? '#dc2626' : '#64748b';
  return `<span style="font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:600;color:${c}">${v >= 0 ? '+' : ''}${v.toFixed(1)}%</span>`;
}

// ── Tab navigation ────────────────────────────────────────────────────────────
function _goToTab(tab) {
  if (!_state.reached.has(tab)) return;
  _state.tab = tab;
  _renderTabBar();
  _TAB_ORDER.forEach(t => {
    const panel = document.getElementById(`ph-panel-${t}`);
    if (panel) panel.style.display = t === tab ? '' : 'none';
  });
  if (tab === 'discover')   _renderDiscover();
  if (tab === 'hedge')      _renderHedge();
}

function _renderTabBar() {
  _TAB_ORDER.forEach(t => {
    const btn = document.getElementById(`ph-tab-btn-${t}`);
    if (!btn) return;
    const isActive  = t === _state.tab;
    const isReached = _state.reached.has(t);
    btn.style.fontWeight        = isActive ? '700' : '500';
    btn.style.color             = isActive ? '#BE185D' : (isReached ? 'var(--text)' : 'var(--t3)');
    btn.style.borderBottomColor = isActive ? '#BE185D' : 'transparent';
    btn.style.cursor            = isReached ? 'pointer' : 'default';
    btn.disabled                = !isReached;
  });
}

// ── Discover tab (merged: holdings + hedge selection) ─────────────────────────
function _fmtEur(v) {
  if (v == null) return '—';
  return '€' + v.toLocaleString('en-EU', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function _renderDiscover() {
  _setText('ph-discover-portfolio-name', _state._portfolioName || '—');
  const eurInput = document.getElementById('ph-total-eur');
  if (eurInput && _state.totalValueEur != null) eurInput.value = _state.totalValueEur;

  const tbody = document.getElementById('ph-discover-holdings');
  if (!tbody) return;

  if (!_state.holdings.length) {
    tbody.innerHTML = '<tr><td colspan="9" style="padding:16px;text-align:center;color:#94a3b8;font-size:12px">No portfolio holdings found.</td></tr>';
    return;
  }

  const tMonths  = _DURATION_MONTHS[_state.duration];
  const hedgeMap = {};
  if (_state.apiHedge?.holdings) {
    for (const hh of _state.apiHedge.holdings) hedgeMap[hh.instrument_id] = hh;
  }

  tbody.innerHTML = _state.holdings.map(h => {
    const inst     = _state.instruments[h.instrument_id] || {};
    const ret      = inst.return_1y_pct ?? inst.daily_return_pct;
    const risk     = inst.risk_score ?? 2;
    const retStr   = ret != null ? ((ret >= 0 ? '+' : '') + ret.toFixed(1) + '%') : '—';
    const retColor = (ret || 0) > 0 ? '#16a34a' : (ret || 0) < 0 ? '#dc2626' : '#64748b';

    const hd      = hedgeMap[h.instrument_id];
    const sigMove = hd ? '±' + (hd.ann_vol_pct * Math.sqrt(tMonths / 12)).toFixed(1) + '%' : '—';
    const checked = _state.hedgeChecked.has(h.instrument_id);

    return `<tr style="border-bottom:1px solid rgba(0,0,0,.05)">
      <td style="padding:9px 10px">
        <span style="font-weight:700;font-family:'IBM Plex Mono',monospace;font-size:13px">${h.instrument_id}</span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--t2);margin-left:5px">${h.allocation_pct}%</span>
        ${hd ? `<br><span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#94a3b8">${_fmtEur(hd.position_eur)}</span>` : ''}
      </td>
      <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;color:${retColor};white-space:nowrap">${retStr}</td>
      <td style="padding:9px 10px">${_riskDots(risk)}</td>
      <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;color:#64748b;white-space:nowrap">${sigMove}</td>
      <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;color:#dc2626;white-space:nowrap">${hd ? '−' + _fmtEur(hd.var_95_eur) : '—'}</td>
      <td style="padding:9px 10px;text-align:center">
        ${hd ? '<span style="font-size:11px;font-weight:700;background:rgba(22,163,74,.12);color:#16a34a;padding:2px 7px;border-radius:100px;font-family:var(--fm)">95%</span>' : '—'}
      </td>
      <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;white-space:nowrap">${hd ? _fmtEur(hd.put_cost_eur) : '—'}</td>
      <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:700;color:#2563eb;white-space:nowrap">${hd && hd.var_95_eur != null && hd.put_cost_eur != null ? _fmtEur(hd.var_95_eur - hd.put_cost_eur) : '—'}</td>
      <td style="padding:9px 14px;text-align:center">
        ${hd ? `<input type="checkbox" ${checked ? 'checked' : ''} onchange="phToggleHedge('${h.instrument_id}')" style="width:16px;height:16px;cursor:pointer;accent-color:#BE185D">` : ''}
      </td>
    </tr>`;
  }).join('');

  // Totals row
  const hedged = _state.holdings.filter(h => hedgeMap[h.instrument_id]);
  if (hedged.length) {
    const totalDrop    = hedged.reduce((s, h) => s + (hedgeMap[h.instrument_id].var_95_eur ?? 0), 0);
    const totalCost    = hedged.reduce((s, h) => s + (hedgeMap[h.instrument_id].put_cost_eur ?? 0), 0);
    const totalSaving  = totalDrop - totalCost;
    const hasEur = hedged.some(h => hedgeMap[h.instrument_id].position_eur != null);
    if (hasEur) {
      tbody.innerHTML += `<tr style="border-top:2px solid rgba(0,0,0,.1);background:rgba(100,116,139,.04)">
        <td style="padding:9px 10px;font-size:11px;font-weight:700;color:var(--t2);font-family:var(--fm);text-transform:uppercase;letter-spacing:.04em">Portfolio total</td>
        <td colspan="4" style="padding:9px 10px"></td>
        <td style="padding:9px 10px;text-align:center"><span style="font-size:11px;font-weight:700;background:rgba(22,163,74,.12);color:#16a34a;padding:2px 7px;border-radius:100px;font-family:var(--fm)">95%</span></td>
        <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:700;white-space:nowrap">${_fmtEur(totalCost)}</td>
        <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:700;color:#2563eb;white-space:nowrap">${_fmtEur(totalSaving)}</td>
        <td></td>
      </tr>`;
    }
  }

  _renderAllocation();
}

// ── Allocation tab ────────────────────────────────────────────────────────────
function _renderAllocation() {
  if (!_state.apiHedge) return;

  const tMonths = _DURATION_MONTHS[_state.duration];
  const SIGMAS  = [-2, -1, 0, 1];

  const rows = _state.apiHedge.holdings.map(h => {
    const sel        = _state.selections[h.instrument_id] || 'put_buy';
    const callStrike = Math.abs(h.strike_pct);
    const cells = SIGMAS.map(n => {
      const move     = n * h.ann_vol_pct * Math.sqrt(tMonths / 12);
      const unhedged = move;
      const hedged   = sel === 'put_buy'
        ? Math.max(move, h.strike_pct) - h.cost_pct
        : Math.min(move, callStrike) + h.call_sell_cost_pct;
      return { unhedged, hedged };
    });
    return { h, sel, cells };
  });

  const totalWeight = rows.reduce((s, r) => s + r.h.weight, 0) || 100;
  const aggCells = SIGMAS.map((_, i) => ({
    unhedged: rows.reduce((s, r) => s + r.cells[i].unhedged * (r.h.weight / totalWeight), 0),
    hedged:   rows.reduce((s, r) => s + r.cells[i].hedged   * (r.h.weight / totalWeight), 0),
  }));

  const tbody = document.getElementById('ph-alloc-body');
  if (tbody) {
    tbody.innerHTML = rows.map(({ h, sel, cells }) => {
      const stratColor = sel === 'put_buy' ? '#1d4ed8' : '#7c3aed';
      const stratLabel = sel === 'put_buy' ? 'Put Buy' : 'Sell Call';
      return `<tr style="border-bottom:1px solid rgba(0,0,0,.04)">
        <td style="padding:8px 10px;font-weight:700;font-family:'IBM Plex Mono',monospace;font-size:12px">
          ${h.instrument_id}
          <span style="font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(0,0,0,.06);color:${stratColor};margin-left:4px;font-weight:600">${stratLabel}</span>
        </td>
        ${cells.map(c => `<td style="padding:8px 6px;text-align:right;vertical-align:middle">
          <div>${_fmtPct(c.unhedged)}</div>
          <div style="margin-top:2px;padding:2px 4px;background:rgba(190,24,93,.06);border-radius:3px">${_fmtPct(c.hedged)}</div>
        </td>`).join('')}
      </tr>`;
    }).join('');
  }

  const aggRow = document.getElementById('ph-alloc-agg-row');
  if (aggRow) {
    aggRow.innerHTML = `<td style="padding:8px 10px;font-weight:700;font-size:12px;color:#BE185D;font-family:var(--fm)">Portfolio</td>
      ${aggCells.map(c => `<td style="padding:8px 6px;text-align:right;vertical-align:middle">
        <div>${_fmtPct(c.unhedged)}</div>
        <div style="margin-top:2px;padding:2px 4px;background:rgba(190,24,93,.1);border-radius:3px">${_fmtPct(c.hedged)}</div>
      </td>`).join('')}`;
  }

  // Summary strip
  const agg = _state.apiHedge.aggregate;
  _setText('ph-alloc-cost', `${agg.monthly_cost_pct.toFixed(2)}%/mo`);
  _setText('ph-alloc-dd',   `${agg.max_dd_protected_pct.toFixed(0)}%`);
}

// ── Hedge tab: old hedge table + coverage dial + payoff simulator ─────────────

// Client-side risk estimate (fallback when no risk_score from API)
function _estRisk(daily_return_pct) {
  const abs = Math.abs(daily_return_pct || 0);
  if (abs < 0.3) return 1;
  if (abs < 0.7) return 2;
  if (abs < 1.2) return 3;
  if (abs < 2.0) return 4;
  return 5;
}

function _hedgeType(id, region, alloc_pct) {
  if (_FNO_ELIGIBLE.has(id)) return alloc_pct >= 20 ? 'put_spread' : 'protective_put';
  if (region === 'US' || region === 'EU') return 'ndx_proxy';
  return 'nifty_proxy';
}

function _hedgeLabel(type) {
  return {
    protective_put: 'Protective put',
    put_spread:     'Put spread',
    ndx_proxy:      'NDX put proxy',
    nifty_proxy:    'NIFTY put proxy',
  }[type] || type;
}

function _isProxy(type) { return type === 'ndx_proxy' || type === 'nifty_proxy'; }

function _rowParams(type, risk, coverage) {
  const c = coverage / 100;
  const strikePct = -(12 - c * 10);

  let strikeLabel;
  if (type === 'put_spread') {
    const lo = Math.round(strikePct);
    const hi = Math.round(strikePct - 6);
    strikeLabel = `${lo}/${hi}%`;
  } else {
    strikeLabel = `${Math.round(strikePct)}% OTM`;
  }

  const baseVol = risk * 0.065;
  const costPct = _isProxy(type)
    ? baseVol * 0.28 * (0.4 + c * 0.6)
    : baseVol * 0.40 * (0.4 + c * 0.6);

  const protectedPct = Math.round((30 + c * 50) * (_isProxy(type) ? 0.85 : 1));
  return { strikePct, strikeLabel, costPct, protectedPct };
}

function _buildRows() {
  // Build API lookup by instrument_id
  const apiMap = {};
  if (_state.apiHedge && Array.isArray(_state.apiHedge.holdings)) {
    for (const h of _state.apiHedge.holdings) apiMap[h.instrument_id] = h;
  }

  return _state.holdings.map(h => {
    const inst   = _state.instruments[h.instrument_id] || {};
    const region = inst.region || 'Other';
    const api    = apiMap[h.instrument_id];

    if (api) {
      return {
        id:           h.instrument_id,
        weight:       h.allocation_pct,
        ret:          api.return_1y_pct ?? inst.daily_return_pct,
        risk:         api.risk_score ?? _estRisk(inst.daily_return_pct),
        region,
        type:         api.hedge_type,
        label:        _hedgeLabel(api.hedge_type),
        proxy:        _isProxy(api.hedge_type),
        strikePct:    api.strike_pct,
        strikeLabel:  api.strike_label,
        costPct:      api.cost_pct,
        protectedPct: api.protected_pct,
      };
    }

    // Client-side fallback
    const risk   = _estRisk(inst.daily_return_pct);
    const ret    = inst.return_1y_pct ?? inst.daily_return_pct;
    const type   = _hedgeType(h.instrument_id, region, h.allocation_pct);
    const params = _rowParams(type, risk, _state.coverage);
    return {
      id: h.instrument_id, weight: h.allocation_pct, ret, risk, region,
      type, label: _hedgeLabel(type), proxy: _isProxy(type), ...params,
    };
  });
}

function _aggregates(rows) {
  if (_state.apiHedge && _state.apiHedge.aggregate) {
    const agg = _state.apiHedge.aggregate;
    const avgStrike = rows.reduce((s, r) => s + r.strikePct * (r.weight / 100), 0);
    return {
      totalCost:     agg.monthly_cost_pct,
      avgStrike,
      maxDdHedged:   agg.max_dd_protected_pct,
      maxDdUnhedged: agg.max_dd_unhedged_pct,
    };
  }
  const totalCost   = rows.reduce((s, r) => s + r.costPct * (r.weight / 100), 0);
  const avgStrike   = rows.reduce((s, r) => s + r.strikePct * (r.weight / 100), 0);
  const maxDdHedged = Math.max(avgStrike - totalCost, -25);
  return { totalCost, avgStrike, maxDdHedged, maxDdUnhedged: -22 };
}

function _renderTable() {
  const rows  = _buildRows();
  const tbody = document.getElementById('ph-table-body');
  if (!tbody) return;

  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="padding:16px;text-align:center;color:#94a3b8;font-size:12px">No portfolio holdings to display.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(r => {
    const retColor = (r.ret || 0) > 0 ? '#16a34a' : (r.ret || 0) < 0 ? '#dc2626' : '#64748b';
    const retStr   = r.ret != null ? ((r.ret >= 0 ? '+' : '') + r.ret.toFixed(2) + '%') : '—';
    const proxyStyle = r.proxy
      ? 'border:1px solid rgba(190,24,93,.4);color:#BE185D;background:rgba(190,24,93,.06)'
      : 'border:1px solid rgba(0,0,0,.1);color:#64748b;background:rgba(0,0,0,.03)';
    const barW = Math.min(r.protectedPct, 100);
    return `<tr style="border-bottom:1px solid rgba(0,0,0,.05);background:${r.proxy ? 'rgba(190,24,93,.02)' : 'transparent'}">
      <td style="padding:9px 10px;font-weight:700;font-family:'IBM Plex Mono',monospace;font-size:13px">${r.id}</td>
      <td style="padding:9px 10px;text-align:right;font-family:'IBM Plex Mono',monospace;font-size:12px">${r.weight}%</td>
      <td style="padding:9px 10px;text-align:right;font-family:'IBM Plex Mono',monospace;font-size:12px;color:${retColor}">${retStr}</td>
      <td style="padding:9px 10px">${_riskDots(r.risk)}</td>
      <td style="padding:9px 10px">
        <span style="display:inline-block;font-size:11px;padding:2px 8px;border-radius:100px;font-weight:500;white-space:nowrap;${proxyStyle}">${r.label}</span>
      </td>
      <td style="padding:9px 10px;font-family:'IBM Plex Mono',monospace;font-size:12px;color:#64748b">${r.strikeLabel}</td>
      <td style="padding:9px 10px;text-align:right;font-family:'IBM Plex Mono',monospace;font-size:12px">${r.costPct.toFixed(2)}%</td>
      <td style="padding:9px 10px">
        <div style="display:flex;align-items:center;gap:8px">
          <div style="width:60px;height:5px;border-radius:3px;background:rgba(0,0,0,.08)">
            <div style="width:${barW}%;height:100%;border-radius:3px;background:#BE185D"></div>
          </div>
          <span style="font-size:12px;font-family:'IBM Plex Mono',monospace;font-weight:600">${r.protectedPct}%</span>
        </div>
      </td>
    </tr>`;
  }).join('');

  const note = document.getElementById('ph-no-fno-note');
  if (note) note.style.display = rows.some(r => r.proxy) ? '' : 'none';
}

function _renderCoverageBand() {
  const rows = _buildRows();
  if (!rows.length) return;
  const { totalCost, maxDdHedged, maxDdUnhedged } = _aggregates(rows);

  _setText('ph-max-dd-hedged',   `${maxDdHedged.toFixed(0)}%`);
  _setText('ph-max-dd-unhedged', `vs ${maxDdUnhedged.toFixed(0)}% unhedged`);
  _setText('ph-monthly-cost',    `${totalCost.toFixed(2)}%`);
  _setText('ph-monthly-cost-sub','premium drag');

  const c = _state.coverage;
  let label = 'Lightly hedged';
  if (c <= 20) label = 'Unhedged';
  else if (c >= 80) label = 'Fully protected';
  _setText('ph-coverage-label', label);
}

function _renderPayoffChart() {
  const canvas = document.getElementById('ph-payoff-chart');
  if (!canvas) return;
  const rows = _buildRows();
  if (!rows.length) return;

  const { totalCost, avgStrike } = _aggregates(rows);
  const moves = [];
  for (let m = -25; m <= 15; m++) moves.push(m);

  function _hedgedPL(m, tab) {
    if (tab === 'pp') {
      return Math.max(m, avgStrike) - totalCost;
    } else if (tab === 'ps') {
      const lo = avgStrike;
      const hi = avgStrike - 5;
      if (m > lo) return m - totalCost * 0.65;
      if (m > hi) return lo - totalCost * 0.65;
      return m + (lo - hi) - totalCost * 0.65;
    } else {
      return Math.max(Math.min(m, 5), avgStrike) - totalCost;
    }
  }

  const hedgedData = moves.map(m => parseFloat(_hedgedPL(m, _scenarioTab).toFixed(2)));

  if (_payoffChart) { _payoffChart.destroy(); _payoffChart = null; }

  requestAnimationFrame(() => {
    _payoffChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: moves.map(m => m + '%'),
        datasets: [
          { label: 'hedged',   data: hedgedData, borderColor: '#BE185D', borderWidth: 2.5, pointRadius: 0, tension: 0.1, fill: false },
          { label: 'unhedged', data: moves, borderColor: 'rgba(100,116,139,.5)', borderWidth: 1.5, borderDash: [5, 4], pointRadius: 0, fill: false },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top', labels: { font: { family: 'IBM Plex Mono', size: 10 }, boxWidth: 20, padding: 10 } },
          tooltip: { mode: 'index', intersect: false, callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%` } },
        },
        scales: {
          x: { title: { display: true, text: 'market move →', font: { family: 'IBM Plex Mono', size: 10 } }, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: { family: 'IBM Plex Mono', size: 9 }, maxTicksLimit: 10 } },
          y: { title: { display: true, text: 'P&L %', font: { family: 'IBM Plex Mono', size: 10 } }, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: { family: 'IBM Plex Mono', size: 9 }, callback: v => v + '%' } },
        },
      },
    });
  });
}

function _renderScenarioTable() {
  const rows = _buildRows();
  if (!rows.length) return;
  const { totalCost, avgStrike } = _aggregates(rows);
  const MOVES = [-20, -10, 0, 10];

  function _hedgedPL(m, tab) {
    if (tab === 'pp') return Math.max(m, avgStrike) - totalCost;
    if (tab === 'ps') {
      const lo = avgStrike;
      const hi = avgStrike - 5;
      if (m > lo) return m - totalCost * 0.65;
      if (m > hi) return lo - totalCost * 0.65;
      return m + (lo - hi) - totalCost * 0.65;
    }
    return Math.max(Math.min(m, 5), avgStrike) - totalCost;
  }

  function _fmtPctLegacy(v) {
    const s     = v.toFixed(0);
    const color = v > 0 ? '#16a34a' : v < -0.5 ? '#dc2626' : '#64748b';
    return `<span style="font-family:'IBM Plex Mono',monospace;font-weight:700;color:${color}">${v > 0 ? '+' : ''}${s}%</span>`;
  }

  const tbody = document.getElementById('ph-scenario-body');
  if (tbody) {
    tbody.innerHTML = MOVES.map(m => {
      const hedged = _hedgedPL(m, _scenarioTab);
      const mLabel = m === 0 ? 'Flat' : (m > 0 ? '+' : '') + m + '%';
      return `<tr style="border-bottom:1px solid rgba(0,0,0,.06)">
        <td style="padding:8px 12px;font-size:13px;color:#64748b">${mLabel}</td>
        <td style="padding:8px 12px;text-align:right">${_fmtPctLegacy(m)}</td>
        <td style="padding:8px 12px;text-align:right">${_fmtPctLegacy(hedged)}</td>
      </tr>`;
    }).join('');
  }

  _setText('ph-cost-display', `${totalCost.toFixed(2)}%/mo`);
  const badge = document.getElementById('ph-chart-coverage-badge');
  if (badge) badge.textContent = `at ${_state.coverage}% coverage`;
}

function _highlightScenarioTab() {
  ['pp', 'ps', 'collar'].forEach(t => {
    const btn = document.getElementById(`ph-tab-${t}`);
    if (!btn) return;
    if (t === _scenarioTab) {
      btn.style.background = '#BE185D'; btn.style.color = '#fff'; btn.style.border = '1px solid #BE185D';
    } else {
      btn.style.background = 'transparent'; btn.style.color = '#64748b'; btn.style.border = '1px solid rgba(0,0,0,.12)';
    }
  });
}

function _renderHedge() {
  _setText('ph-portfolio-name', _state._portfolioName || '—');
  const slider = document.getElementById('ph-coverage-slider');
  if (slider) slider.value = _state.coverage;
  _renderTable();
  _renderCoverageBand();
  _renderPayoffChart();
  _renderScenarioTable();
  _highlightScenarioTab();
}

// ── API fetch ─────────────────────────────────────────────────────────────────
async function _fetchHedge(token) {
  try {
    let url = `/api/v1/experience/fno/portfolio-hedge?coverage=${_state.coverage}&duration=${_state.duration}`;
    if (_state.totalValueEur != null) url += `&total_value_eur=${_state.totalValueEur}`;
    return await apiFetch(url, { headers: { Authorization: `Bearer ${token}` } });
  } catch (_) {
    return null;
  }
}

// ── Entry point ───────────────────────────────────────────────────────────────
export async function loadPortfolioHedge() {
  _show('ph-loading');
  _hide('ph-error');
  _hide('ph-empty');
  _hide('ph-content');

  // On localhost always remint the dev token — ensureDevToken skips refresh when a
  // token already exists, so a stale token from a server restart would never clear.
  if (isLocalDev()) {
    sessionStorage.removeItem('auth_token');
    await ensureDevToken();
  }

  const token = sessionStorage.getItem('auth_token');
  if (!token) {
    _hide('ph-loading');
    _show('ph-empty');
    _setText('ph-empty-msg', 'Please sign in to view your hedge plan.');
    return;
  }

  try {
    const [portfolio, geo] = await Promise.all([
      apiFetch('/api/v1/experience/user-portfolio', { headers: { Authorization: `Bearer ${token}` } }),
      apiFetch('/api/v1/experience/rita/geography-overview'),
    ]);

    _hide('ph-loading');

    if (!portfolio) {
      _show('ph-empty');
      _setText('ph-empty-msg', 'Could not load portfolio — check the server is running and try again.');
      return;
    }

    if (!portfolio.holdings || !portfolio.holdings.length) {
      _show('ph-empty');
      _setText('ph-empty-msg', 'No portfolio saved yet. Build one in the RITA Portfolio Builder.');
      return;
    }

    _state.holdings       = portfolio.holdings;
    _state._portfolioName = portfolio.name || '';
    _state.totalValueEur  = portfolio.total_value_eur ?? null;
    _state.instruments    = {};

    if (geo && geo.regions) {
      for (const r of geo.regions) {
        for (const i of (r.instruments || [])) {
          _state.instruments[i.id] = { ...i, region: r.region };
        }
      }
    }

    // Reset wizard
    _state.tab          = 'discover';
    _state.duration     = '1y';
    _state.coverage     = 50;
    _state.apiHedge     = null;
    _state.selections   = {};
    _state.hedgeChecked = new Set();
    _state.reached      = new Set(_TAB_ORDER);

    // Fetch hedge data eagerly so Discover tab is fully populated on load
    const hedgeData = await _fetchHedge(token);
    _state.apiHedge = hedgeData;
    if (hedgeData?.holdings) {
      for (const h of hedgeData.holdings) {
        _state.selections[h.instrument_id] = (h.risk_score ?? 2) >= 3 ? 'put_buy' : 'call_sell';
      }
    }

    _show('ph-content');
    _goToTab('discover');

  } catch (e) {
    _hide('ph-loading');
    _show('ph-error');
    _setText('ph-error-msg', e.message || 'Failed to load portfolio.');
    console.error('[PH] loadPortfolioHedge error:', e);
  }
}

// ── Window-exposed actions ────────────────────────────────────────────────────

export function phSetDuration(d) {
  _state.duration = d;
  _renderDiscover();
  const token = sessionStorage.getItem('auth_token');
  if (token) {
    _fetchHedge(token).then(data => {
      if (data) { _state.apiHedge = data; _renderDiscover(); }
    });
  }
}

export function phGoNext() {
  const idx = _TAB_ORDER.indexOf(_state.tab);
  if (idx < 0 || idx >= _TAB_ORDER.length - 1) return;
  _goToTab(_TAB_ORDER[idx + 1]);
}

export function phGoBack() {
  const idx = _TAB_ORDER.indexOf(_state.tab);
  if (idx <= 0) return;
  _goToTab(_TAB_ORDER[idx - 1]);
}

export function phGoToTab(tab) {
  _goToTab(tab);
}

export function phPickStrategy(id, strategy) {
  _state.selections[id] = strategy;
}

export function phSetTotalEur(val) {
  const v = parseFloat(val);
  _state.totalValueEur = isNaN(v) || v <= 0 ? null : v;
}

export function phToggleHedge(id) {
  if (_state.hedgeChecked.has(id)) {
    _state.hedgeChecked.delete(id);
  } else {
    _state.hedgeChecked.add(id);
  }
}

export function phSetCoverage(val) {
  _state.coverage = parseInt(val, 10);
  _renderCoverageBand();
  _renderPayoffChart();
  _renderScenarioTable();

  // Debounced API re-fetch
  const token = sessionStorage.getItem('auth_token');
  if (token) {
    const captureCov = _state.coverage;
    setTimeout(async () => {
      if (captureCov !== _state.coverage) return;
      const fresh = await _fetchHedge(token);
      if (fresh && captureCov === _state.coverage) {
        _state.apiHedge = fresh;
        _renderTable();
        _renderCoverageBand();
      }
    }, 300);
  }
}

export function phSetScenarioTab(tab) {
  _scenarioTab = tab;
  _highlightScenarioTab();
  _renderPayoffChart();
  _renderScenarioTable();
}
