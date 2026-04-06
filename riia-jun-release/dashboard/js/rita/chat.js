// ── Chat ───────────────────────────────────────────────────
let _chatConfs = [], _chatLats = [];

// Wire up textarea: auto-resize + Enter to send
(function () {
  const ta = document.getElementById('chat-ta');
  if (!ta) return;
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 80) + 'px';
  });
  ta.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMsg(); }
  });
})();

export function useChip(btn) {
  const ta = document.getElementById('chat-ta');
  if (!ta) return;
  ta.value = btn.textContent.trim();
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 80) + 'px';
  ta.focus();
  sendChatMsg();
}

export async function sendChatMsg() {
  const ta = document.getElementById('chat-ta');
  const sendBtn = document.getElementById('chat-send');
  const query = (ta.value || '').trim();
  if (!query) return;

  ta.value = '';
  ta.style.height = 'auto';
  sendBtn.disabled = true;

  appendChatMsg('user', query);
  const tid = appendTyping();

  const t0 = Date.now();
  try {
    const resp = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, portfolio_inr: 1000000 })
    });
    if (!resp.ok) throw new Error('API error ' + resp.status);
    const data = await resp.json();
    removeTyping(tid);
    appendRitaMsg(data, Date.now() - t0);
    updateChatStats(data.confidence, data.latency_ms ?? (Date.now() - t0));
  } catch (e) {
    removeTyping(tid);
    appendChatError('Could not reach RITA API. Make sure the server is running.');
  } finally {
    sendBtn.disabled = false;
    ta.focus();
  }
}

function appendChatMsg(role, text) {
  const box = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'cmsg ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'cbubble';
  bubble.textContent = text;
  div.appendChild(bubble);
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function appendTyping() {
  const box = document.getElementById('chat-messages');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.className = 'cmsg rita';
  div.id = id;
  div.innerHTML = '<div class="cbubble"><span class="tdot"></span><span class="tdot"></span><span class="tdot"></span></div>';
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendRitaMsg(data, elapsed) {
  const box = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'cmsg rita';

  const conf = typeof data.confidence === 'number' ? data.confidence : null;
  const lat = data.latency_ms ?? elapsed;
  const confPct = conf !== null ? Math.round(conf * 100) + '%' : '—';
  const confCls = conf === null ? '' : conf >= 0.6 ? 'pos' : conf >= 0.42 ? 'neu' : 'neg';
  const intent = (data.intent || '').replace(/_/g, ' ');

  div.innerHTML = `
    <div class="cbubble">${chatMd(escChatHtml(data.response || '(no response)'))}</div>
    <div style="display:flex;gap:8px;align-items:center;margin-top:3px;flex-wrap:wrap">
      ${intent ? `<span style="font-family:var(--fm);font-size:9px;text-transform:uppercase;letter-spacing:.05em;color:var(--t3);background:var(--surface2);border:1px solid var(--border);border-radius:3px;padding:1px 5px">${escChatHtml(intent)}</span>` : ''}
      ${conf !== null ? `<span style="font-family:var(--fm);font-size:9px;color:var(--${confCls === 'pos' ? 'build' : confCls === 'neu' ? 'run' : confCls === 'neg' ? 'danger' : 't3'})">${confPct} conf</span>` : ''}
      ${lat ? `<span style="font-family:var(--fm);font-size:9px;color:var(--t4)">${lat}ms</span>` : ''}
    </div>`;

  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function appendChatError(msg) {
  const box = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'cmsg rita';
  div.innerHTML = `<div class="cbubble" style="background:var(--danger-bg);border-color:var(--danger-bd);color:var(--danger)">${escChatHtml(msg)}</div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function escChatHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function chatMd(s) {
  // Basic markdown: **bold**, *italic*, newlines
  return s
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

export function clearChat() {
  const box = document.getElementById('chat-messages');
  box.innerHTML = '<div class="cmsg rita"><div class="cbubble">Hi! Ask me anything about Nifty investment — market sentiment, return estimates, allocation advice, or stress scenarios.</div></div>';
  _chatConfs = []; _chatLats = [];
  const qEl = document.getElementById('cs-count');
  const cEl = document.getElementById('cs-conf');
  const lEl = document.getElementById('cs-lat');
  if (qEl) qEl.textContent = '0';
  if (cEl) cEl.textContent = '—';
  if (lEl) lEl.textContent = '—';
}

function updateChatStats(conf, lat) {
  if (conf != null) _chatConfs.push(conf);
  if (lat != null) _chatLats.push(lat);
  const n = _chatConfs.length;
  const avgConf = n > 0 ? (_chatConfs.reduce((a, b) => a + b, 0) / n * 100).toFixed(0) + '%' : '—';
  const avgLat = _chatLats.length > 0 ? Math.round(_chatLats.reduce((a, b) => a + b, 0) / _chatLats.length) + 'ms' : '—';
  const qEl = document.getElementById('cs-count');
  const cEl = document.getElementById('cs-conf');
  const lEl = document.getElementById('cs-lat');
  if (qEl) qEl.textContent = n;
  if (cEl) cEl.textContent = avgConf;
  if (lEl) lEl.textContent = avgLat;
}
