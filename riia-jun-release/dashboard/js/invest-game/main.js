import { selectDays, runDay, getResult } from './api.js';

const TRANSACTION_RATE = 0.001;
const TAX_RATE = 0.30;

const gameState = {
  gameId: null,
  instrument: 'ASML',
  currency: 'EUR',
  startingCapital: 5000,
  warmupDays: [],
  gameDays: [],
  currentDayIndex: 0,
  nextRowToReveal: 3,
  started: false,
  user: { position: 'flat', cash: 5000, shares: 0, entryPrice: 0, portfolio: 0, cumCosts: 0, cumTax: 0, netValue: 5000, prevNetValue: 5000 },
  ai:   { position: 'flat', cash: 5000, shares: 0, entryPrice: 0, portfolio: 0, cumCosts: 0, cumTax: 0, netValue: 5000, prevNetValue: 5000 }
};

function sym() {
  return gameState.currency === 'USD' ? '$' : '€';
}

function fmtAbs(value) {
  return sym() + Math.abs(value).toFixed(2);
}

function fmtSigned(value) {
  if (value > 0)  return '+' + sym() + value.toFixed(2);
  if (value < 0)  return '−' + sym() + Math.abs(value).toFixed(2);
  return sym() + '0.00';
}

function calculateDay(actor, action, closePrice) {
  let effectiveAction = action;
  if (action === 'BUY'  && actor.position === 'long') effectiveAction = 'HOLD';
  if (action === 'SELL' && actor.position === 'flat') effectiveAction = 'HOLD';

  if (effectiveAction === 'BUY') {
    const txCost = actor.cash * TRANSACTION_RATE;
    actor.cumCosts += txCost;
    actor.shares = (actor.cash - txCost) / closePrice;
    actor.cash = 0;
    actor.entryPrice = closePrice;
    actor.position = 'long';
  } else if (effectiveAction === 'SELL') {
    const proceeds = actor.shares * closePrice;
    const txCost = proceeds * TRANSACTION_RATE;
    actor.cumCosts += txCost;
    const grossProfit = actor.shares * (closePrice - actor.entryPrice);
    let tax = 0;
    if (grossProfit > 0) {
      tax = grossProfit * TAX_RATE;
      actor.cumTax += tax;
    }
    actor.cash = proceeds - txCost - tax;
    actor.shares = 0;
    actor.entryPrice = 0;
    actor.position = 'flat';
  }
  // HOLD: no changes to cash/shares/costs/tax

  actor.portfolio = actor.shares * closePrice;
  actor.netValue = actor.cash + actor.portfolio - actor.cumCosts - actor.cumTax;
}

function renderPnLCards() {
  const s = sym();
  const cap = gameState.startingCapital;

  const setCard = (prefix, actor) => {
    document.getElementById(`${prefix}-cash`).textContent      = s + actor.cash.toFixed(2);
    document.getElementById(`${prefix}-portfolio`).textContent = s + actor.portfolio.toFixed(2);
    document.getElementById(`${prefix}-costs`).textContent     = '−' + s + actor.cumCosts.toFixed(2);
    document.getElementById(`${prefix}-tax`).textContent       = '−' + s + actor.cumTax.toFixed(2);
    const netEl = document.getElementById(`${prefix}-net`);
    netEl.textContent = s + actor.netValue.toFixed(2);
    netEl.className = 'pnl-value' + (actor.netValue > cap ? ' pos' : actor.netValue < cap ? ' neg' : '');
  };

  setCard('user', gameState.user);
  setCard('ai', gameState.ai);
}

function setEndDateMax() {
  const d = new Date();
  d.setMonth(d.getMonth() - 3);
  const iso = d.toISOString().split('T')[0];
  const el = document.getElementById('end-date');
  el.max = iso;
  el.value = iso;
}

function validateDates() {
  const start = document.getElementById('start-date').value;
  const end   = document.getElementById('end-date').value;
  document.getElementById('btn-select-days').disabled = !(start && end && end > start);
}

function lockControls() {
  document.getElementById('pill-asml').disabled  = true;
  document.getElementById('pill-nvidia').disabled = true;
  document.getElementById('start-date').disabled  = true;
  document.getElementById('end-date').disabled    = true;
  document.getElementById('btn-select-days').style.display = 'none';
  document.getElementById('btn-new-game').style.display    = '';
}

