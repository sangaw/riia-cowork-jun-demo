// ── Portfolio Builder — Feature 28 Phase 1 ────────────────────────────────────
// Section entry point: loadPortfolioBuilder()
// API: GET /api/v1/experience/rita/geography-overview (no auth)
//      GET /api/v1/experience/user-portfolio          (JWT, silent 404)
//      POST /api/v1/user-portfolio/                   (JWT, basket build)

import { api, apiFetch } from './api.js';

// ── State ─────────────────────────────────────────────────────────────────────
const _basket = new Set();
let _mapChart  = null;
let _draftChart = null;
let _sortCol   = 'return';
let _sortAsc   = false;
let _geoCache  = null;
let _draftItems = [];   // [{id, ret, on}]
let _activePreset = null;

// ── Sector lookup (Phase 1 derived; Phase 2 replaces with API field) ──────────
const _SECTOR_MAP = {
  RELIANCE:'Energy',   TATAMOTOR:'Auto',      SBIN:'Financials',
  TCS:'Tech',          HDFCBANK:'Financials',  INFY:'Tech',
  WIPRO:'Tech',        BAJFINANCE:'Financials', TATASTEEL:'Materials',
  NVIDIA:'Tech',       MSFT:'Tech',            AAPL:'Tech',
  TSLA:'Auto',         GOOGL:'Tech',           AMZN:'Consumer',
  ASML:'Tech',         SAP:'Tech',             NESTLE:'Consumer',
  LVMH:'Consumer',
};

// ── DOM helpers ───────────────────────────────────────────────────────────────
function _show(id) { const el = document.getElementById(id); if (el) el.style.display = ''; }
function _hide(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; }
function _setText(id, txt) { const el = document.getElementById(id); if (el) el.textContent = txt; }

// ── Data helpers ──────────────────────────────────────────────────────────────
function _estRisk(pct) {
  const abs = Math.abs(pct || 0);
  if (abs < 0.3) return 1;
  if (abs < 0.7) return 2;
  if (abs < 1.2) return 3;
  if (abs < 2.0) return 4;
  return 5;
}

function _riskDots(r) {
  return Array.from({ length: 5 }, (_, i) =>
    `<span style="font-size:11px;color:${i < r ? '#BE185D' : 'rgba(0,0,0,.15)'}">●</span>`
  ).join('');
}

function _miniBar(pct) {
  const w = Math.min(Math.abs(pct || 0) * 10, 40);
  return `<span style="display:inline-block;width:${w}px;height:5px;border-radius:2px;background:${(pct||0)>=0?'#BE185D':'#94a3b8'};vertical-align:middle;flex-shrink:0"></span>`;
}

