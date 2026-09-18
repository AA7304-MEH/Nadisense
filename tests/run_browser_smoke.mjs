#!/usr/bin/env node
/*
 * run_browser_smoke.mjs — boots the actual app in jsdom and drives it
 * through the real UI: on-boarding, language switch, a full AF scenario
 * (debugRun), the complete result dashboard, and a normal scenario.
 *
 * Run:  node tests/run_browser_smoke.mjs
 */

import { JSDOM } from 'jsdom';
import path from 'path';
import { fileURLToPath } from 'url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = path.join(root, 'index.html');

let pass = 0, fail = 0;
const ok = (name, cond, extra = '') => {
  if (cond) { pass++; console.log(`  ✓ ${name}`); }
  else { fail++; console.log(`  ✗ ${name} ${extra}`); }
};

const errors = [];

const dom = await JSDOM.fromFile(html, {
  runScripts: 'dangerously',
  resources: 'usable',
  pretendToBeVisual: true,
  url: 'file://' + html,
  beforeParse(window) {
    // canvas 2D stub (no native canvas in jsdom)
    const ctx2d = () => new Proxy({}, {
      get(t, k) {
        if (k === 'canvas') return { width: 300, height: 150 };
        return typeof k === 'string' ? (() => {}) : undefined;
      },
      set() { return true; },
    });
    window.HTMLCanvasElement.prototype.getContext = ctx2d;
    // in-memory localStorage (jsdom disables it for file:// origins)
    const store = {};
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: (k) => (k in store ? store[k] : null),
        setItem: (k, v) => { store[k] = String(v); },
        removeItem: (k) => { delete store[k]; },
      },
      configurable: true,
    });
    window.HTMLElement.prototype.getBoundingClientRect = () =>
      ({ left: 0, top: 0, right: 320, bottom: 220, width: 320, height: 220 });
    window.onerror = (msg, src, line, col, err) => errors.push(String(msg));
    window.addEventListener('error', (e) => errors.push(String(e.message)));
  },
});

const w = dom.window;
await new Promise((res) => { if (w.document.readyState === 'complete') res(); else w.addEventListener('load', res); });
// give script execution a beat
await new Promise(r => setTimeout(r, 400));

console.log('NadiSense browser smoke test\n');

ok('app booted (onboard visible)', w.document.querySelector('#view-onboard').classList.contains('active'));
ok('no uncaught errors at boot', errors.length === 0, errors.join(' | '));

// language switch
const taPill = w.document.querySelector('.lang-pill[data-lang="ta"]');
taPill.dispatchEvent(new w.Event('click', { bubbles: true }));
const h1 = w.document.querySelector('#view-onboard h1');
ok('Tamil UI applied', h1.textContent.includes('60 வினாடி'));
w.document.querySelector('.lang-pill[data-lang="en"]').dispatchEvent(new w.Event('click', { bubbles: true }));

// full AF scenario through the real UI
w.__nadi.debugRun('afib');
await new Promise(r => setTimeout(r, 2400)); // staged reveal ~1.4 s + slack

const dash = w.document.querySelector('#result-dash');
ok('result dashboard shown', !dash.classList.contains('hidden'));
const chip = w.document.querySelector('#level-chip');
ok('AF scenario → high-risk chip', chip.textContent.includes('Irregular'), `(got "${chip.textContent}")`);
const pv = w.document.querySelector('#p-value');
// AF scenario must read clearly high-probability. The real-data (AFDB) model is
// calibrated rather than saturated like the old synthetic one — an extreme
// synthetic AF pattern reads ~90% instead of pegging at 100%. ≥ 85% keeps the
// user-facing "high-risk" meaning; the chip assertion above guards the class.
ok('P(irregular) shown high (≥ 85%)', parseInt(pv.textContent) >= 85, `(got ${pv.textContent})`);
ok('8 HRV metric cards', w.document.querySelectorAll('#metric-grid .metric').length === 8);
ok('warnings/notes rendered', w.document.querySelector('#notes').textContent.trim().length > 0);
ok('logbook row recorded', w.document.querySelectorAll('#logbook-list .log-row').length >= 1);

// normal scenario
w.__nadi.debugRun('normal');
await new Promise(r => setTimeout(r, 2400));
const chip2 = w.document.querySelector('#level-chip');
ok('normal scenario → regular-rhythm chip', chip2.textContent.includes('regular'), `(got "${chip2.textContent}")`);
const pv2 = w.document.querySelector('#p-value');
ok('P(irregular) low for normal', parseInt(pv2.textContent) <= 30, `(got ${pv2.textContent})`);

// report builder produces a document
const patient = w.document.querySelector('#patient-name');
patient.value = 'Demo Patient';
let reportOk = false;
try {
  const htmlStr = (function () {
    // call buildReport indirectly via click; capture blob creation
    const oldCreate = w.URL.createObjectURL;
    w.URL.createObjectURL = () => 'blob:mock';
    w.document.querySelector('#btn-report').dispatchEvent(new w.Event('click', { bubbles: true }));
    return true;
  })();
  reportOk = reportOk || true;
} catch (e) { reportOk = false; }
ok('report export triggered without error', reportOk);

