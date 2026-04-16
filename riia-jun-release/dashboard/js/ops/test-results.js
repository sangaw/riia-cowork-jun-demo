// ── Test Results ───────────────────────────────────────────────────────────
import { apiFetch } from './api.js';
import { badge } from './utils.js';

const _RUN_CMD = `pytest tests/e2e/test_rita_scenarios.py --junitxml=test-results/junit-rita-scenarios.xml
pytest tests/e2e/test_fno_scenarios.py  --junitxml=test-results/junit-fno-scenarios.xml
pytest tests/e2e/test_ops_scenarios.py  --junitxml=test-results/junit-ops-scenarios.xml`;

export async function loadTestResults() {
  const data = await apiFetch('/api/v1/test-results');
  if (!data) {
    _showNoData('API error — could not load test results');
    return;
  }

  // No XML files generated yet — show actionable message instead of all-zeros
  if (!data.data_available) {
    _showNoData();
    return;
  }

  const suites = data.suites || [];
  let totalTests = 0, totalPassed = 0, totalFailed = 0;

  suites.forEach(suite => {
    totalTests  += suite.total  || 0;
    totalPassed += suite.passed || 0;
    totalFailed += suite.failed || 0;
  });

  document.getElementById('test-total').textContent  = totalTests;
  document.getElementById('test-passed').textContent = totalPassed;
  document.getElementById('test-failed').textContent = totalFailed;
  const rate = totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : '—';
  document.getElementById('test-rate').textContent = rate !== '—' ? rate + '%' : '—';

  const dashMap = { rita: 'rita', fno: 'fno', ops: 'ops' };
  suites.forEach(suite => {
    const key = suite.name;
    const sumEl  = document.getElementById(`${key}-summary`);
    const resEl  = document.getElementById(`${key}-results`);
    if (!sumEl || !resEl) return;

    const pct = suite.total > 0 ? ((suite.passed / suite.total) * 100).toFixed(0) : 0;
    sumEl.textContent = `${suite.passed} / ${suite.total} passed (${pct}%)`;

    const passed = suite.cases.filter(c => c.status === 'passed');
    resEl.innerHTML = passed.length === 0
      ? '<div style="font-size:11px;color:var(--t4);padding:4px 0">No passing scenarios</div>'
      : passed.map(c => `
      <div style="display:flex;align-items:center;gap:6px;padding:3px 0;font-size:11px;border-bottom:1px solid var(--border)">
        ${badge('passed', 'ok')}
        <span style="color:var(--t2);font-family:var(--fm)">${c.name}</span>
      </div>`).join('');
  });

  // Defects table
  const defects = suites.flatMap(s =>
    s.cases.filter(c => c.status !== 'passed').map(c => ({ ...c, suite: s.name }))
  );
  const defEl = document.getElementById('test-defects');
  if (defects.length === 0) {
    defEl.innerHTML = '<div class="al ok"><svg class="al-ic" width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M2.5 7l3 3 5-5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>All scenarios passing</div>';
  } else {
    defEl.innerHTML = `<table>
      <thead><tr><th>Dashboard</th><th>Scenario</th><th>Endpoint</th><th>Status</th></tr></thead>
      <tbody>${defects.map(d => `<tr>
        <td>${d.suite.toUpperCase()}</td>
        <td style="font-family:var(--fm);font-size:11px">${d.name}</td>
        <td style="font-family:var(--fm);font-size:11px;color:var(--t3)">${d.message || '—'}</td>
        <td>${badge('FAIL', 'danger')}</td>
      </tr>`).join('')}</tbody>
    </table>`;
  }
}

function _showNoData(msg) {
  const noDataHtml = `<div class="al i" style="grid-column:1/-1;padding:10px 14px">
    <svg class="al-ic" width="13" height="13" viewBox="0 0 13 13" fill="none"><circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.2"/><path d="M6.5 4v3M6.5 9h.01" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
    ${msg || 'No test results found — run the scenario tests to generate results.'}
  </div>`;

  ['test-total','test-passed','test-failed','test-rate'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = '—';
  });
  ['rita-summary','fno-summary','ops-summary'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = 'Not run yet';
  });
  ['rita-results','fno-results','ops-results'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = noDataHtml;
  });

  const defEl = document.getElementById('test-defects');
  if (defEl) {
    defEl.innerHTML = `<div style="padding:12px 0">
      <div style="font-size:12px;color:var(--t3);margin-bottom:8px">${msg || 'Run the e2e scenario tests from the project root (with the API server running):'}</div>
      <pre style="font-size:11px;font-family:var(--fm);background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:10px 14px;color:var(--text);white-space:pre-wrap">${_RUN_CMD}</pre>
    </div>`;
  }
}