function _fmtRet(pct, est) {
  if (pct == null) return '—';
  return (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%' + (est ? ' (est.)' : '');
}

function _allInstruments(geo) {
  return (geo.regions || []).flatMap(r => r.instruments || []);
}

function _regionDisplay(apiRegion) {
  return { India: 'India', US: 'US', EU: 'Europe', Other: 'Other' }[apiRegion] || apiRegion;
}

function _buildRegionLookup(geo) {
  const map = {};
  for (const r of (geo.regions || [])) {
    const d = _regionDisplay(r.region);
    for (const i of (r.instruments || [])) map[i.id] = d;
  }
  return map;
}

// ── Render: region buckets ────────────────────────────────────────────────────
function _renderBuckets(geo) {
  const keyMap = { India: 'india', US: 'us', EU: 'europe' };
  for (const region of (geo.regions || [])) {
    const key = keyMap[region.region];
    if (!key) continue; // "Other" instruments show in table/map only

    const container = document.getElementById(`pb-instruments-${key}`);
    if (!container) continue;

    const insts = region.instruments || [];
    const avg = insts.length ? insts.reduce((s, i) => s + (i.daily_return_pct || 0), 0) / insts.length : null;

    const metaEl = document.getElementById(`pb-region-meta-${key}`);
    if (metaEl) metaEl.textContent = `${insts.length} instruments · ranked by return`;
    const avgEl = document.getElementById(`pb-region-avg-${key}`);
    if (avgEl && avg != null) {
      avgEl.textContent = _fmtRet(avg);
      avgEl.style.color = avg >= 0 ? '#16a34a' : '#dc2626';
    }

    const sorted = [...insts].sort((a, b) => (b.daily_return_pct || 0) - (a.daily_return_pct || 0));

    container.innerHTML = sorted.map(inst => {
      const inBasket = _basket.has(inst.id);
      const sector = _SECTOR_MAP[inst.id] || '—';
      const retColor = (inst.daily_return_pct || 0) >= 0 ? '#16a34a' : '#dc2626';
      return `<div onclick="pbToggleInstrument('${inst.id}')"
                   style="display:flex;align-items:center;gap:8px;padding:7px 8px;border-radius:6px;cursor:pointer;
                          border:1px solid ${inBasket ? 'rgba(190,24,93,.3)' : 'transparent'};
                          background:${inBasket ? 'rgba(190,24,93,.06)' : 'transparent'};margin-bottom:3px">
        <input type="checkbox" ${inBasket ? 'checked' : ''} onclick="event.stopPropagation();pbToggleInstrument('${inst.id}')" style="accent-color:#BE185D;flex-shrink:0">
        <div style="flex:1;min-width:0">
          <div style="font-weight:700;font-size:13px;color:${inBasket ? '#BE185D' : 'var(--text)'}">${inst.id}</div>
          <span style="display:inline-block;font-size:10px;padding:1px 6px;border-radius:100px;background:rgba(0,0,0,.06);color:var(--t2);font-weight:500">${sector}</span>
        </div>
        ${_miniBar(inst.daily_return_pct)}
        <span style="font-size:12px;font-weight:700;font-family:'IBM Plex Mono',monospace;color:${retColor};white-space:nowrap">${_fmtRet(inst.daily_return_pct, true)}</span>
      </div>`;
    }).join('') || '<div style="color:#94a3b8;font-size:12px;padding:8px">No instruments</div>';
  }
}

// ── Render: basket sidebar ────────────────────────────────────────────────────
function _renderBasket() {
  const geo = _geoCache;
  const count = _basket.size;

  const badge = document.getElementById('pb-basket-badge');
  if (badge) badge.textContent = count;

  const listEl  = document.getElementById('pb-basket-list');
  const emptyMsg = document.getElementById('pb-basket-empty-msg');
  if (listEl) {
    if (count === 0) {
      listEl.innerHTML = '';
      if (emptyMsg) emptyMsg.style.display = '';
    } else {
      if (emptyMsg) emptyMsg.style.display = 'none';
      const regionLookup = geo ? _buildRegionLookup(geo) : {};
      listEl.innerHTML = [..._basket].map(id => `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border)">
          <div>
            <div style="font-weight:700;font-size:13px;font-family:'IBM Plex Mono',monospace">${id}</div>
            ${regionLookup[id] ? `<div style="font-size:11px;color:var(--t2)">${regionLookup[id]}</div>` : ''}
          </div>
          <button onclick="pbToggleInstrument('${id}')" style="background:none;border:none;color:var(--t2);cursor:pointer;font-size:18px;line-height:1;padding:0 4px">×</button>
        </div>`).join('');
    }
  }

  // Stats
  const regions = new Set();
  let totalRet = 0, retCount = 0;
  if (geo) {
    for (const r of (geo.regions || [])) {
      for (const i of (r.instruments || [])) {
        if (_basket.has(i.id)) {
          regions.add(r.region);
          if (i.daily_return_pct != null) { totalRet += i.daily_return_pct; retCount++; }
        }
      }
    }
  }
  const avgRet = retCount > 0 ? totalRet / retCount : null;

  const regEl = document.getElementById('pb-basket-regions');
  if (regEl) regEl.textContent = regions.size || '—';

  const avgEl = document.getElementById('pb-basket-avg-return');
  if (avgEl) {
    avgEl.textContent = avgRet != null ? _fmtRet(avgRet) : '—';
    if (avgRet != null) avgEl.style.color = avgRet >= 0 ? '#16a34a' : '#dc2626';
  }

  const buildBtn = document.getElementById('pb-basket-build-btn');
  if (buildBtn) buildBtn.disabled = count === 0;
}

// ── Render: scatter map ───────────────────────────────────────────────────────
function _renderMap(geo) {
  const instruments = _allInstruments(geo).filter(i => i.daily_return_pct != null);
  const mapEmpty = document.getElementById('pb-map-empty');

  if (!instruments.length) {
    _hide('pb-map-canvas');
    if (mapEmpty) mapEmpty.style.display = '';
    return;
  }
  _show('pb-map-canvas');
  if (mapEmpty) mapEmpty.style.display = 'none';

  if (_mapChart) { _mapChart.destroy(); _mapChart = null; }
  const canvas = document.getElementById('pb-map-canvas');
  if (!canvas) return;

  const points = instruments.map(i => ({
    x: i.daily_return_pct,
    y: _estRisk(i.daily_return_pct),
    label: i.id,
  }));

  requestAnimationFrame(() => {
    _mapChart = new Chart(canvas, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Instruments',
          data: points.map(p => ({ x: p.x, y: p.y })),
          backgroundColor: points.map(p => _basket.has(p.label) ? 'rgba(190,24,93,.85)' : 'rgba(100,116,139,.5)'),
          pointRadius: points.map(p => _basket.has(p.label) ? 9 : 7),
          pointHoverRadius: 11,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        onClick: (_, elements) => {
          if (elements.length > 0) pbToggleInstrument(points[elements[0].index].label);
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => {
                const p = points[ctx.dataIndex];
                return `${p.label}  ret: ${ctx.parsed.x.toFixed(2)}%  risk: ${ctx.parsed.y}/5`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: 'RETURN →', font: { family: 'IBM Plex Mono', size: 10 } },
            grid: { color: 'rgba(0,0,0,.05)' },
            ticks: { font: { family: 'IBM Plex Mono', size: 10 } },
          },
          y: {
            title: { display: true, text: 'RISK →', font: { family: 'IBM Plex Mono', size: 10 } },
            min: 0, max: 6,
            ticks: { stepSize: 1, font: { family: 'IBM Plex Mono', size: 10 }, callback: v => (v > 0 && v < 6) ? v : '' },
            grid: { color: 'rgba(0,0,0,.05)' },
          },
        },
      },
    });
  });
}

