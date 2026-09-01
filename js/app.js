/*
 * app.js — NadiSense application shell
 * ------------------------------------
 * View state machine (onboard -> capture -> analyzing -> result),
 * capture engine (camera PPG or synthetic demo source), live waveform
 * rendering, on-device classification, result dashboard, offline
 * logbook and printable report.
 *
 * Built for the TECHNOVA 2026 demo: everything runs from a single
 * folder with zero build step and zero network calls.
 */

(() => {
  'use strict';

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));

  const app = {
    lang: 'en',
    mode: null,            // 'camera' | 'sim'
    running: false,
    buffer: [],            // {t, v} unified timeline (camera or sim)
    t0: 0,
    lastHrTick: 0,
    simSeed: 7,
    result: null,
    answers: { q1: null, q2: null },
    qIndex: 0,
  };

  /* ------------------------------------------------------------------ */
  /* VIEW SWITCHING                                                     */
  /* ------------------------------------------------------------------ */
  function show(view) {
    $$('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + view));
    window.scrollTo(0, 0);
  }

  /* ------------------------------------------------------------------ */
  /* SOURCES                                                            */
  /* ------------------------------------------------------------------ */
  const sources = {
    cam: null,
    simData: null,

    async startCamera(videoEl) {
      sources.cam = new PpgCamera.Source();
      await sources.cam.start(videoEl);
    },
    startSim() {
      const rec = Simulator.generate($('#sim-kind').value, app.simSeed);
      sources.simData = rec.signal;
      return rec;
    },
    /* Return {t,v} window samples between t0 and t0+secs (uniform 30 Hz). */
    window: (t0, secs) => {
      if (app.mode === 'camera' && sources.cam) {
        // read() already resamples the queue; trim to the requested span
        const full = sources.cam.read(secs + 1);
        return full.slice(0, Math.floor(secs * 30));
      }
      // simulator: pre-generated 30 s signal
      const n = Math.floor(secs * 30);
      const out = new Float64Array(n);
      const start = Math.floor(t0 * 30);
      for (let i = 0; i < n; i++) {
        const idx = start + i;
        out[i] = idx >= 0 && idx < sources.simData.length ? sources.simData[idx] : 0;
      }
      return out;
    },
  };

  /* ------------------------------------------------------------------ */
  /* CAPTURE ENGINE (unified rAF loop)                                  */
  /* ------------------------------------------------------------------ */
  const waveCtx = { t: 0 };

  function currentTime() {
    return sources.simData !== null && app.mode === 'sim'
      ? (performance.now() - app.t0) / 1000 : 0;
  }

  function captureLoop(now) {
    if (!app.running) return;
    const t = (now - app.t0) / 1000;

    if (app.mode === 'sim') {
      // synthetic source: emit samples as wall-clock time advances
      const sim = sources.simData;
      const idx = Math.floor(t * 30);
      while (app.simCursor <= idx && app.simCursor < sim.length) {
        app.buffer.push({ t: app.simCursor / 30, v: sim[app.simCursor] });
        app.simCursor++;
      }
    } else if (sources.cam) {
      // camera source: drain the worker queue
      const q = sources.cam.queue;
      if (q.length) {
        const lastT = q[q.length - 1].t;
        // push only newer samples than the last one we've emitted
        while (q.length && q[0].t <= (app.buffer.length ? app.buffer[app.buffer.length - 1].t : -1)) q.shift();
        for (const s of q) app.buffer.push(s);
        q.length = 0;
        waveCtx.t = lastT;
      }
    }

    drawWave();
    updateQuality();
    updateLiveHr();

    const elapsed = app.mode === 'sim'
      ? (app.simCursor / 30)
      : (app.buffer.length ? app.buffer[app.buffer.length - 1].t : 0);
    updateTimer(elapsed);

    if (elapsed >= 30) { stopCapture(); return; }
    requestAnimationFrame(captureLoop);
  }

  /* ------------------------------------------------------------------ */
  /* LIVE WAVEFORM + METERS                                             */
  /* ------------------------------------------------------------------ */
  const waveCanvas = null;

  function drawWave() {
    const c = $('#wave');
    const ctx = c.getContext('2d');
    const W = c.width = c.clientWidth * devicePixelRatio;
    const H = c.height = c.clientHeight * devicePixelRatio;
    ctx.clearRect(0, 0, W, H);

    const span = 12; // seconds shown
    const now = app.mode === 'sim'
      ? (app.simCursor / 30)
      : (app.buffer.length ? app.buffer[app.buffer.length - 1].t : 0);
    if (now < 0.5) { drawCenter(ctx, W, H); return; }

    const t0 = Math.max(0, now - span);
    const sig = sources.window(t0, Math.min(span, now - t0 + 0.001));
    if (!sig || sig.length < 8) { drawCenter(ctx, W, H); return; }

    const bp = DSP.bandpass(sig, 0.6, 3.5, 30);
    let mn = 1e9, mx = -1e9;
    for (const v of bp) { if (v < mn) mn = v; if (v > mx) mx = v; }
    const rng = Math.max(mx - mn, 1e-6);

    ctx.strokeStyle = '#2dd4bf';
    ctx.lineWidth = Math.max(1.5, W / 900);
    ctx.beginPath();
    const n = bp.length;
    for (let i = 0; i < n; i++) {
      const x = (i / Math.max(n - 1, 1)) * W;
      const y = H * 0.5 - ((bp[i] - mn) / rng - 0.5) * H * 0.82;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();

    // right-edge time marker
    ctx.fillStyle = 'rgba(148,163,184,.8)';
    ctx.font = `${Math.max(10, W / 60)}px system-ui`;
    ctx.fillText(`${now.toFixed(0)}s`, W - 52, 20);
  }

  function drawCenter(ctx, W, H) {
    ctx.strokeStyle = 'rgba(148,163,184,.4)';
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 6]);
    ctx.beginPath(); ctx.moveTo(0, H / 2); ctx.lineTo(W, H / 2); ctx.stroke();
    ctx.setLineDash([]);
  }

  function updateQuality() {
    const now = app.mode === 'sim'
      ? (app.simCursor / 30)
      : (app.buffer.length ? app.buffer[app.buffer.length - 1].t : 0);
    if (now < 4) return;
    const sig = sources.window(Math.max(0, now - 8), Math.min(8, now));
    if (!sig || sig.length < 64) return;
    const det = DSP.detrend(sig);
    const bp = DSP.bandpass(det, 0.6, 3.5, 30);
    const pks = DSP.detectPeaks(bp);
    const qrr = []; for (let i = 1; i < pks.length; i++) qrr.push((pks[i] - pks[i - 1]) / 30);
    const q = DSP.qualityIndex(bp, det, qrr);
    const bar = $('#quality-bar');
    bar.style.width = `${Math.round(q * 100)}%`;
    bar.style.background = q > 0.6 ? '#22c55e' : q > 0.35 ? '#f59e0b' : '#ef4444';
    $('#quality-txt').textContent = `${Math.round(q * 100)}%`;
  }

  function updateLiveHr() {
    const now = app.mode === 'sim'
      ? (app.simCursor / 30)
      : (app.buffer.length ? app.buffer[app.buffer.length - 1].t : 0);
    if (now - app.lastHrTick < 1.5) return;
    app.lastHrTick = now;
    if (now < 6) return;
    const sig = sources.window(Math.max(0, now - 10), 10);
    if (!sig || sig.length < 60) return;
    const bp = DSP.bandpass(sig, 0.6, 3.5, 30);
    const pks = DSP.detectPeaks(bp);
    if (pks.length >= 4) {
      const rr = [];
      for (let i = 1; i < pks.length; i++) rr.push((pks[i] - pks[i - 1]) / 30);
      const med = rr.slice().sort((a, b) => a - b)[rr.length >> 1];
      $('#live-hr').textContent = Math.round(60 / med);
    }
  }

  function updateTimer(elapsed) {
    const left = Math.max(0, 30 - elapsed);
    const bar = $('#time-bar');
    bar.style.width = `${(elapsed / 30) * 100}%`;
    $('#time-txt').textContent = `${left.toFixed(0)}s`;
  }

  /* ------------------------------------------------------------------ */
  /* FLOW CONTROL                                                       */
  /* ------------------------------------------------------------------ */
  async function startCapture(mode) {
    app.mode = mode;
    app.buffer = [];
    app.simCursor = 0;
    app.answers = { q1: null, q2: null };
    app.qIndex = 0;
    show('capture');
    $('#cam-feed').classList.toggle('hidden', mode !== 'camera');
    $('#sim-panel').classList.toggle('hidden', mode !== 'sim');
    $('#capture-state').textContent = mode === 'camera' ? I18N.t('usingCam') : I18N.t('usingSim');

    try {
      if (mode === 'camera') {
        await sources.startCamera($('#cam-video'));
      } else {
        sources.startSim();
      }
      $('#wave').classList.remove('hidden');
      $('#quality-box').classList.remove('hidden');
      app.running = true;
      app.t0 = performance.now();
      app.lastHrTick = 0;                 // reset live-HR so old sessions don't leak
      $('#live-hr').textContent = '\u2014';
      requestAnimationFrame(captureLoop);
      $('#capture-actions').classList.remove('hidden');
      $('#cam-btn-row').classList.add('hidden');
    } catch (e) {
      alert(I18N.t('camDenied'));
      show('onboard');
    }
  }

  function stopCapture() {
    app.running = false;
    if (sources.cam) { sources.cam.stop(); sources.cam = null; }
    analyze();
  }

  /* ------------------------------------------------------------------ */
  /* ANALYSIS                                                           */
  /* ------------------------------------------------------------------ */
  function analyze() {
    show('analyzing');
    $('#analyzing').textContent = I18N.t('analyzing');

    const now = app.mode === 'sim'
      ? (app.simCursor / 30)
      : (app.buffer.length ? app.buffer[app.buffer.length - 1].t : 0);
    const t0 = Math.max(0, now - 30);
    const sig = sources.window(t0, Math.min(30, now - t0 + 0.001));
    const ft = DSP.features(sig);
    const det = ft ? DSP.detrend(sig) : null;
    const bp = ft ? DSP.bandpass(det, 0.6, 3.5, 30) : null;
    const quality = ft ? DSP.qualityIndex(bp, det, ft.rr) : 0;
    const res = Classifier.assess(ft, quality);
    app.result = Object.assign({}, res, {
      features: ft, quality, waveform: sig || new Float64Array(0), t0, now,
      ts: Date.now(), mode: app.mode, answers: Object.assign({}, app.answers),
    });

    // staged reveal (the compute really is instant — this just narrates it)
    const steps = ['stQuality', 'stBeats', 'stFeatures', 'stClassify'];
    steps.forEach((k, i) => setTimeout(() => {
      const el = $(`#step-${i}`);
      el.classList.add('done');
      el.querySelector('span').textContent = I18N.t(k);
      el.querySelector('.chk').textContent = '✓';
      if (i === steps.length - 1) setTimeout(showResult, 420);
    }, 240 * (i + 1)));
  }

  /* ------------------------------------------------------------------ */
  /* RESULTS                                                            */
  /* ------------------------------------------------------------------ */
  function showResult() {
    show('result');
    const r = app.result;
    const level = r.level;
    const lvlColors = { low: '#22c55e', mid: '#f59e0b', high: '#ef4444', error: '#64748b' };
    const color = lvlColors[level] || lvlColors.low;

    if (level === 'error' || !r.features) {
      $('#result-error').classList.remove('hidden');
      $('#result-dash').classList.add('hidden');
      $('#btn-new').classList.remove('hidden');
      return;
    }

    $('#result-error').classList.add('hidden');
    $('#result-dash').classList.remove('hidden');

    // gauge
    const p = r.p;
    const angle = -90 + 180 * p;
    const needle = $('#gauge-needle');
    needle.setAttribute('transform', `rotate(${angle} 100 100)`);
    needle.style.transition = 'transform 1.2s cubic-bezier(.2,.8,.2,1)';
    $('#p-value').textContent = `${(p * 100).toFixed(0)}%`;
    $('#p-label').textContent = I18N.t('pLabel');
    $('#level-chip').textContent = I18N.t(
      level === 'low' ? 'levelLow' : level === 'mid' ? 'levelMid' : 'levelHigh');
    $('#level-chip').style.background = color;

    const levelBody = $('#level-body');
    levelBody.textContent = I18N.t(
      level === 'low' ? 'levelLowD' : level === 'mid' ? 'levelMidD' : 'levelHighD');

    // metric cards
    const f = r.features;
    const cards = [
      ['HR', `${Math.round(f.hrMean)}`, 'bpm'],
      ['SDNN', `${f.sdnn.toFixed(0)}`, 'ms'],
      ['RMSSD', `${f.rmssd.toFixed(0)}`, 'ms'],
      ['pNN50', `${f.pnn50.toFixed(0)}`, '%'],
      ['SD1/SD2', `${f.sd1sd2.toFixed(2)}`, ''],
      ['LF/HF', `${f.lf_hf.toFixed(2)}`, ''],
      ['SpecEn', `${f.s_ent.toFixed(2)}`, ''],
      ['Beats', `${f.n_beats}`, ''],
    ];
    $('#metric-grid').innerHTML = cards.map(([k, v, u]) => `
      <div class="metric"><div class="m-k">${k}</div><div class="m-v">${v}<span class="m-u">${u}</span></div></div>`).join('');

    // context notes (warnings etc.) — translated keys
    const notes = (r.notes || []).map(k => {
      const map = {
        WARN_HR_RANGE: 'Note: HR outside the 40–180 range — retake while resting.',
        WARN_SHORT: 'Note: short capture window — the retake suggestion is only for very short tests.',
        WARN_QUALITY: 'Note: low signal quality — retake in a quieter spot.',
        WARN_FEW_BEATS: 'Note: too few clean beats.',
        NOTE_ECTOPIC: 'Some ectopy-like beats present (often benign; can mimic irregularity).',
        NOTE_LOW_HRV: 'Low HRV — often stress/sleep-related; not a diagnosis.',
      };
      return `<li>${map[k] || k}</li>`;
    }).join('');
    $('#notes').innerHTML = notes ? `<ul>${notes}</ul>` : '';

    // plots
    drawTachogram(f.rr, color);
    drawPoincare(f.rr);
    drawReviewWave(r.waveform);

    // questionnaire state
    const qWrap = $('#q-answers');
    const a1 = app.answers.q1, a2 = app.answers.q2;
    qWrap.textContent = `${I18N.t('q1')} ${a1 ? (a1.yes ? I18N.t('qYes') : I18N.t('qNo')) : '—'} · ${I18N.t('q2')} ${a2 ? a2.text : '—'}`;

    saveLog(r);
    renderLogbook();
  }

  function drawTachogram(rr, color) {
    const c = $('#tachogram'); const ctx = c.getContext('2d');
    const W = c.width = c.clientWidth * devicePixelRatio;
    const H = c.height = c.clientHeight * devicePixelRatio;
    ctx.clearRect(0, 0, W, H);
    if (!rr || rr.length < 2) return;
    const max = 1.4, min = 0.3;
    const bw = W / rr.length;
    rr.forEach((v, i) => {
      const h = (v - min) / (max - min) * H * 0.86;
      ctx.fillStyle = i % 2 ? color : color + 'cc';
      ctx.globalAlpha = 0.85;
      ctx.fillRect(i * bw + 1, H - h, Math.max(bw - 2, 1), h);
    });
    ctx.globalAlpha = 1;
    ctx.strokeStyle = 'rgba(148,163,184,.5)';
    ctx.strokeRect(0.5, 0.5, W - 1, H - 1);
  }

  function drawPoincare(rr) {
    const c = $('#poincare'); const ctx = c.getContext('2d');
    const W = c.width = c.clientWidth * devicePixelRatio;
    const H = c.height = c.clientHeight * devicePixelRatio;
    ctx.clearRect(0, 0, W, H);
    if (!rr || rr.length < 3) return;
    const pts = [];
    for (let i = 0; i + 1 < rr.length; i++) pts.push([rr[i], rr[i + 1]]);
    const min = 0.3, max = 1.4;
    ctx.fillStyle = '#2dd4bf';
    ctx.globalAlpha = 0.75;
    for (const [x, y] of pts) {
      const px = (x - min) / (max - min) * (W - 12) + 6;
      const py = H - 6 - (y - min) / (max - min) * (H - 12);
      ctx.beginPath(); ctx.arc(px, py, 2.2, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  function drawReviewWave(sig) {
    const c = $('#review-wave'); const ctx = c.getContext('2d');
    const W = c.width = c.clientWidth * devicePixelRatio;
    const H = c.height = c.clientHeight * devicePixelRatio;
    ctx.clearRect(0, 0, W, H);
    if (!sig || sig.length < 16) return;
    const det = DSP.detrend(sig);
    const bp = DSP.bandpass(det, 0.6, 3.5, 30);
    let mn = 1e9, mx = -1e9;
    for (const v of bp) { if (v < mn) mn = v; if (v > mx) mx = v; }
    const rng = Math.max(mx - mn, 1e-6);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = Math.max(1.2, W / 1200);
    ctx.beginPath();
    for (let i = 0; i < bp.length; i++) {
      const x = i / (bp.length - 1) * W;
      const y = H / 2 - ((bp[i] - mn) / rng - 0.5) * H * 0.8;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    // mark detected peaks
    const pks = DSP.detectPeaks(bp);
    ctx.fillStyle = '#f472b6';
    for (const pk of pks) {
      const x = pk / (bp.length - 1) * W;
      const y = H / 2 - ((bp[pk] - mn) / rng - 0.5) * H * 0.8;
      ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();
    }
  }

  /* ------------------------------------------------------------------ */
  /* LOGBOOK (local only)                                               */
  /* ------------------------------------------------------------------ */
  function saveLog(r) {
    try {
      const log = JSON.parse(localStorage.getItem('nadi-log') || '[]');
      log.unshift({
        ts: r.ts, level: r.level, p: r.p ? Math.round(r.p * 100) : null,
        hr: r.features ? Math.round(r.features.hrMean) : null,
        sdnn: r.features ? Math.round(r.features.sdnn) : null,
        mode: r.mode,
      });
      localStorage.setItem('nadi-log', JSON.stringify(log.slice(0, 12)));
    } catch (e) { /* private mode etc. — ignore */ }
  }

  function renderLogbook() {
    try {
      const log = JSON.parse(localStorage.getItem('nadi-log') || '[]');
      const el = $('#logbook-list');
      const colors = { low: '#22c55e', mid: '#f59e0b', high: '#ef4444', error: '#64748b' };
      el.innerHTML = log.length ? log.slice(0, 6).map(e => `
        <div class="log-row">
          <span class="dot" style="background:${colors[e.level] || '#777'}"></span>
          <span>${new Date(e.ts).toLocaleString()}</span>
          <span class="log-nums">${e.hr ?? '—'} bpm ${e.p !== null ? '· ' + e.p + '%' : ''}</span>
        </div>`).join('') : '<div class="log-empty">—</div>';
      $('#logbook').classList.toggle('hidden', log.length === 0);
    } catch (e) { /* ignore */ }
  }

  /* ------------------------------------------------------------------ */
  /* REPORT (printable HTML + copy)                                     */
  /* ------------------------------------------------------------------ */
  function reportHTML() {
    const r = app.result;
    const f = r.features;
    const lvlName = { low: 'Regular rhythm', mid: 'Inconclusive', high: 'Irregular pattern flagged', error: 'Unreadable' }[r.level];
    const name = ($('#patient-name').value || '').trim() || '(name withheld)';
    const levelNamesT = { low: I18N.t('levelLow'), mid: I18N.t('levelMid'), high: I18N.t('levelHigh') };
    return `<!doctype html><html><head><meta charset="utf-8"><title>NadiSense report</title>
<style>
 body{font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:#111;max-width:720px;margin:24px auto;padding:0 16px}
 h1{font-size:20px} .sub{color:#555} .head{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #0f766e;padding-bottom:8px}
 .badge{display:inline-block;padding:4px 12px;border-radius:999px;color:#fff;font-weight:600;margin:10px 0}
 table{border-collapse:collapse;width:100%;margin:12px 0} td,th{border:1px solid #d5d9de;padding:6px 10px;text-align:left}
 th{background:#f1f5f9} .warn{background:#fff7ed;border:1px solid #fdba74;padding:10px;border-radius:8px;margin:12px 0}
 .foot{font-size:11px;color:#666;border-top:1px solid #ddd;margin-top:20px;padding-top:8px}
 @media print{.no-print{display:none}}
</style></head><body>
<div class="head"><div><h1>NadiSense — Screening Report</h1><div class="sub">${I18N.t('appName')} · on-device AI rhythm screening (PPG)</div></div><div class="sub">${new Date(r.ts).toLocaleString()}</div></div>
<p><b>Person:</b> ${name}</p>
<span class="badge" style="background:${r.level === 'low' ? '#16a34a' : r.level === 'mid' ? '#d97706' : '#dc2626'}">${levelNamesT[r.level] || lvlName} · P=${(r.p * 100).toFixed(0)}%</span>
<p>${I18N.t(r.level === 'low' ? 'levelLowD' : r.level === 'mid' ? 'levelMidD' : 'levelHighD')}</p>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Heart rate</td><td>${Math.round(f.hrMean)} bpm</td></tr>
<tr><td>SDNN</td><td>${f.sdnn.toFixed(0)} ms</td></tr>
<tr><td>RMSSD</td><td>${f.rmssd.toFixed(0)} ms</td></tr>
<tr><td>pNN50</td><td>${f.pnn50.toFixed(0)} %</td></tr>
<tr><td>SD1/SD2</td><td>${f.sd1sd2.toFixed(2)}</td></tr>
<tr><td>LF/HF</td><td>${f.lf_hf.toFixed(2)}</td></tr>
<tr><td>Sample entropy</td><td>${f.sampen.toFixed(2)}</td></tr>
<tr><td>Beats analysed</td><td>${f.n_beats}</td></tr></table>
<p><b>Questionnaire:</b> history — ${app.answers.q1 ? (app.answers.q1.yes ? 'Yes' : 'No') : 'not asked'}; symptoms — ${app.answers.q2 ? app.answers.q2.text : 'not asked'}</p>
<div class="warn"><b>Next step:</b> ${r.level === 'high' ? 'Refer for a 12-lead ECG within 7 days. This is a screening signal — not a diagnosis.' : r.level === 'mid' ? 'Repeat screening in 2 weeks; refer sooner if symptomatic.' : 'Routine follow-up in 6 months; seek care sooner if symptoms appear.'}</div>
<p class="foot">${I18N.t('disclaimer')}<br>NadiSense v0.9 · MatricPhase · TECHNOVA 2026 · generated on-device, no data uploaded.</p>
<button class="no-print" onclick="window.print()">Print</button>
</body></html>`;
  }

  function buildReport() {
    const html = reportHTML();
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `nadi-report-${new Date().toISOString().slice(0, 10)}.html`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  }

  async function copySummary() {
    const r = app.result; if (!r) return;
    const f = r.features;
    const txt = `NadiSense screening ${new Date(r.ts).toLocaleString()}\n` +
      `Level: ${r.level} · P(irregular)=${(r.p * 100).toFixed(0)}%\n` +
      `HR ${Math.round(f.hrMean)} bpm · SDNN ${f.sdnn.toFixed(0)} ms · RMSSD ${f.rmssd.toFixed(0)} ms · ${f.n_beats} beats`;
    try { await navigator.clipboard.writeText(txt); } catch (e) { prompt('Copy:', txt); }
  }

  /* ------------------------------------------------------------------ */
  /* VOICE QUESTIONNAIRE                                                */
  /* ------------------------------------------------------------------ */
  const QUESTIONS = () => [I18N.t('q1'), I18N.t('q2')];
  const LANG_TAG = () => ({ en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN' }[app.lang] || 'en-IN');

  async function askNext() {
    if (app.qIndex >= 2) return;
    const q = QUESTIONS()[app.qIndex];
    $('#q-text').textContent = q;
    $('#q-status').textContent = I18N.t('listening');
    try {
      const txt = await Asr.once(LANG_TAG());
      // robust: explicit no-words → no, anything else (or silence) → yes
      const isNo = /no|nahin|nahi|nah|இல்லை|illai|ille|नहीं/.test(String(txt).toLowerCase());
      const ans = { yes: !isNo, text: txt && txt.trim() ? String(txt).trim() : (isNo ? 'no' : 'yes') };
      app.answers[app.qIndex === 0 ? 'q1' : 'q2'] = ans;
    } catch (e) {
      // voice failed — leave unanswered, tell user to type
      $('#q-status').textContent = I18N.t('voiceUnsupported');
      return;
    }
    app.qIndex++;
    if (app.qIndex < 2) {
      setTimeout(askNext, 600);
    } else {
      $('#q-status').textContent = I18N.t('qAnswered');
    }
  }

  /* ------------------------------------------------------------------ */
  /* WIRING                                                             */
  /* ------------------------------------------------------------------ */
  function wire() {
    $('#btn-start').addEventListener('click', () => startCapture('camera'));
    $('#btn-demo').addEventListener('click', () => startCapture('sim'));
    $('#btn-stop').addEventListener('click', stopCapture);
    $('#sim-seed').addEventListener('input', (e) => { app.simSeed = parseInt(e.target.value || '7', 10); });
    $('#btn-retake').addEventListener('click', () => show('onboard'));
    $('#btn-new').addEventListener('click', () => show('onboard'));
    $('#btn-report').addEventListener('click', buildReport);
    $('#btn-copy').addEventListener('click', copySummary);
    $('#btn-ask-voice').addEventListener('click', () => { app.qIndex = 0; askNext(); });
    $('#btn-q-skip').addEventListener('click', () => { $('#q-status').textContent = I18N.t('qAnswered'); });
    $('#btn-clear-log').addEventListener('click', () => {
      localStorage.removeItem('nadi-log'); renderLogbook();
    });

    // language pills
    $$('.lang-pill').forEach(btn => btn.addEventListener('click', () => {
      app.lang = btn.getAttribute('data-lang');
      I18N.setLang(app.lang);
      I18N.applyDom();
      $$('.lang-pill').forEach(b => b.classList.toggle('active', b === btn));
    }));

    $('#method-details summary').textContent = 'Method & limits';
  }

  /* Debug/test hook: run a full simulated scenario instantly.
   * (Used by tests/run_browser_smoke.mjs and useful at demo time.) */
  function debugRun(kind) {
    const rec = Simulator.generate(kind || 'afib', app.simSeed);
    app.mode = 'sim';
    app.buffer = [];
    for (let i = 0; i < rec.signal.length; i++) {
      app.buffer.push({ t: i / 30, v: rec.signal[i] });
    }
    sources.simData = rec.signal;
    app.simCursor = rec.signal.length;
    app.running = false;
    analyze();
  }
  window.__nadi = { debugRun, getApp: () => app };

  document.addEventListener('DOMContentLoaded', () => {
    I18N.setLang('en');
    I18N.applyDom();
    wire();
    renderLogbook();
    // announce the model facts in the onboarding footer
    if (typeof NADI_MODEL !== 'undefined') {
      const meta = NADI_MODEL.meta || {};
      $('#model-facts').textContent =
        `${meta.architecture || 'MLP 13-20-10-1'} · val acc ${(meta.val_accuracy * 100).toFixed(1)}% · sens ${(meta.val_sensitivity * 100).toFixed(1)}% · spec ${(meta.val_specificity * 100).toFixed(1)}%`;
    }
  });
})();