function renderWarmupRows() {
  [1, 2].forEach((n, i) => {
    const d = gameState.warmupDays[i];
    document.getElementById(`row${n}-date`).textContent       = d.date;
    document.getElementById(`row${n}-instrument`).textContent = gameState.instrument;
    document.getElementById(`row${n}-price`).textContent      = sym() + d.close.toFixed(2);
  });
}

function populateActiveRowData(n) {
  const d = gameState.gameDays[n - 3];
  document.getElementById(`row${n}-date`).textContent       = d.date;
  document.getElementById(`row${n}-instrument`).textContent = gameState.instrument;
  document.getElementById(`row${n}-price`).textContent      = sym() + d.close.toFixed(2);
}

function unlockRow(n) {
  document.getElementById(`game-row-${n}`).classList.remove('locked');
  populateActiveRowData(n);
  const buyBtn  = document.getElementById(`buy-${n}`);
  const sellBtn = document.getElementById(`sell-${n}`);
  const holdBtn = document.getElementById(`hold-${n}`);
  buyBtn.disabled  = false;
  sellBtn.disabled = false;
  holdBtn.disabled = false;
  buyBtn.onclick  = () => handleUserAction(n, 'BUY');
  sellBtn.onclick = () => handleUserAction(n, 'SELL');
  holdBtn.onclick = () => handleUserAction(n, 'HOLD');
}

async function handleUserAction(n, action) {
  const buyBtn  = document.getElementById(`buy-${n}`);
  const sellBtn = document.getElementById(`sell-${n}`);
  const holdBtn = document.getElementById(`hold-${n}`);
  buyBtn.disabled  = true;
  sellBtn.disabled = true;
  holdBtn.disabled = true;
  buyBtn.classList.toggle('selected',  action === 'BUY');
  sellBtn.classList.toggle('selected', action === 'SELL');
  holdBtn.classList.toggle('selected', action === 'HOLD');

  const dayIndex   = n - 3;
  const closePrice = gameState.gameDays[dayIndex].close;

  gameState.user.prevNetValue = gameState.user.netValue;
  gameState.ai.prevNetValue   = gameState.ai.netValue;

  calculateDay(gameState.user, action, closePrice);

  let result;
  try {
    result = await runDay(gameState.gameId, dayIndex, action);
  } catch (e) {
    console.error('runDay error', e);
    buyBtn.disabled  = false;
    sellBtn.disabled = false;
    holdBtn.disabled = false;
    return;
  }

  calculateDay(gameState.ai, result.ai_action, closePrice);
  gameState.currentDayIndex = dayIndex + 1;

  // AI cell
  const aiCell = document.getElementById(`ai-cell-${n}`);
  const aiClass = result.ai_action === 'BUY' ? 'ai-buy' : result.ai_action === 'SELL' ? 'ai-sell' : 'ai-hold';
  aiCell.textContent = result.ai_action;
  aiCell.className   = `ai-cell ${aiClass}`;
  aiCell.style.visibility = 'visible';

  // Delta cells
  const userDelta = gameState.user.netValue - gameState.user.prevNetValue;
  const aiDelta   = gameState.ai.netValue   - gameState.ai.prevNetValue;
  const isUserFlat = gameState.user.position === 'flat' && action === 'HOLD' && userDelta === 0 && gameState.user.shares === 0;
  const isAiFlat   = gameState.ai.position   === 'flat' && result.ai_action === 'HOLD' && aiDelta === 0 && gameState.ai.shares === 0;

  const userDeltaEl = document.getElementById(`row${n}-user-delta`);
  userDeltaEl.textContent = isUserFlat ? '—' : fmtSigned(userDelta);
  userDeltaEl.className   = isUserFlat ? 'pnl-cell' : `pnl-cell ${userDelta >= 0 ? 'pos' : 'neg'}`;

  const aiDeltaEl = document.getElementById(`row${n}-ai-delta`);
  aiDeltaEl.textContent = isAiFlat ? '—' : fmtSigned(aiDelta);
  aiDeltaEl.className   = isAiFlat ? 'pnl-cell' : `pnl-cell ${aiDelta >= 0 ? 'pos' : 'neg'}`;

  renderPnLCards();

  const pct = ((dayIndex + 1) / 10) * 100;
  document.getElementById('progress-fill').style.width      = `${pct}%`;
  document.getElementById('progress-label-text').textContent = `Day ${dayIndex + 1} of 10`;

  renderComplianceRow(n, result);

  if (n < 12) {
    document.getElementById('btn-next-day').disabled = false;
  } else {
    document.getElementById('btn-next-day').disabled = true;
    await endGame();
  }
}

