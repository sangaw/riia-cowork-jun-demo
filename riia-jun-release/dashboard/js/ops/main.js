// ── Ops Dashboard — Entry Point ───────────────────────────────────────────────
import { nav, sectionLoaders, loadSection } from './nav.js';
import { loadOverview } from './overview.js';
import { loadMonitoring } from './monitoring.js';
import { loadCICD } from './cicd.js';
import { loadDeploy } from './deploy.js';
import { loadObservability } from './observability.js';
import { loadChat } from './chat.js';
import { loadDailyOps, triggerSnapshot, loadInstruments, toggleInstrument, saveInstruments } from './daily-ops.js';
import { refreshSidebar } from './sidebar.js';
import { loadTestResults } from './test-results.js';
import { loadUsers, saveUserRoles } from './users.js';
import { loadAlerts } from './alerts.js';
import { loadSourceAvailability } from './source-availability.js';
import { loadFunctionalKPIs } from './functional-kpis.js';

// ── Populate section loader registry ─────────────────────────────────────────
sectionLoaders['overview']            = loadOverview;
sectionLoaders['monitoring']          = loadMonitoring;
sectionLoaders['cicd']               = loadCICD;
sectionLoaders['test']               = loadTestResults;
sectionLoaders['deploy']             = loadDeploy;
sectionLoaders['observability']      = loadObservability;
sectionLoaders['chat']               = loadChat;
sectionLoaders['dailyops']           = () => { loadDailyOps(); loadInstruments(); };
sectionLoaders['users']              = loadUsers;
sectionLoaders['alerts']             = loadAlerts;
sectionLoaders['source-availability'] = loadSourceAvailability;
sectionLoaders['functional-kpis']    = loadFunctionalKPIs;

// ── Window bindings for inline onclick= attributes ────────────────────────────
window.nav                      = nav;
window.refreshTestResults       = loadTestResults;
window.triggerSnapshot          = triggerSnapshot;
window.loadChat                 = loadChat;
window.loadDailyOps             = loadDailyOps;
window.toggleInstrument         = toggleInstrument;
window.saveInstruments          = saveInstruments;
window.loadUsers                = loadUsers;
window.saveUserRoles            = saveUserRoles;
window.loadAlerts               = loadAlerts;
window.loadSourceAvailability   = loadSourceAvailability;
window.loadFunctionalKPIs       = loadFunctionalKPIs;

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadOverview();
  loadAlerts();
  loadSourceAvailability();
  loadFunctionalKPIs();
  setInterval(refreshSidebar, 30000);
});
