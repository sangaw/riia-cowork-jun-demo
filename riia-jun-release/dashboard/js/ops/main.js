// ── Ops Dashboard — Entry Point ───────────────────────────────────────────────
import { nav, sectionLoaders, loadSection } from './nav.js';
import { loadOverview } from './overview.js';
import { loadMonitoring } from './monitoring.js';
import { loadCICD } from './cicd.js';
import { loadDeploy } from './deploy.js';
import { loadObservability } from './observability.js';
import { loadChat } from './chat.js';
import { loadDailyOps, triggerSnapshot } from './daily-ops.js';
import { refreshSidebar } from './sidebar.js';

// ── Populate section loader registry ─────────────────────────────────────────
sectionLoaders['overview']      = loadOverview;
sectionLoaders['monitoring']    = loadMonitoring;
sectionLoaders['cicd']          = loadCICD;
sectionLoaders['deploy']        = loadDeploy;
sectionLoaders['observability'] = loadObservability;
sectionLoaders['chat']          = loadChat;
sectionLoaders['dailyops']      = loadDailyOps;

// ── Window bindings for inline onclick= attributes ────────────────────────────
window.nav              = nav;
window.triggerSnapshot  = triggerSnapshot;
window.loadChat         = loadChat;
window.loadDailyOps     = loadDailyOps;

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadOverview();
  setInterval(refreshSidebar, 30000);
});
