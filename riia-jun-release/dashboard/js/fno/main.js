// ── FnO Dashboard — Entry Point ───────────────────────────────────────────────
import { initApp, checkStatus } from './api.js';
import { initNav, setUnderlying, setExpiry } from './nav.js';
import { filterPos } from './positions.js';
import {
  manSelectTile,
  manSwitchTab,
  manDragStart,
  manDragEnd,
  manDropToGroup,
  manDropToPool,
  manRemove,
  manSaveName,
  manToggleView,
  manSaveCsv,
  manSaveSnapshot,
} from './manoeuvre.js';

// ── Window bindings for inline onclick= attributes ────────────────────────────
// Navigation / filter
window.setUnderlying = setUnderlying;
window.setExpiry     = setExpiry;
window.filterPos     = filterPos;

// Manoeuvre
window.manSelectTile    = manSelectTile;
window.manSwitchTab     = manSwitchTab;
window.manDragStart     = manDragStart;
window.manDragEnd       = manDragEnd;
window.manDropToGroup   = manDropToGroup;
window.manDropToPool    = manDropToPool;
window.manRemove        = manRemove;
window.manSaveName      = manSaveName;
window.manToggleView    = manToggleView;
window.manSaveCsv       = manSaveCsv;
window.manSaveSnapshot  = manSaveSnapshot;

// ── Boot ──────────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  initNav();
  initApp();
  checkStatus();
  // Poll API status every 30s
  setInterval(checkStatus, 30000);
});
