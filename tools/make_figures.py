#!/usr/bin/env python3
"""
make_figures.py — renders the signal figures used in the pitch deck.
The waveforms come from the SAME simulator + DSP pipeline that ships in
the app, so the deck figures are literally the product's output.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

# ---- reuse the app's simulator by calling node ----
import subprocess, json
def js_run(code):
    r = subprocess.run(['node', '-e', code], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/..')
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return r.stdout

def banner_wave(png, seconds=30, kind='normal', seed=7, w=2200, h=340,
                color=(45, 212, 191), bg=(11, 34, 49)):
    """Thin pulse strip for the title slide + AI slide."""
    code = f"""
const DSP = require('./js/dsp.js');
const Sim = require('./js/simulator.js');
const sig = Sim.generate('{kind}', {seed}).signal;
const det = DSP.detrend(sig);
const bp = DSP.bandpass(det, 0.6, 3.5, 30);
process.stdout.write(JSON.stringify(Array.from(bp)));
"""
    bp = np.array(json.loads(js_run(code)))
    img = Image.new('RGB', (w, h), bg)
    px = img.load()
    mn, mx = bp.min(), bp.max()
    rng = max(mx - mn, 1e-9)
    n = len(bp)
    for i in range(n - 1):
        x0, x1 = int(i / n * w), int((i + 1) / n * w)
        y0 = h * 0.5 - ((bp[i] - mn) / rng - 0.5) * h * 0.72
        y1 = h * 0.5 - ((bp[i + 1] - mn) / rng - 0.5) * h * 0.72
        for x in range(x0, x1):
            y = y0 + (y1 - y0) * (x - x0) / max(x1 - x0, 1)
            for dy in range(-2, 3):
                yy = int(y) + dy
                if 0 <= yy < h:
                    px[x, yy] = color
    img.save(png)
    return png

def tach_pair(png, kind_a='normal', kind_b='afib', seed=7, w=1600, h=700):
    """RR-interval tachogram: healthy vs AFib-like (top/bottom)."""
    code = f"""
const DSP = require('./js/dsp.js');
const Sim = require('./js/simulator.js');
const out = {{}};
for (const k of ['{kind_a}', '{kind_b}']) {{
  const sig = Sim.generate(k, {seed}).signal;
  const f = DSP.features(sig);
  out[k] = {{ rr: f.rr, hr: f.hrMean, sdnn: f.sdnn }};
}}
process.stdout.write(JSON.stringify(out));
"""
    data = json.loads(js_run(code))
    img = Image.new('RGB', (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    palette = [(15, 118, 110), (220, 38, 38)]  # teal / red
    titles = [f"Healthy sinus rhythm — HR {data[kind_a]['hr']:.0f} bpm · SDNN {data[kind_a]['sdnn']:.0f} ms",
              f"AFib-like trace — HR {data[kind_b]['hr']:.0f} bpm · SDNN {data[kind_b]['sdnn']:.0f} ms"]
    for idx, kind in enumerate([kind_a, kind_b]):
        rr = data[kind]['rr']
        top = idx * (h // 2)
        d.text((20, top + 12), titles[idx], fill=(30, 41, 59))
        d.line([(20, top + 44), (w - 20, top + 44)], fill=(226, 232, 240), width=2)
        bw = (w - 40) / len(rr)
        for i, v in enumerate(rr):
            hh = (v - 0.3) / 1.1 * (h / 2 - 90)
            x0 = 20 + i * bw
            y0 = top + h - 46
            d.rectangle([x0, y0 - hh, x0 + max(bw - 2, 1.5), y0], fill=palette[idx])
    img.save(png)
    return png

def poincare_pair(png, kind_a='normal', kind_b='afib', seed=7, w=1600, h=760):
    code = f"""
const DSP = require('./js/dsp.js');
const Sim = require('./js/simulator.js');
const out = {{}};
for (const k of ['{kind_a}', '{kind_b}']) {{
  const sig = Sim.generate(k, {seed}).signal;
  out[k] = DSP.features(sig).rr;
}}
process.stdout.write(JSON.stringify(out));
"""
    data = json.loads(js_run(code))
    img = Image.new('RGB', (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for idx, kind in enumerate([kind_a, kind_b]):
        rr = data[kind]
        ox = idx * (w // 2)
        d.rectangle([ox + 24, 30, ox + w // 2 - 24, h - 40], outline=(203, 213, 225), width=3)
        for i in range(len(rr) - 1):
            x, y = rr[i], rr[i + 1]
            cx = ox + 24 + (x - 0.3) / 1.1 * (w // 2 - 48)
            cy = h - 44 - (y - 0.3) / 1.1 * (h - 74)
            r = 4 if idx == 0 else 4
            if idx == 0:
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(15, 118, 110))
            else:
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 38, 38))
        d.text((ox + 30, 12), f"Poincaré · {'healthy' if idx == 0 else 'AFib-like'}", fill=(30, 41, 59))
    img.save(png)
    return png

if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    outdir = '../assets'
    os.makedirs(outdir, exist_ok=True)
    banner_wave(f'{outdir}/wave_banner.png', color=(45, 212, 191), bg=(11, 34, 49))
    banner_wave(f'{outdir}/wave_banner_afib.png', kind='afib', color=(248, 113, 113), bg=(30, 10, 14))
    tach_pair(f'{outdir}/tach_pair.png')
    poincare_pair(f'{outdir}/poincare_pair.png')
    print('figures written to', outdir)
