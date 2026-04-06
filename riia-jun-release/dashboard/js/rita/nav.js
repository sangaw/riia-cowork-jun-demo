// ── Navigation ─────────────────────────────────────────────
// API base — empty string means relative paths (same origin)
const API = '';

export let _currentSection = 'home';
export let _mcpPollTimer = null;
let _chatWarmedUp = false;

export function warmupChat() {
  if (_chatWarmedUp) return;
  _chatWarmedUp = true;
  fetch(`${API}/api/v1/chat/warmup`, { method: 'POST' }).catch(() => {});
}

// Section loaders map — populated by main.js after all modules are imported
export const _sectionLoaders = {};

export function show(name, navEl) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const sec = document.getElementById('sec-' + name);
  if (sec) sec.classList.add('active');
  if (navEl) navEl.classList.add('active');
  _currentSection = name;
  if (_sectionLoaders[name]) requestAnimationFrame(() => _sectionLoaders[name]());

  // Auto-refresh MCP Calls page every 10s while active; stop when leaving
  clearInterval(_mcpPollTimer);
  if (name === 'mcp') {
    _mcpPollTimer = setInterval(_sectionLoaders['mcp'], 10000);
  }
}

export function getCurrentSection() {
  return _currentSection;
}