// ── Render: sortable table ────────────────────────────────────────────────────
function _renderTable(geo) {
  const regionLookup = _buildRegionLookup(geo);
  let instruments = _allInstruments(geo).slice().sort((a, b) => {
    let av, bv;
    if (_sortCol === 'name')   { av = a.id; bv = b.id; }
    if (_sortCol === 'region') { av = regionLookup[a.id] || ''; bv = regionLookup[b.id] || ''; }
    if (_sortCol === 'return') { av = a.daily_return_pct ?? -999; bv = b.daily_return_pct ?? -999; }
    if (_sortCol === 'risk')   { av = _estRisk(a.daily_return_pct); bv = _estRisk(b.daily_return_pct); }
    if (av === bv) return 0;
    const cmp = av < bv ? -1 : 1;
    return _sortAsc ? cmp : -cmp;
  });

  const wrap = document.getElementById('pb-table-wrap');
  const tableEmpty = document.getElementById('pb-table-empty');
  if (!instruments.length) {
    if (wrap) wrap.style.display = 'none';
    if (tableEmpty) tableEmpty.style.display = '';
    return;
  }
  if (wrap) wrap.style.display = '';
  if (tableEmpty) tableEmpty.style.display = 'none';

  function _th(col, label) {
    const active = _sortCol === col;
    return `<th onclick="pbSortTable('${col}')" style="padding:8px;text-align:${col==='return'?'right':'left'};font-weight:700;cursor:pointer;user-select:none">
      ${label}${active ? (' ' + (_sortAsc ? '▲' : '▼')) : ''}
    </th>`;
  }

  const table = document.getElementById('pb-table');
  if (!table) return;
  table.innerHTML = `
    <thead>
      <tr style="font-size:11px;color:#64748b;border-bottom:2px solid rgba(0,0,0,.1);text-transform:uppercase;letter-spacing:.04em">
        <th style="padding:8px;width:30px"></th>
        ${_th('name','Ticker')}
        ${_th('region','Region')}
        ${_th('return','Return')}
        ${_th('risk','Risk')}
        <th style="padding:8px;text-align:center">Action</th>
      </tr>
    </thead>
    <tbody>
      ${instruments.map(i => {
        const inBasket = _basket.has(i.id);
        const retColor = (i.daily_return_pct || 0) > 0 ? '#16a34a' : (i.daily_return_pct || 0) < 0 ? '#dc2626' : '#64748b';
        const risk = _estRisk(i.daily_return_pct);
        const region = regionLookup[i.id] || '—';
        return `<tr onclick="pbToggleInstrument('${i.id}')"
                    style="cursor:pointer;border-bottom:1px solid rgba(0,0,0,.05);background:${inBasket ? 'rgba(190,24,93,.04)' : 'transparent'}">
          <td style="padding:7px 8px;text-align:center">
            <input type="checkbox" ${inBasket ? 'checked' : ''} onclick="event.stopPropagation();pbToggleInstrument('${i.id}')" style="accent-color:#BE185D">
          </td>
          <td style="padding:7px 8px;font-weight:700;font-family:'IBM Plex Mono',monospace;color:${inBasket ? '#BE185D' : 'var(--text)'}">
            ${i.id}
          </td>
          <td style="padding:7px 8px">
            <span style="font-size:11px;padding:2px 8px;border-radius:100px;background:rgba(0,0,0,.06);color:var(--t2);font-weight:500">${region}</span>
          </td>
          <td style="padding:7px 8px;text-align:right;font-family:'IBM Plex Mono',monospace;font-weight:700;font-size:12px;color:${retColor}">
            ${_fmtRet(i.daily_return_pct)}
          </td>
          <td style="padding:7px 8px">${_riskDots(risk)}</td>
          <td style="padding:7px 8px;text-align:center">
            <button onclick="event.stopPropagation();pbToggleInstrument('${i.id}')"
                    style="padding:4px 12px;border-radius:100px;border:none;
                           background:${inBasket ? 'rgba(190,24,93,1)' : 'rgba(0,0,0,.07)'};
                           color:${inBasket ? '#fff' : '#64748b'};
                           font-size:11px;font-weight:600;cursor:pointer;min-width:48px">
              ${inBasket ? 'added' : 'add'}
            </button>
          </td>
        </tr>`;
      }).join('')}
    </tbody>`;
}