function renderComplianceRow(n, result) {
  document.getElementById('row-compliance').style.display = '';
  const row = document.getElementById(`comp-row-${n}`);
  row.style.display = '';
  document.getElementById(`comp-date-${n}`).textContent   = gameState.gameDays[n - 3].date;
  document.getElementById(`comp-action-${n}`).textContent = result.ai_action;
  const isFlag = result.compliance_status === 'flagged';
  document.getElementById(`comp-status-${n}`).innerHTML   = `<span class="status-badge ${isFlag ? 'flag' : 'ok'}">${isFlag ? 'FLAGGED' : 'PASS'}</span>`;
  document.getElementById(`comp-rule-${n}`).textContent   = result.compliance_rule;
  document.getElementById(`comp-insight-${n}`).textContent = result.ai_insight;
}

async function endGame() {
  try { await getResult(gameState.gameId); } catch (e) { console.error('getResult error', e); }

  const userNet = gameState.user.netValue;
  const aiNet   = gameState.ai.netValue;
  const winner  = userNet > aiNet ? 'user' : aiNet > userNet ? 'ai' : 'draw';

  const badge = document.getElementById('winner-badge');
  if (winner === 'user') { badge.textContent = 'You Win!';     badge.className = 'you-win'; }
  else if (winner === 'ai') { badge.textContent = 'AI Wins';   badge.className = 'ai-wins'; }
  else                    { badge.textContent = "It's a Draw"; badge.className = 'tie'; }

  document.getElementById('winner-banner').style.display = '';
}

function resetGame() {
  const cap = 5000;
  const freshActor = () => ({ position: 'flat', cash: cap, shares: 0, entryPrice: 0, portfolio: 0, cumCosts: 0, cumTax: 0, netValue: cap, prevNetValue: cap });

  Object.assign(gameState, {
    gameId: null, instrument: 'ASML', currency: 'EUR', startingCapital: cap,
    warmupDays: [], gameDays: [], currentDayIndex: 0, nextRowToReveal: 3, started: false,
    user: freshActor(), ai: freshActor()
  });

  // Row 1
  document.getElementById('pill-asml').disabled  = false;
  document.getElementById('pill-nvidia').disabled = false;
  document.getElementById('pill-asml').classList.add('active');
  document.getElementById('pill-nvidia').classList.remove('active');
  document.getElementById('start-date').disabled = false;
  document.getElementById('end-date').disabled   = false;
  document.getElementById('btn-select-days').style.display = '';
  document.getElementById('btn-new-game').style.display    = 'none';
  document.getElementById('selection-label').style.display = 'none';
  document.getElementById('selected-instrument').textContent = '—';
  document.getElementById('selected-range-text').textContent = '—';
  document.getElementById('selected-days-count').textContent = '—';

  // Row 2
  const s = '€';
  document.getElementById('user-cash').textContent      = s + '5,000.00';
  document.getElementById('user-portfolio').textContent = s + '0.00';
  document.getElementById('user-costs').textContent     = '−' + s + '0.00';
  document.getElementById('user-tax').textContent       = '−' + s + '0.00';
  const uNet = document.getElementById('user-net');
  uNet.textContent = s + '5,000.00'; uNet.className = 'pnl-value';
  document.getElementById('ai-cash').textContent        = s + '5,000.00';
  document.getElementById('ai-portfolio').textContent   = s + '0.00';
  document.getElementById('ai-costs').textContent       = '−' + s + '0.00';
  document.getElementById('ai-tax').textContent         = '−' + s + '0.00';
  const aNet = document.getElementById('ai-net');
  aNet.textContent = s + '5,000.00'; aNet.className = 'pnl-value';
  document.getElementById('winner-banner').style.display = 'none';
  document.getElementById('winner-badge').textContent = '—';
  document.getElementById('winner-badge').className   = '';
  document.getElementById('progress-fill').style.width      = '0%';
  document.getElementById('progress-label-text').textContent = 'Day 0 of 10';
  document.getElementById('row-performance').style.display  = 'none';

  // Warmup rows
  [1, 2].forEach(n => {
    ['date', 'instrument', 'price'].forEach(f => { document.getElementById(`row${n}-${f}`).textContent = '—'; });
  });

  document.getElementById('btn-next-day').disabled = true;

  // Active rows
  for (let n = 3; n <= 12; n++) {
    const activeRow = document.getElementById(`game-row-${n}`);
    activeRow.classList.add('locked');
    activeRow.style.display = 'none';
    ['buy', 'sell', 'hold'].forEach(a => {
      const b = document.getElementById(`${a}-${n}`);
      b.disabled = true; b.classList.remove('selected'); b.onclick = null;
    });
    const aiCell = document.getElementById(`ai-cell-${n}`);
    aiCell.textContent = '—'; aiCell.className = 'ai-cell'; aiCell.style.visibility = 'hidden';
    ['date', 'instrument', 'price'].forEach(f => { document.getElementById(`row${n}-${f}`).textContent = '—'; });
    ['user-delta', 'ai-delta'].forEach(f => {
      const el = document.getElementById(`row${n}-${f}`);
      el.textContent = '—'; el.className = 'pnl-cell';
    });
    // Compliance
    document.getElementById(`comp-row-${n}`).style.display = 'none';
    ['date', 'action', 'status', 'rule', 'insight'].forEach(f => {
      document.getElementById(`comp-${f}-${n}`).textContent = '—';
    });
    document.getElementById(`comp-status-${n}`).innerHTML = '—';
  }
  document.getElementById('row-compliance').style.display = 'none';

  validateDates();
}

