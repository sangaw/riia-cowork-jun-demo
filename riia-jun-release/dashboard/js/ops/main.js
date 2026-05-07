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
import { loadAgentBuilds } from './agent-builds.js';

// ── Populate section loader registry ─────────────────────────────────────────
sectionLoaders['overview']      = loadOverview;
sectionLoaders['monitoring']    = loadMonitoring;
sectionLoaders['cicd']          = loadCICD;
sectionLoaders['test']          = loadTestResults;
sectionLoaders['deploy']        = loadDeploy;
sectionLoaders['observability'] = loadObservability;
sectionLoaders['chat']          = loadChat;
sectionLoaders['dailyops']      = () => { loadDailyOps(); loadInstruments(); };
sectionLoaders['users']         = loadUsers;
sectionLoaders['agent-builds']  = loadAgentBuilds;

// ── Window bindings for inline onclick= attributes ────────────────────────────
window.nav                = nav;
window.refreshTestResults = loadTestResults;
window.triggerSnapshot    = triggerSnapshot;
window.loadChat           = loadChat;
window.loadDailyOps       = loadDailyOps;
window.toggleInstrument   = toggleInstrument;
window.saveInstruments    = saveInstruments;
window.loadUsers          = loadUsers;
window.saveUserRoles      = saveUserRoles;
window.loadAgentBuilds    = loadAgentBuilds;

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadOverview();
  setInterval(refreshSidebar, 30000);
});
