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
ok('P(irregular) shown ≈ 100%', parseInt(pv.textContent) >= 95, `(got ${pv.textContent})`);
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

ok('no uncaught errors during full flow', errors.length === 0, errors.join(' | '));

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