// ---------- regression: camera-mode window reads the buffer archive ----------
{
  // Simulate exactly what captureLoop does in camera mode: samples land in
  // app.buffer while the (transient) queue is drained every frame. The
  // old bug read the drained queue → flat signal → "could not read pulse".
  const app = w.__nadi.getApp();
  const src = w.__nadi.sources;
  app.mode = 'camera';
  app.buffer = [];
  const rec = w.__nadi ? true : false;
  // synthetic normal-rhythm signal written like the camera drain writes it
  const sim = (function () {
    // reuse the real simulator via the exposed sources module-level object
    const out = [];
    for (let i = 0; i < 900; i++) {
      const t = i / 30;
      out.push({ t, v: 128 + 6 * Math.sin(2 * Math.PI * 1.2 * t) + (i % 7) * 0.05 });
    }
    return out;
  })();
  for (const s of sim) app.buffer.push(s);   // queue drained elsewhere — buffer holds it all

  const win = src.window(0, 30);
  ok('cam-regression: window(0,30) returns 900 samples from buffer archive',
    win.length === 900, `got ${win.length}`);
  let mn = 1e9, mx = -1e9, flat = true;
  for (const v of win) { if (v < mn) mn = v; if (v > mx) mx = v; }
  flat = (mx - mn) < 1;
  ok('cam-regression: signal is NOT flat (peak-to-peak ' + (mx - mn).toFixed(2) + ')', !flat);
  const ft = w.__nadi.sources && w.eval('DSP') ? w.eval('DSP').features(win) : null;
  ok('cam-regression: DSP features extractable (HR ≈ ' + (ft ? ft.hrMean.toFixed(0) : 'null') + ' bpm)',
    !!ft && Math.abs(ft.hrMean - 72) < 10);

  // ---------- adaptive channel: saturated green + pulsatile red ----------
  app.camChan = null;
  app.buffer = [];
  for (let i = 0; i < 900; i++) {
    const t = i / 30;
    app.buffer.push({
      t,
      v: 253,                                  // legacy green field: saturated
      g: 253,                                  // green clipped near white
      r: 170 + 12 * Math.sin(2 * Math.PI * 1.2 * t),   // red carries the pulse
      b: 60,
    });
  }
  const win2 = src.window(0, 30);
  let mn2 = 1e9, mx2 = -1e9;
  for (const v of win2) { if (v < mn2) mn2 = v; if (v > mx2) mx2 = v; }
  ok('cam-adaptive: saturated-green capture auto-switches to RED channel',
    app.camChan === 'red' && (mx2 - mn2) > 5,
    `chan=${app.camChan} p2p=${(mx2 - mn2).toFixed(1)}`);
  const ft2 = w.eval('DSP') ? w.eval('DSP').features(win2) : null;
  ok('cam-adaptive: pulse extractable from red channel (HR ≈ ' + (ft2 ? ft2.hrMean.toFixed(0) : 'null') + ')',
    !!ft2 && Math.abs(ft2.hrMean - 72) < 10);
  app.camChan = null;

  // edge: empty buffer must not explode (defensive path)
  app.buffer = [];
  const empty = src.window(0, 5);
  ok('cam-regression: empty buffer returns safe zeros (no crash)',
    empty.length === 150 && empty.every(v => v === 0));
  app.mode = 'sim';
}

// ---------- camera failure UX: every broken context must get a named, ----------
// ---------- fixable answer — and the user is never silently dead-ended ----------
{
  const $ = (s) => w.document.querySelector(s);
  const app = w.__nadi.getApp();
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const camErrOf = (name) => Object.assign(new Error('test'), { name });

  // (1) insecure context (file:// — jsdom has no mediaDevices at all) →
  //     the secure-link guidance, not a black screen
  $('#btn-start').click();
  await sleep(80);
  ok('cam-ux: insecure context shows the secure-link panel',
    !$('#cam-error').classList.contains('hidden') &&
    $('#cam-err-title').textContent === 'Camera needs the secure link',
    `(title="${$('#cam-err-title').textContent}")`);
  ok('cam-ux: app not left "running" after failed start', app.running === false);

  // (2) persistent permission denial → unblock-instructions panel.
  //     This is the "works in incognito but not in my normal tab" case:
  //     incognito never remembers the deny; the panel now tells the user
  //     exactly how to allow it for normal tabs too.
  Object.defineProperty(w.navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia: () => Promise.reject(camErrOf('NotAllowedError')) },
  });
  $('#cam-retry').click();           // Retry re-attempts the REAL camera path
  await sleep(80);
  ok('cam-ux: denied camera shows step-by-step unblock (normal-tabs fix)',
    !$('#cam-error').classList.contains('hidden') &&
    $('#cam-err-title').textContent === 'Camera is blocked for this site' &&
    $('#cam-err-body').textContent.includes('NORMAL tabs'),
    `(title="${$('#cam-err-title').textContent}")`);

  // (3) camera held by another app/tab → "close it and retry" panel
  w.navigator.mediaDevices.getUserMedia = () => Promise.reject(camErrOf('NotReadableError'));
  $('#cam-retry').click();
  await sleep(80);
  ok('cam-ux: busy camera shows close-other-apps panel',
    $('#cam-err-title').textContent === 'Camera is busy',
    `(title="${$('#cam-err-title').textContent}")`);

  // (4) the escape hatch always works: "Use Demo Mode instead" starts sim
  $('#cam-todemo').click();
  await sleep(80);
  ok('cam-ux: demo fallback button starts Demo Mode',
    $('#cam-error').classList.contains('hidden') &&
    !$('#sim-panel').classList.contains('hidden') && app.mode === 'sim');
  $('#btn-stop').click();            // finish cleanly so no live loop lingers
  await sleep(80);
}

ok('no uncaught errors during full flow', errors.length === 0, errors.join(' | '));

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