function initControls() {
  setEndDateMax();
  validateDates();

  document.getElementById('pill-asml').addEventListener('click', () => {
    gameState.instrument = 'ASML'; gameState.currency = 'EUR';
    document.getElementById('pill-asml').classList.add('active');
    document.getElementById('pill-nvidia').classList.remove('active');
    validateDates();
  });
  document.getElementById('pill-nvidia').addEventListener('click', () => {
    gameState.instrument = 'NVIDIA'; gameState.currency = 'USD';
    document.getElementById('pill-nvidia').classList.add('active');
    document.getElementById('pill-asml').classList.remove('active');
    validateDates();
  });

  document.getElementById('start-date').addEventListener('change', validateDates);
  document.getElementById('end-date').addEventListener('change',   validateDates);

  document.getElementById('btn-select-days').addEventListener('click', async () => {
    document.getElementById('btn-select-days').disabled = true;
    const start = document.getElementById('start-date').value;
    const end   = document.getElementById('end-date').value;
    let data;
    try {
      data = await selectDays(gameState.instrument, start, end);
    } catch (e) {
      console.error('selectDays error', e);
      document.getElementById('btn-select-days').disabled = false;
      return;
    }

    gameState.gameId          = data.game_id;
    gameState.currency        = data.currency;
    gameState.startingCapital = data.starting_capital ?? 5000;
    gameState.warmupDays      = data.warmup_days;
    gameState.gameDays        = data.game_days;
    gameState.user.cash       = gameState.startingCapital;
    gameState.user.netValue   = gameState.startingCapital;
    gameState.user.prevNetValue = gameState.startingCapital;
    gameState.ai.cash         = gameState.startingCapital;
    gameState.ai.netValue     = gameState.startingCapital;
    gameState.ai.prevNetValue = gameState.startingCapital;
    gameState.started         = true;

    lockControls();

    document.getElementById('selected-instrument').textContent = data.instrument;
    document.getElementById('selected-range-text').textContent =
      data.game_days[0].date + ' — ' + data.game_days[data.game_days.length - 1].date;
    document.getElementById('selected-days-count').textContent = '10 trading days';
    document.getElementById('selection-label').style.display   = '';

    document.getElementById('row-performance').style.display   = '';
    document.getElementById('progress-fill').style.width       = '0%';
    document.getElementById('progress-label-text').textContent = 'Day 0 of 10';
    renderPnLCards();

    gameState.nextRowToReveal = 3;
    renderWarmupRows();
    document.getElementById('btn-next-day').disabled = false;
  });

  document.getElementById('btn-new-game').addEventListener('click', resetGame);

  document.getElementById('btn-next-day').addEventListener('click', () => {
    const n = gameState.nextRowToReveal;
    if (n > 12) return;
    const row = document.getElementById(`game-row-${n}`);
    row.style.display = '';
    unlockRow(n);
    gameState.nextRowToReveal = n + 1;
    document.getElementById('btn-next-day').disabled = true;
    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
}

document.addEventListener('DOMContentLoaded', initControls);