// ── Guided basket — draft state & rendering ───────────────────────────────────
const _GOAL_PRESETS = {
  aggressive: { label: 'Aggressive growth', signalFilter: ['bullish'],              riskMin: 3 },
  balanced:   { label: 'Balanced',           signalFilter: ['bullish', 'neutral'],   riskMin: 2, riskMax: 4 },
  income:     { label: 'Income & stability', signalFilter: ['neutral', 'bullish'],   riskMax: 3 },
  custom:     { label: 'Custom',             custom: true },
};

function _draftAlloc() {
  const on = _draftItems.filter(i => i.on);
  if (!on.length) return {};
  const base = Math.floor(100 / on.length);
  const rem  = 100 - base * on.length;
  const map  = {};
  on.forEach((i, idx) => { map[i.id] = base + (idx === 0 ? rem : 0); });
  return map;
}

function _renderDraftDonut(items) {
  if (_draftChart) { _draftChart.destroy(); _draftChart = null; }
  const canvas = document.getElementById('pb-draft-donut');
  if (!canvas) return;
  const on = items.filter(i => i.on);
  const COLORS = ['#BE185D','#9f1239','#e11d48','#f43f5e','#fb7185','#fda4af','#fecdd3'];
  if (!on.length) {
    _draftChart = new Chart(canvas, {
      type: 'doughnut',
      data: { datasets: [{ data: [1], backgroundColor: ['#f1f5f9'], borderWidth: 0 }] },
      options: { plugins: { legend: { display: false }, tooltip: { enabled: false } }, cutout: '65%', responsive: false },
    });
    return;
  }
  const alloc = _draftAlloc();
  _draftChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: on.map(i => i.id),
      datasets: [{
        data: on.map(i => alloc[i.id] || 0),
        backgroundColor: on.map((_, idx) => COLORS[idx % COLORS.length]),
        borderWidth: 2,
        borderColor: '#fff',
      }],
    },
    options: {
      responsive: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.parsed}%` } },
      },
      cutout: '65%',
    },
  });
}

function _updateDraftStats() {
  const on = _draftItems.filter(i => i.on);
  const avgRet  = on.length ? on.reduce((s, i) => s + (i.ret || 0), 0) / on.length : null;
  const avgRisk = on.length ? on.reduce((s, i) => s + _estRisk(i.ret), 0) / on.length : null;

  _setText('pb-draft-holdings', on.length || '—');
  const projEl = document.getElementById('pb-draft-proj-return');
  if (projEl) {
    projEl.textContent  = avgRet != null ? _fmtRet(avgRet) : '—';
    projEl.style.color  = (avgRet || 0) >= 0 ? '#16a34a' : '#dc2626';
  }
  const riskEl = document.getElementById('pb-draft-risk');
  if (riskEl) riskEl.innerHTML = avgRisk != null ? _riskDots(Math.round(avgRisk)) : '—';

  _renderDraftDonut(_draftItems);
}

function _renderDraftList() {
  const draftEl = document.getElementById('pb-guided-draft');
  if (!draftEl) return;
  if (!_draftItems.length) {
    draftEl.innerHTML = '<div style="padding:12px 14px;color:#94a3b8;font-size:12px">Select a goal above to see a ranked draft.</div>';
    return;
  }
  const alloc = _draftAlloc();
  draftEl.innerHTML = _draftItems.map((item, idx) => {
    const retColor = (item.ret || 0) >= 0 ? '#16a34a' : '#dc2626';
    const pct = item.on ? (alloc[item.id] || 0) : 0;
    const barW = Math.min(pct * 2, 100);
    return `<div style="display:flex;align-items:center;gap:10px;padding:9px 14px;border-bottom:1px solid var(--border);background:${item.on ? 'transparent' : 'rgba(0,0,0,.02)'}">
      <span style="width:16px;text-align:right;font-size:11px;color:var(--t2);font-family:'IBM Plex Mono',monospace">${idx + 1}</span>
      <span style="font-weight:700;font-size:13px;font-family:'IBM Plex Mono',monospace;width:68px">${item.id}</span>
      <span style="font-size:12px;font-weight:700;color:${retColor};font-family:'IBM Plex Mono',monospace;width:52px">${_fmtRet(item.ret)}</span>
      <div style="flex:1;height:5px;border-radius:3px;background:rgba(0,0,0,.08)">
        <div style="width:${barW}%;height:100%;border-radius:3px;background:${item.on ? '#BE185D' : '#cbd5e1'}"></div>
      </div>
      <span style="font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--t2);width:32px;text-align:right">${item.on ? pct + '%' : ''}</span>
      <button onclick="pbToggleDraftItem('${item.id}')"
              style="width:38px;height:21px;border-radius:100px;border:none;
                     background:${item.on ? '#BE185D' : '#cbd5e1'};
                     cursor:pointer;position:relative;padding:0;flex-shrink:0;transition:background .2s">
        <span style="position:absolute;top:2px;${item.on ? 'right:2px' : 'left:2px'};
                     width:17px;height:17px;border-radius:50%;background:#fff"></span>
      </button>
    </div>`;
  }).join('');
}

function _applyPreset(presetKey, geo) {
  _activePreset = presetKey;
  const preset = _GOAL_PRESETS[presetKey];
  if (!preset) return;

  // Highlight selected goal card
  ['aggressive', 'balanced', 'income', 'custom'].forEach(k => {
    const el = document.getElementById(`pb-preset-${k}`);
    if (!el) return;
    el.style.border     = k === presetKey ? '2px solid #BE185D' : '2px solid var(--border)';
    el.style.background = k === presetKey ? 'rgba(190,24,93,.05)' : '';
  });

  const titleEl = document.getElementById('pb-draft-title');
  if (titleEl) titleEl.textContent = `Recommended for ${preset.label}`;

  let all = _allInstruments(geo);
  if (!preset.custom) {
    all = all.filter(i => {
      const r = _estRisk(i.daily_return_pct);
      if (preset.signalFilter && !preset.signalFilter.includes(i.signal)) return false;
      if (preset.riskMin != null && r < preset.riskMin) return false;
      if (preset.riskMax != null && r > preset.riskMax) return false;
      return true;
    });
  }
  // Rank by return desc, top 7; top 5 toggled on by default
  const ranked = all.slice().sort((a, b) => (b.daily_return_pct || 0) - (a.daily_return_pct || 0)).slice(0, 7);
  _draftItems = ranked.map((i, idx) => ({ id: i.id, ret: i.daily_return_pct, on: idx < 5 }));

  _renderDraftList();
  _updateDraftStats();
}

// ── Section loader ────────────────────────────────────────────────────────────
export async function loadPortfolioBuilder() {
  _hide('pb-error');
  _hide('pb-empty');
  _show('pb-loading');
  _hide('pb-status-msg');

  try {
    const geo = await apiFetch('/api/v1/experience/rita/geography-overview');
    _hide('pb-loading');

    if (!geo || !geo.regions || !geo.regions.length) {
      _show('pb-empty');
      _renderBasket();
      return;
    }
    _geoCache = geo;

    // Pre-fill basket from saved portfolio (silent on 401/404)
    try {
      const token = sessionStorage.getItem('auth_token');
      if (token) {
        const up = await apiFetch('/api/v1/experience/user-portfolio', {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (up && Array.isArray(up.holdings)) {
          for (const h of up.holdings) {
            if (h.instrument_id) _basket.add(h.instrument_id.toUpperCase());
          }
        }
      }
    } catch (_) {}

    _renderBuckets(geo);
    _renderTable(geo);
    _renderBasket();
    _renderMap(geo);

  } catch (e) {
    _hide('pb-loading');
    _setText('pb-error-msg', e.message || 'Failed to load portfolio data');
    _show('pb-error');
    console.error('[PB] load error:', e);
  }
}

// ── Exported actions ──────────────────────────────────────────────────────────
export function pbToggleInstrument(id) {
  if (_basket.has(id)) _basket.delete(id);
  else _basket.add(id);
  _renderBasket();
  if (_geoCache) {
    _renderBuckets(_geoCache);
    _renderTable(_geoCache);
    _renderMap(_geoCache);
  }
}

export function pbSelectAllRegion(regionKey) {
  if (!_geoCache) return;
  const apiKey = { india: 'India', us: 'US', europe: 'EU', other: 'Other' }[regionKey] || regionKey;
  const region = (_geoCache.regions || []).find(r => r.region === apiKey);
  if (!region) return;
  for (const i of region.instruments) _basket.add(i.id);
  _renderBasket();
  _renderBuckets(_geoCache);
  _renderTable(_geoCache);
  _renderMap(_geoCache);
}

export function pbClearAllRegion(regionKey) {
  if (!_geoCache) return;
  const apiKey = { india: 'India', us: 'US', europe: 'EU', other: 'Other' }[regionKey] || regionKey;
  const region = (_geoCache.regions || []).find(r => r.region === apiKey);
  if (!region) return;
  for (const i of region.instruments) _basket.delete(i.id);
  _renderBasket();
  _renderBuckets(_geoCache);
  _renderTable(_geoCache);
  _renderMap(_geoCache);
}

export function pbSortTable(col) {
  if (_sortCol === col) _sortAsc = !_sortAsc;
  else { _sortCol = col; _sortAsc = (col === 'name' || col === 'region'); }
  if (_geoCache) _renderTable(_geoCache);
}

export function pbApplyGoalPreset(presetKey) {
  if (_geoCache) _applyPreset(presetKey, _geoCache);
}

export function pbToggleDraftItem(id) {
  const item = _draftItems.find(i => i.id === id);
  if (!item) return;
  item.on = !item.on;
  _renderDraftList();
  _updateDraftStats();
}

export function pbBuildFromDraft() {
  const on = _draftItems.filter(i => i.on);
  if (!on.length) return;
  for (const item of on) _basket.add(item.id);
  _renderBasket();
  if (_geoCache) { _renderBuckets(_geoCache); _renderTable(_geoCache); _renderMap(_geoCache); }
  pbBuildPortfolio();
}

export function pbClearBasket() {
  _basket.clear();
  _renderBasket();
  if (_geoCache) { _renderBuckets(_geoCache); _renderTable(_geoCache); _renderMap(_geoCache); }
}

export async function pbBuildPortfolio() {
  if (_basket.size === 0) {
    const msg = document.getElementById('pb-status-msg');
    if (msg) { msg.textContent = 'Add at least one instrument to the basket first.'; msg.style.color = '#dc2626'; msg.style.display = ''; }
    return;
  }
  const token = sessionStorage.getItem('auth_token');
  if (!token) {
    const msg = document.getElementById('pb-status-msg');
    if (msg) { msg.textContent = 'Login required to build a portfolio. Please sign in.'; msg.style.color = '#dc2626'; msg.style.display = ''; }
    return;
  }
  const name = `My Portfolio ${new Date().toLocaleDateString('en-IN')}`;
  const allocationPct = Math.floor(100 / _basket.size);
  const holdings = [..._basket].map(id => ({ instrument_id: id, allocation_pct: allocationPct }));
  const rem = 100 - allocationPct * _basket.size;
  if (rem > 0 && holdings.length) holdings[0].allocation_pct += rem;

  const buildBtn      = document.getElementById('pb-basket-build-btn');
  const draftBuildBtn = document.getElementById('pb-draft-build-btn');
  [buildBtn, draftBuildBtn].forEach(b => { if (b) { b.disabled = true; b.textContent = 'Building…'; } });
  _hide('pb-status-msg');

  try {
    await api('/api/v1/user-portfolio/', 'POST', { name, holdings });
    const msg = document.getElementById('pb-status-msg');
    if (msg) { msg.textContent = `Portfolio "${name}" saved with ${_basket.size} instruments.`; msg.style.color = '#16a34a'; msg.style.display = ''; }
  } catch (e) {
    const msg = document.getElementById('pb-status-msg');
    if (msg) { msg.textContent = `Save failed: ${e.message || 'Unknown error'}`; msg.style.color = '#dc2626'; msg.style.display = ''; }
  } finally {
    if (buildBtn)      { buildBtn.disabled = _basket.size === 0; buildBtn.textContent = 'Continue → Allocate'; }
    if (draftBuildBtn) { draftBuildBtn.disabled = false; draftBuildBtn.textContent = 'Build portfolio →'; }
  }
}
