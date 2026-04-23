// ── RITA Dashboard — main.js (entry point) ─────────────────
import { api } from './api.js';
import { show, warmupChat, _sectionLoaders, getCurrentSection } from './nav.js';
import { loadHealth, loadPerfSummary, loadDrift, loadProgress } from './health.js';
import { switchMsTab, loadMarketSignals, loadGoalHint } from './market-signals.js';
import { loadPerformance } from './performance.js';
import { loadTrades, downloadTradeJournal } from './trades.js';
import { loadDiagnostics } from './diagnostics.js';
import { loadExplain } from './explainability.js';
import { loadRisk } from './risk.js';
import { loadTrainProgress } from './training.js';
import { loadObservability } from './observability.js';
import { loadMcp } from './mcp.js';
import { loadExport, runGoal, runMarket, runStrategy, runFullPipeline, doReset } from './export.js';
import { loadScenarios, runScenarioBacktest, setScenarioPeriod } from './scenarios.js';
import { loadAudit } from './audit.js';
import { useChip, sendChatMsg, clearChat, updateChips, showAlerts, refreshChatChips } from './chat.js';
import { openChartModal, closeChartModal } from './chart-modal.js';

// ── Populate section loaders map ───────────────────────────
_sectionLoaders.market            = async () => { refreshChatChips(); clearChat(); const data = await warmupChat(); if (data) { updateChips(data.chips); showAlerts(data.alerts); } };
_sectionLoaders['market-signals'] = loadMarketSignals;
_sectionLoaders.goal              = loadGoalHint;
_sectionLoaders.scenarios         = loadScenarios;
_sectionLoaders.performance       = loadPerformance;
_sectionLoaders.trades            = loadTrades;
_sectionLoaders.diagnostics       = loadDiagnostics;
_sectionLoaders.explain           = loadExplain;
_sectionLoaders.risk              = loadRisk;
_sectionLoaders['train-progress'] = loadTrainProgress;
_sectionLoaders.observability     = loadObservability;
_sectionLoaders.mcp               = loadMcp;
_sectionLoaders.export            = loadExport;
_sectionLoaders.audit             = loadAudit;

// ── Expose to window for inline HTML onclick attributes ────
window.show               = show;
window.selectInstrumentTab = selectInstrumentTab;
window.switchMsTab        = switchMsTab;
window.downloadTradeJournal = downloadTradeJournal;
window.runGoal            = runGoal;
window.runMarket          = runMarket;
window.runStrategy        = runStrategy;
window.runFullPipeline    = runFullPipeline;
window.doReset            = doReset;
window.setScenarioPeriod  = setScenarioPeriod;
window.runScenarioBacktest = runScenarioBacktest;
window.useChip            = useChip;
window.sendChatMsg        = sendChatMsg;
window.clearChat          = clearChat;
window.openChartModal     = openChartModal;
window.closeChartModal    = closeChartModal;
// Reload buttons for individual sections
window.loadMarketSignals  = loadMarketSignals;
window.loadGoalHint       = loadGoalHint;
window.loadPerformance    = loadPerformance;
window.loadTrades         = loadTrades;
window.loadDiagnostics    = loadDiagnostics;
window.loadExplain        = loadExplain;
window.loadRisk           = loadRisk;
window.loadTrainProgress  = loadTrainProgress;
window.loadObservability  = loadObservability;
window.loadMcp            = loadMcp;
window.loadAudit          = loadAudit;

// ── Refresh all home KPIs & active section ─────────────────
async function refresh() {
  await Promise.all([loadHealth(), loadPerfSummary(), loadDrift(), loadProgress()]);
  const current = getCurrentSection();
  if (_sectionLoaders[current]) _sectionLoaders[current]();
}

// Expose refresh so export.js can call it via window._ritaRefresh
window._ritaRefresh = refresh;

// ── Instrument tab selection (Overview) ───────────────────
function _initInstrumentTabs() {
  const saved = localStorage.getItem('ritaInstrument') || 'NIFTY';
  document.querySelectorAll('.inst-tab').forEach(t =>
    t.classList.toggle('active', t.id === 'itab-' + saved)
  );
}

async function selectInstrumentTab(id) {
  localStorage.setItem('ritaInstrument', id);
  document.querySelectorAll('.inst-tab').forEach(t =>
    t.classList.toggle('active', t.id === 'itab-' + id)
  );
  try { await api('/api/v1/instrument/select', 'POST', { instrument_id: id }).catch(() => {}); } catch (_) {}
  if (getCurrentSection() === 'market') {
    clearChat();
    const data = await warmupChat();
    if (data) { updateChips(data.chips); showAlerts(data.alerts); }
  } else {
    refreshChatChips();
  }
  await loadActiveInstrument();
  await Promise.all([loadHealth(), loadPerfSummary(), loadDrift(), loadProgress()]);
}

// ── Active instrument pill ─────────────────────────────────
async function loadActiveInstrument() {
  try {
    const inst = await api('/api/v1/instrument/active');
    if (!inst || !inst.id) return;
    const pill = document.getElementById('inst-pill');
    document.getElementById('inst-pill-flag').textContent = inst.flag || '';
    document.getElementById('inst-pill-name').textContent = inst.name || inst.id;
    document.getElementById('inst-pill-exch').textContent = inst.exchange ? `· ${inst.exchange}` : '';
    pill.style.display = 'flex';
    document.title = `RITA — ${inst.name || inst.id}`;
  } catch { /* silently skip if API not ready */ }
}

// ── Init ───────────────────────────────────────────────────
window.addEventListener('load', () => { _initInstrumentTabs(); refresh(); loadActiveInstrument(); });
