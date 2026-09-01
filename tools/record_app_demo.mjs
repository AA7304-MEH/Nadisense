#!/usr/bin/env node
/*
 * record_app_demo.mjs — REAL screen recording of the NadiSense app.
 * Drives the ACTUAL UI (Demo Mode → AFib capture → result → healthy →
 * motion guardrail → Hindi → report) in headless Chrome and captures
 * frames with page.screenshot() (works on every Chrome build).
 */
import puppeteer from 'puppeteer';
import fs from 'fs';

const URL = 'http://127.0.0.1:8123/index.html';
const FR = '/tmp/frames';
fs.rmSync(FR, { recursive: true, force: true });
fs.mkdirSync(FR, { recursive: true });

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox',
         '--autoplay-policy=no-user-gesture-required'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });

// Guarantee animation + capture-advance even if compositor throttles rAF.
await page.evaluateOnNewDocument(() => {
  window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 33);
  window.cancelAnimationFrame = (id) => clearTimeout(id);
});

await page.goto(URL, { waitUntil: 'networkidle0' });
await new Promise(r => setTimeout(r, 1600));
// DejaVu can't render some emoji → remove the one tofu glyph (privacy lock)
await page.evaluate(() => {
  const el = document.querySelector('.privacy strong');
  if (el) el.textContent = '';
});

/* ---- frame grabber (sequential, best-effort ~12-15 fps) ---- */
let n = 0, busy = false, last = 0;
const grab = setInterval(async () => {
  if (busy) return;
  const now = Date.now();
  if (now - last < 66) return;          // ~15 fps cap
  busy = true; last = now;
  try {
    await page.screenshot({ path: `${FR}/${String(n).padStart(6, '0')}.jpg`, type: 'jpeg', quality: 82 });
    n++;
  } catch (_) {}
  busy = false;
}, 30);

const wait = (ms) => new Promise(r => setTimeout(r, ms));
const click = async (sel, ms = 4000) => {
  try {
    const el = await page.waitForSelector(sel, { visible: true, timeout: ms });
    await el.click();
  } catch (_) { /* already past this state — fine */ }
};

/* ---------- Scene 1 · Onboarding (4.5 s) ---------- */
await wait(4500);

/* ---------- Scene 2 · AFib capture (16 s) ---------- */
await page.select('#sim-kind', 'afib');
await click('#btn-demo');
await wait(16000);
await click('#btn-stop');                 // finish early → analyzing
await wait(3000);

/* ---------- Scene 3 · Result (8.5 s, scroll through plots) ---------- */
await wait(4000);
await page.evaluate(() => {
  const el = document.querySelector('#review-wave');
  if (el) el.scrollIntoView({ block: 'start' });
});
await wait(2500);
await page.evaluate(() => window.scrollTo(0, 0));
await wait(1200);

/* ---------- Scene 4 · Healthy rhythm (10 s + result) ---------- */
await click('#btn-new');
await wait(1300);
await page.select('#sim-kind', 'normal');
await click('#btn-demo');
await wait(24000);
await click('#btn-stop');
await wait(3000);
await wait(2600);

/* ---------- Scene 5 · Motion guardrail (8 s + result) ---------- */
await click('#btn-new');
await wait(1300);
await page.select('#sim-kind', 'motion');
await click('#btn-demo');
await wait(24000);
await click('#btn-stop');
await wait(3000);
await wait(2000);

/* ---------- Scene 6 · Hindi UI (2.5 s) ---------- */
await page.click('.lang-pill[data-lang="hi"]');
await wait(2500);

/* ---------- Scene 7 · Report card (2.5 s) ---------- */
await page.type('#patient-name', 'Demo Patient');
await wait(1200);
try { await click('#btn-report'); } catch (_) {}
await wait(1300);

clearInterval(grab);
await browser.close();
console.log('frames captured:', n);
