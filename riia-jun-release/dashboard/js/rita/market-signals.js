// ── Market Signals ─────────────────────────────────────────
import { api } from './api.js';
import { setEl } from './utils.js';
import { mkChart, C } from './charts.js';

let _msTimeframe = 'daily';

export function switchMsTab(tf) {
  _msTimeframe = tf;
  ['daily','weekly','monthly'].forEach(t => {
    const el = document.getElementById('tab-' + t);
    if (el) el.classList.toggle('active', t === tf);
  });
  loadMarketSignals();
}

export async function loadMarketSignals() {
  const periods = _msTimeframe === 'monthly' ? 60 : _msTimeframe === 'weekly' ? 104 : 252;
  try {
    const rows = await api(`/api/v1/market-signals?timeframe=${_msTimeframe}&periods=${periods}`);
    if (!rows || !rows.length) return;

    const last = rows[rows.length - 1];
    const dates = rows.map(r => r.date);

    // ── Data range label ────────────────────────────────────
    const firstDate = rows.find(r => r.date)?.date || '—';
    setEl('ms-data-range', `Data: ${firstDate} → ${last.date || '—'} &nbsp;|&nbsp; ${rows.length} bars`);

    // ── Signal summary KPIs ─────────────────────────────────
    const rsi = parseFloat(last.rsi_14);
    setEl('ms-rsi-val', isNaN(rsi) ? '—' : rsi.toFixed(1));
    document.getElementById('ms-rsi-val').className = 'kpi-value ' + (rsi > 70 ? 'neg' : rsi < 30 ? 'pos' : 'neu');
    setEl('ms-rsi-sig', rsi > 70 ? 'Overbought' : rsi < 30 ? 'Oversold' : 'Neutral');

    const macdVal = parseFloat(last.macd);
    const sigVal  = parseFloat(last.macd_signal);
    const macdBull = macdVal > sigVal;
    setEl('ms-macd-val', isNaN(macdVal) ? '—' : macdVal.toFixed(2));
    document.getElementById('ms-macd-val').className = 'kpi-value ' + (macdBull ? 'pos' : 'neg');
    setEl('ms-macd-sig', macdBull ? 'Bullish crossover' : 'Bearish crossover');

    const bbPct = parseFloat(last.bb_pct_b);
    setEl('ms-bb-val', isNaN(bbPct) ? '—' : bbPct.toFixed(2));
    document.getElementById('ms-bb-val').className = 'kpi-value ' + (bbPct > 0.8 ? 'neg' : bbPct < 0.2 ? 'pos' : 'neu');
    setEl('ms-bb-sig', bbPct > 0.8 ? 'Near upper band' : bbPct < 0.2 ? 'Near lower band' : 'Mid-band');

    const price  = parseFloat(last.Close);
    const ema5   = parseFloat(last.ema_5);
    const ema13  = parseFloat(last.ema_13);
    const ema26  = parseFloat(last.ema_26);
    const abv5   = price > ema5;
    const abv13  = price > ema13;
    const abv26  = price > ema26;
    setEl('ms-ema5-val',  isNaN(ema5)  ? '—' : ema5.toFixed(0));
    document.getElementById('ms-ema5-val').className  = 'kpi-value ' + (abv5  ? 'pos' : 'neg');
    setEl('ms-ema5-sig',  abv5  ? 'Above EMA5'  : 'Below EMA5');
    setEl('ms-ema13-val', isNaN(ema13) ? '—' : ema13.toFixed(0));
    document.getElementById('ms-ema13-val').className = 'kpi-value ' + (abv13 ? 'pos' : 'neg');
    setEl('ms-ema13-sig', abv13 ? 'Above EMA13' : 'Below EMA13');
    setEl('ms-ema26-val', isNaN(ema26) ? '—' : ema26.toFixed(0));
    document.getElementById('ms-ema26-val').className = 'kpi-value ' + (abv26 ? 'pos' : 'neg');
    setEl('ms-ema26-sig', abv26 ? 'Above EMA26' : 'Below EMA26');

    // Update historical avg hint from last 252 days
    const histHint = document.getElementById('historical-avg-hint');
    if (histHint && rows.length >= 2) {
      const ret12m = ((parseFloat(last.Close) / parseFloat(rows[0].Close)) - 1) * 100;
      if (!isNaN(ret12m)) histHint.textContent = `Last ${rows.length} trading days: ${ret12m.toFixed(1)}%`;
    }

    const atrRaw  = parseFloat(last.atr_14);
    const atrPct  = (!isNaN(atrRaw) && price) ? (atrRaw / price * 100) : NaN;
    setEl('ms-atr-val', isNaN(atrPct) ? '—' : atrPct.toFixed(2) + '%');
    document.getElementById('ms-atr-val').className = 'kpi-value ' + (atrPct > 1.5 ? 'neg' : atrPct < 0.8 ? 'pos' : 'neu');
    setEl('ms-atr-sig', atrPct > 1.5 ? 'High volatility' : atrPct < 0.8 ? 'Compressed' : 'Normal range');

    const trendVal = parseFloat(last.trend_score);
    setEl('ms-trend-val', isNaN(trendVal) ? '—' : trendVal.toFixed(2));
    document.getElementById('ms-trend-val').className = 'kpi-value ' + (trendVal > 0.2 ? 'pos' : trendVal < -0.2 ? 'neg' : 'neu');
    setEl('ms-trend-sig', trendVal > 0.5 ? 'Strong uptrend' : trendVal > 0.2 ? 'Mild uptrend' : trendVal < -0.5 ? 'Strong downtrend' : trendVal < -0.2 ? 'Mild downtrend' : 'Sideways');

    // ── Price + Volume chart ────────────────────────────────
    mkChart('chart-ms-pv', {
      type: 'bar',
      data: {
        labels: dates,
        datasets: [
          { type: 'line', label: 'Close', data: rows.map(r => r.Close),
            borderColor: C.run, backgroundColor: 'transparent',
            pointRadius: 0, borderWidth: 2, yAxisID: 'yPrice', order: 1 },
          { type: 'bar', label: 'Volume', data: rows.map(r => r.Volume),
            backgroundColor: 'rgba(0,86,184,0.18)', borderWidth: 0,
            yAxisID: 'yVol', order: 2 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { size: 11 } } } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { family: C.mono, size: 10 } } },
          yPrice: { position: 'left',  grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(0), font: { family: C.mono, size: 10 } } },
          yVol:   { position: 'right', grid: { display: false }, ticks: { callback: v => v >= 1e7 ? (v/1e7).toFixed(0)+'Cr' : v >= 1e5 ? (v/1e5).toFixed(0)+'L' : v, font: { family: C.mono, size: 10 } } },
        }
      }
    });

    // ── RSI chart ───────────────────────────────────────────
    mkChart('chart-ms-rsi', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'RSI-14', data: rows.map(r => r.rsi_14), borderColor: C.run, backgroundColor: 'rgba(0,86,184,0.06)', fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          annotation: { annotations: {
            ob:  { type: 'line', yMin: 70, yMax: 70, borderColor: C.danger,          borderWidth: 1,   borderDash: [4,3] },
            obz: { type: 'line', yMin: 60, yMax: 60, borderColor: 'rgba(180,40,40,0.4)', borderWidth: 1, borderDash: [2,4] },
            os:  { type: 'line', yMin: 30, yMax: 30, borderColor: C.build,           borderWidth: 1,   borderDash: [4,3] },
            osz: { type: 'line', yMin: 40, yMax: 40, borderColor: 'rgba(26,107,60,0.4)', borderWidth: 1, borderDash: [2,4] },
          }}
        },
        scales: {
          x: { grid: { color: 'rgba(0,0,0,.03)' }, ticks: { maxTicksLimit: 8, font: { family: C.mono, size: 10 } } },
          y: { min: 0, max: 100, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v, font: { family: C.mono, size: 10 } } }
        }
      }
    });

    // ── MACD chart ──────────────────────────────────────────
    const macdHist = rows.map(r => r.macd_hist);
    mkChart('chart-ms-macd', {
      type: 'bar',
      data: {
        labels: dates,
        datasets: [
          { type: 'line', label: 'MACD',   data: rows.map(r => r.macd),        borderColor: C.run,   backgroundColor: 'transparent', pointRadius: 0, borderWidth: 1.5, order: 1 },
          { type: 'line', label: 'Signal', data: rows.map(r => r.macd_signal), borderColor: C.warn,  backgroundColor: 'transparent', pointRadius: 0, borderWidth: 1.5, borderDash: [3,2], order: 2 },
          { type: 'bar',  label: 'Hist',   data: macdHist,
            backgroundColor: macdHist.map(v => (v || 0) >= 0 ? 'rgba(26,107,60,0.55)' : 'rgba(155,28,28,0.55)'),
            borderWidth: 0, order: 3 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { size: 11 } } } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { family: C.mono, size: 10 } } },
          y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(1), font: { family: C.mono, size: 10 } } }
        }
      }
    });

    // ── Bollinger Bands chart ───────────────────────────────
    mkChart('chart-ms-bb', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'Upper',  data: rows.map(r => r.bb_upper),  borderColor: 'rgba(146,72,10,0.4)',  backgroundColor: 'rgba(146,72,10,0.04)', fill: '+1', pointRadius: 0, borderWidth: 1, borderDash: [3,2] },
          { label: 'Close',  data: rows.map(r => r.Close),     borderColor: C.run,                  backgroundColor: 'rgba(0,86,184,0.06)',  fill: false, pointRadius: 0, borderWidth: 2 },
          { label: 'Lower',  data: rows.map(r => r.bb_lower),  borderColor: 'rgba(146,72,10,0.4)',  backgroundColor: 'rgba(146,72,10,0.04)', fill: '-1', pointRadius: 0, borderWidth: 1, borderDash: [3,2] },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { size: 11 } } } },
        scales: {
          x: { grid: { color: 'rgba(0,0,0,.03)' }, ticks: { maxTicksLimit: 8, font: { family: C.mono, size: 10 } } },
          y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(0), font: { family: C.mono, size: 10 } } }
        }
      }
    });

    // ── EMA crossover signals (EMA5 vs EMA13) ──────────────
    const n = rows.length;
    const crossUp   = new Array(n).fill(null);
    const crossDown = new Array(n).fill(null);
    let lastCrossDir = null, lastCrossIdx = -1;
    for (let i = 1; i < n; i++) {
      const p = rows[i-1], c = rows[i];
      if (p.ema_5 != null && p.ema_13 != null && c.ema_5 != null && c.ema_13 != null) {
        if (p.ema_5 <= p.ema_13 && c.ema_5 > c.ema_13) {
          crossUp[i] = (c.ema_5 + c.ema_13) / 2;
          lastCrossDir = 'up'; lastCrossIdx = i;
        } else if (p.ema_5 >= p.ema_13 && c.ema_5 < c.ema_13) {
          crossDown[i] = (c.ema_5 + c.ema_13) / 2;
          lastCrossDir = 'down'; lastCrossIdx = i;
        }
      }
    }

    // ── EMA chart ───────────────────────────────────────────
    mkChart('chart-ms-ema', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'Close',      data: rows.map(r => r.Close),  borderColor: 'rgba(100,181,246,0.7)', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 1.5, borderDash: [3,3] },
          { label: 'EMA 5',      data: rows.map(r => r.ema_5),  borderColor: '#9C27B0',              backgroundColor: 'transparent', pointRadius: 0, borderWidth: 1.2, borderDash: [2,2] },
          { label: 'EMA 13',     data: rows.map(r => r.ema_13), borderColor: C.build,                backgroundColor: 'transparent', pointRadius: 0, borderWidth: 1.2, borderDash: [4,2] },
          { label: 'EMA 26',     data: rows.map(r => r.ema_26), borderColor: 'rgba(0,150,136,0.85)', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 1.5, borderDash: [4,3] },
          { label: 'EMA 50',     data: rows.map(r => r.ema_50), borderColor: C.warn,                 backgroundColor: 'transparent', pointRadius: 0, borderWidth: 1.5, borderDash: [6,3] },
          { label: '▲ Bull X',   data: crossUp,   type: 'line', showLine: false, spanGaps: false,
            pointStyle: 'triangle', pointRadius: 5, rotation: 0,
            borderColor: '#1a6b3c', backgroundColor: '#1a6b3c', pointBorderColor: '#1a6b3c', pointBackgroundColor: '#1a6b3c' },
          { label: '▼ Bear X',   data: crossDown, type: 'line', showLine: false, spanGaps: false,
            pointStyle: 'triangle', pointRadius: 5, rotation: 180,
            borderColor: '#9b1c1c', backgroundColor: '#9b1c1c', pointBorderColor: '#9b1c1c', pointBackgroundColor: '#9b1c1c' },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { size: 11 }, boxWidth: 20 } } },
        scales: {
          x: { grid: { color: 'rgba(0,0,0,.03)' }, ticks: { maxTicksLimit: 8, font: { family: C.mono, size: 10 } } },
          y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(0), font: { family: C.mono, size: 10 } } }
        }
      }
    });

    // ── ATR% chart ──────────────────────────────────────────
    const atrPctData = rows.map(r => {
      const a = parseFloat(r.atr_14), c = parseFloat(r.Close);
      return (!isNaN(a) && !isNaN(c) && c) ? +(a / c * 100).toFixed(3) : null;
    });
    mkChart('chart-ms-atr', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'ATR%', data: atrPctData,
            borderColor: C.warn, backgroundColor: 'rgba(146,72,10,0.07)',
            fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          annotation: { annotations: {
            hiLine: { type: 'line', yMin: 1.5, yMax: 1.5, borderColor: 'rgba(155,28,28,0.55)', borderWidth: 1, borderDash: [4,3] },
            loLine: { type: 'line', yMin: 0.8, yMax: 0.8, borderColor: 'rgba(26,107,60,0.45)',  borderWidth: 1, borderDash: [4,3] },
          }}
        },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { family: C.mono, size: 10 } } },
          y: { grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(1)+'%', font: { family: C.mono, size: 10 } } }
        }
      }
    });

    // ── Trend Score chart ────────────────────────────────────
    const trendData = rows.map(r => r.trend_score != null ? +parseFloat(r.trend_score).toFixed(3) : null);
    mkChart('chart-ms-trend', {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          { label: 'Trend Score', data: trendData,
            borderColor: C.mon, backgroundColor: 'rgba(107,47,160,0.07)',
            fill: 'origin', tension: 0.25, pointRadius: 0, borderWidth: 2 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          annotation: { annotations: {
            zero:  { type: 'line', yMin: 0,    yMax: 0,    borderColor: 'rgba(0,0,0,0.3)',           borderWidth: 1.5 },
            upMid: { type: 'line', yMin: 0.2,  yMax: 0.2,  borderColor: 'rgba(26,107,60,0.35)',      borderWidth: 1, borderDash: [3,3] },
            dnMid: { type: 'line', yMin: -0.2, yMax: -0.2, borderColor: 'rgba(155,28,28,0.35)',      borderWidth: 1, borderDash: [3,3] },
            upStr: { type: 'line', yMin: 0.5,  yMax: 0.5,  borderColor: 'rgba(26,107,60,0.6)',       borderWidth: 1, borderDash: [4,3] },
            dnStr: { type: 'line', yMin: -0.5, yMax: -0.5, borderColor: 'rgba(155,28,28,0.6)',       borderWidth: 1, borderDash: [4,3] },
          }}
        },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { family: C.mono, size: 10 } } },
          y: { min: -1, max: 1, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { callback: v => v.toFixed(1), font: { family: C.mono, size: 10 } } }
        }
      }
    });

    // ── Alerts strip ────────────────────────────────────────
    const alerts = [];
    const mkAlert = (cls, txt) => `<span class="badge ${cls}" style="font-size:11px;padding:4px 10px">${txt}</span>`;

    // RSI
    if      (rsi > 70)       alerts.push(mkAlert('err',  `RSI Overbought ${rsi.toFixed(1)}`));
    else if (rsi > 60)       alerts.push(mkAlert('warn', `RSI Approaching OB ${rsi.toFixed(1)}`));
    else if (rsi < 30)       alerts.push(mkAlert('ok',   `RSI Oversold ${rsi.toFixed(1)}`));
    else if (rsi < 40)       alerts.push(mkAlert('warn', `RSI Approaching OS ${rsi.toFixed(1)}`));

    // MACD
    if      (macdBull)       alerts.push(mkAlert('ok',  'MACD Bullish Cross'));
    else                     alerts.push(mkAlert('err', 'MACD Bearish Cross'));

    // BB
    if      (bbPct > 0.8)    alerts.push(mkAlert('err',  `BB Near Upper Band ${bbPct.toFixed(2)}`));
    else if (bbPct < 0.2)    alerts.push(mkAlert('ok',   `BB Near Lower Band ${bbPct.toFixed(2)}`));

    // EMA 5 vs EMA 13 current state
    const curEma5 = parseFloat(last.ema_5), curEma13 = parseFloat(last.ema_13);
    if (!isNaN(curEma5) && !isNaN(curEma13)) {
      if   (curEma5 > curEma13) alerts.push(mkAlert('ok',  'EMA5 > EMA13 Bullish'));
      else                      alerts.push(mkAlert('err', 'EMA5 < EMA13 Bearish'));
    }

    // Recent crossover (within last 5 bars)
    if (lastCrossIdx >= 0 && (n - 1 - lastCrossIdx) <= 5) {
      const ago = n - 1 - lastCrossIdx;
      const label = ago === 0 ? 'today' : `${ago}d ago`;
      if (lastCrossDir === 'up')   alerts.push(mkAlert('ok',  `Fresh Bull Cross EMA5×EMA13 (${label})`));
      else                         alerts.push(mkAlert('err', `Fresh Bear Cross EMA5×EMA13 (${label})`));
    }

    // Price vs EMA26 trend
    if (!isNaN(ema26)) {
      if   (price > ema26) alerts.push(mkAlert('ok',  `Price > EMA26 Uptrend`));
      else                 alerts.push(mkAlert('err', `Price < EMA26 Downtrend`));
    }

    // ATR%
    if (!isNaN(atrPct)) {
      if      (atrPct > 1.5) alerts.push(mkAlert('err',  `ATR High Volatility ${atrPct.toFixed(2)}%`));
      else if (atrPct < 0.8) alerts.push(mkAlert('ok',   `ATR Compressed ${atrPct.toFixed(2)}%`));
    }

    // Trend Score
    if (!isNaN(trendVal)) {
      if      (trendVal >  0.5) alerts.push(mkAlert('ok',  `Trend Strong Uptrend ${trendVal.toFixed(2)}`));
      else if (trendVal >  0.2) alerts.push(mkAlert('ok',  `Trend Mild Uptrend ${trendVal.toFixed(2)}`));
      else if (trendVal < -0.5) alerts.push(mkAlert('err', `Trend Strong Downtrend ${trendVal.toFixed(2)}`));
      else if (trendVal < -0.2) alerts.push(mkAlert('err', `Trend Mild Downtrend ${trendVal.toFixed(2)}`));
      else                      alerts.push(mkAlert('neu', `Trend Sideways ${trendVal.toFixed(2)}`));
    }

    document.getElementById('ms-alerts').innerHTML = alerts.length
      ? alerts.join('')
      : mkAlert('neu', 'No significant signals');

  } catch (e) {
    console.warn('market signals error', e);
    setEl('ms-loading', `<div class="empty" style="color:var(--danger)">Error: ${e.message}</div>`);
    document.getElementById('ms-loading').style.display = '';
  }
}
