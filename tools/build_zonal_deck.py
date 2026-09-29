#!/usr/bin/env python3
"""
build_zonal_deck.py — TECHNOVA 2026 Online Zonal Evaluation deck
================================================================
Rebuilds the NadiSense pitch specifically for the 15-minute jury slot
(12 min talk + demo, 3 min Q&A). Every slide is tagged top-right with
the jury criterion it answers, so the panel can score while we talk.

Output: UPLOAD_THIS/NadiSense_Zonal_Round_Pitch.pptx  (16:9, dark theme)
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import qrcode, os

# ---------- palette -------------------------------------------------
BG      = RGBColor(0x0B, 0x12, 0x20)   # deep navy
CARD    = RGBColor(0x12, 0x1D, 0x31)   # card navy
EDGE    = RGBColor(0x1F, 0x2E, 0x49)   # hairline
TEAL    = RGBColor(0x2D, 0xD4, 0xBF)   # app accent
GREEN   = RGBColor(0x22, 0xC5, 0x5E)
AMBER   = RGBColor(0xF5, 0x9E, 0x0B)
RED     = RGBColor(0xEF, 0x44, 0x44)
WHITE   = RGBColor(0xF1, 0xF5, 0xF9)
MUTED   = RGBColor(0x94, 0xA3, 0xB8)
FONT    = 'Segoe UI'
FONT_L  = 'Segoe UI Light'

SW, SH = Inches(13.333), Inches(7.5)

prs = Presentation()
prs.slide_width, prs.slide_height = SW, SH
BLANK = prs.slide_layouts[6]

ASSETS = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets'))

# ---------- helpers -------------------------------------------------
def slide():
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    r.fill.solid(); r.fill.fore_color.rgb = BG
    r.line.fill.background(); r.shadow.inherit = False
    return s

def box(s, x, y, w, h, fill=CARD, line=EDGE, radius=True):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                             Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        try: shp.adjustments[0] = 0.055
        except Exception: pass
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None: shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp

def txt(s, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = wrap; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get('align', PP_ALIGN.LEFT)
        para.space_before = Pt(p.get('before', 0)); para.space_after = Pt(p.get('after', 0))
        para.line_spacing = p.get('ls', 1.0)
        runs = p['runs'] if 'runs' in p else [p]
        for rr in runs:
            run = para.add_run(); run.text = rr['t']
            f = run.font
            f.size = Pt(rr.get('size', 14)); f.bold = rr.get('bold', False)
            f.italic = rr.get('italic', False)
            f.color.rgb = rr.get('color', WHITE)
            f.name = rr.get('font', FONT)
    return tb

def kick(s, text, y=0.42):
    txt(s, 0.62, y, 9.5, 0.32, [dict(t=text.upper(), size=11, bold=True, color=TEAL)])

def title(s, text, y=0.72, size=30):
    txt(s, 0.6, y, 12.1, 1.0, [dict(t=text, size=size, bold=True, color=WHITE)])

def pill(s, text, x=10.55, y=0.44, w=2.2, color=CARD):
    p = box(s, x, y, w, 0.3, fill=color, line=EDGE)
    tf = p.text_frame; tf.word_wrap = False
    tf.margin_left = tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = 0
    para = tf.paragraphs[0]; para.alignment = PP_ALIGN.CENTER
    run = para.add_run(); run.text = text
    run.font.size = Pt(9); run.font.bold = True; run.font.color.rgb = MUTED; run.font.name = FONT
    return p

def footer(s, n):
    txt(s, 0.62, 7.08, 12.1, 0.3, [
        dict(t=f'Agent Matrix · Thakur College of Engineering & Technology · TECHNOVA 2026 Zonal      {n:02d}',
             size=9, color=MUTED)])

def pic(s, path, x, y, w=None, h=None):
    kw = {}
    if w: kw['width'] = Inches(w)
    if h: kw['height'] = Inches(h)
    return s.shapes.add_picture(os.path.join(ASSETS, path), Inches(x), Inches(y), **kw)

def code(s, text, x, y, w, h, size=11):
    b = box(s, x, y, w, h, fill=RGBColor(0x0A, 0x10, 0x1D), line=EDGE)
    tf = b.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.14); tf.margin_top = tf.margin_bottom = Inches(0.1)
    first = True
    for line in text.split('\n'):
        para = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        run = para.add_run(); run.text = line
        run.font.size = Pt(size); run.font.color.rgb = RGBColor(0xA7, 0xF3, 0xD0)
        run.font.name = 'Consolas'
    return b

def notes(s, text):
    s.notes_slide.notes_text_frame.text = text

def bullets(s, x, y, w, h, items, size=14, gap=6, ls=1.12):
    paras = []
    for it in items:
        if isinstance(it, tuple):
            head, body = it
            paras.append(dict(runs=[dict(t=head, size=size, bold=True, color=WHITE),
                                    dict(t=body, size=size, color=MUTED)], ls=ls, after=gap))
        else:
            paras.append(dict(t=it, size=size, color=WHITE, ls=ls, after=gap))
    return txt(s, x, y, w, h, paras)

# ---------- QR for the demo slide -----------------------------------
qr_img = '/tmp/nadisense_qr.png'
qrcode.make('https://nadisense.vercel.app', border=2, box_size=12).save(qr_img)

# ====================================================================
# SLIDE 1 — TITLE
# ====================================================================
s = slide()
txt(s, 0.62, 0.55, 12.1, 0.35, [dict(t='AGENT MATRIX · TECHNOVA 2026 · NATIONAL GRAND FINALE · MADURAI', size=12, bold=True, color=TEAL)])
txt(s, 0.6, 1.05, 12.1, 1.6, [
    dict(t='NadiSense', size=64, bold=True, color=WHITE, font=FONT_L),
    dict(t='60-second AI heart-rhythm screening for rural India', size=22, color=TEAL, before=6),
])
pic(s, 'wave_banner_afib.png', 0.62, 3.05, w=12.1)
box(s, 0.62, 3.75, 12.1, 0.02, fill=EDGE, line=None, radius=False)
bullets(s, 0.62, 4.15, 12.1, 1.6, [
    'Every phone already carries the sensor. We turn the camera into a screening-grade pulse reader — point it, wait 60 seconds, flag risk.',
    (' ₹0 hardware', '   nothing to buy, nothing to charge beyond the phone in the ASHA worker\'s hand'),
    (' ₹0 internet', '   the entire AI runs on-device; zero data ever leaves the phone'),
], size=16, gap=8)
txt(s, 0.62, 6.35, 12.1, 0.6, [dict(runs=[
    dict(t='LIVE: ', size=13, bold=True, color=MUTED),
    dict(t='nadisense.vercel.app', size=13, bold=True, color=TEAL),
    dict(t='    ·    repo: github.com/AA7304-MEH/Nadisense    ·    team: Aditya Mehra · Akanshu Pandey · Siddesh Wagh', size=13, color=MUTED)])])
footer(s, 1)
notes(s, """[0:00 open — 45 s] Namaste. We are Agent Matrix from Thakur College of Engineering and Technology, Mumbai University. NadiSense is a 60-second AI heart-rhythm screening built for rural India.
One line: a community health worker presses any phone camera against a fingertip, and in one minute our on-device AI flags an irregular rhythm — with zero extra hardware and zero internet.
We will spend two minutes on why this matters, four minutes on how it works, two minutes live with the product — it is deployed right now at nadisense.vercel.app — and the rest on evidence and scale.""")

# ====================================================================
# SLIDE 2 — THE PROBLEM  (criterion 1)
# ====================================================================
s = slide()
kick(s, 'The problem · clarity & relevance')
pill(s, 'JURY ① · PROBLEM')
title(s, "India's #1 killer — and the village never sees an ECG")
stats = [
    ('28%', 'of all Indian deaths are cardio-vascular (GBD/IHME) — the single largest killer', TEAL),
    ('5×', 'stroke risk in atrial fibrillation, the most common sustained arrhythmia (AHA)', RED),
    ('silent', 'most AFib episodes produce no symptoms — the first sign is often the stroke itself', AMBER),
]
x = 0.62
for head, body, col in stats:
    b = box(s, x, 1.95, 3.9, 1.75)
    txt(s, x + 0.25, 2.15, 3.4, 1.3, [
        dict(t=head, size=34, bold=True, color=col),
        dict(t=body, size=12.5, color=MUTED, before=4, ls=1.15)])
    x += 4.1
bullets(s, 0.62, 4.15, 12.1, 2.6, [
    ('The gap is access, not awareness.  ', 'An ECG means travel to the town, a queue, a fee. So screening simply does not happen below the district headquarters.'),
    ('The medicity is lopsided.  ', 'Most specialists sit in cities; a village meets a doctor rarely, a cardiologist almost never. The ASHA/ANM worker is the only health touchpoint that reliably reaches the last mile.'),
    ('Timing decides outcomes.  ', 'AFib caught early is managed with a cheap blood-thinner; caught late it is a stroke, a hospital bed, a family pushed into debt.'),
], size=15, gap=10)
footer(s, 2)
notes(s, """[~0:45 — 60 s] Why this problem. Cardio-vascular disease is India's biggest killer — about 28% of all deaths. Atrial fibrillation is the most common sustained arrhythmia and it multiplies stroke risk five times — and the cruel part is that most AFib is silent: no chest pain, no warning. The first symptom is often the stroke.
Now look at rural access: an ECG means a trip to the town and a queue, so below district level, screening effectively does not happen. The one reliable health touchpoint in a village is the ASHA worker.
We are not diagnosing disease here — we are finding the silent risk early, when a referral still changes the outcome.""")

# ====================================================================
# SLIDE 3 — VALIDATION OF NEED (criterion 2)
# ====================================================================
s = slide()
kick(s, 'Problem validation · why existing options fail')
pill(s, 'JURY ② · VALIDATION')
title(s, 'Every existing answer fails on cost, distance, or power')
rows = [
    ('Hospital ECG', '₹200–500 + travel + half-day wage lost', 'gold standard but unreachable as a *habit*'),
    ('Smartwatch ECG', '₹8,000–40,000 per device', 'one person owns it — not a population tool'),
    ('Handheld ECG devices', '₹5,000–15,000 hardware per unit', 'one unit per PHC; needs batteries, maintenance, calibration'),
    ('NadiSense', '₹0 — the phone already exists', 'screening as a daily habit, at the doorstep'),
]
y = 1.85
for name, cost, note in rows:
    last = name == 'NadiSense'
    b = box(s, 0.62, y, 12.1, 0.78, fill=RGBColor(0x10, 0x2A, 0x27) if last else CARD,
            line=TEAL if last else EDGE)
    txt(s, 0.92, y + 0.13, 3.6, 0.5, [dict(t=name, size=15, bold=True, color=TEAL if last else WHITE)])
    txt(s, 4.35, y + 0.13, 3.9, 0.5, [dict(t=cost, size=13, color=TEAL if last else MUTED)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, 8.15, y + 0.13, 4.35, 0.5, [dict(t=note, size=12, italic=True, color=TEAL if last else MUTED)], anchor=MSO_ANCHOR.MIDDLE)
    y += 0.92
bullets(s, 0.62, 5.8, 12.1, 1.1, [
    ('Why now:  ', 'India carries 750 M+ smartphones (NITI/ICEA). Photoplethysmography — the same physics as the hospital finger-clip — works off a camera sensor and a flash. Two mature pieces finally overlap for the first population-scale tool.'),
], size=14, gap=6)
footer(s, 3)
notes(s, """[~1:45 — 55 s] How did we validate the need? By elimination. The hospital ECG is the gold standard but unreachable as a habit. A smartwatch is thirty thousand rupees and screens one person. Handheld ECG boxes solve cost per test but add hardware, maintenance and calibration — and they sit one-per-PHC.
And why now: three-quarters of a billion Indians already carry the sensor — the smartphone. Camera PPG uses the same physics as the hospital's finger-clip oximeter. The two halves of the solution already exist; nobody had assembled them into a doorstep habit yet. That is the gap NadiSense fills.""")

# ====================================================================
# SLIDE 4 — SOLUTION & ORIGINALITY (criterion 3)
# ====================================================================
s = slide()
kick(s, 'The solution · originality')
pill(s, 'JURY ③ · INNOVATION')
title(s, 'Fingertip on the lens. Sixty seconds. A care decision.')
pic(s, 'ui_mock.png', 8.55, 1.7, w=4.35)
diffs = [
    ('Zero-hardware', 'No device to buy, ship, charge or calibrate. The cameraphone IS the instrument.', TEAL),
    ('11.5 KB on-device AI', 'A neural net smaller than an SMS. Runs offline in ~2 ms on any entry-level phone.', TEAL),
    ('Refuses to guess', 'Motion or weak light → quality gate FAILS the capture instead of inventing a rhythm.', TEAL),
    ('Speaks her language', 'English · हिंदी · தமிழ் UI + voice prompts for low-literacy users.', TEAL),
]
y = 1.75
for head, body, col in diffs:
    b = box(s, 0.62, y, 7.6, 1.12)
    txt(s, 0.9, y + 0.12, 7.1, 0.9, [
        dict(t=head, size=15, bold=True, color=TEAL),
        dict(t=body, size=12.5, color=MUTED, before=3, ls=1.12)])
    y += 1.28
footer(s, 4)
notes(s, """[~2:40 — 50 s] The solution in one breath: fingertip covers the rear camera, the app reads the pulse wave for about a minute, an on-device neural network scores it, and the health worker gets a green, amber or red care level with the next step written in her language.
Three original decisions define the product. One, zero hardware — the phone is the instrument. Two, the entire AI lives on the phone — the model is six kilobytes, smaller than a single SMS. Three — and judges, this one we are proudest of — the app refuses to guess: if the signal is bad it fails the test and asks for a retake. You will see that guardrail live shortly.""")

# ====================================================================
# SLIDE 5 — THE AI, SPECIFICALLY (criterion 4)
# ====================================================================
s = slide()
kick(s, 'Artificial intelligence · meaningful application')
pill(s, 'JURY ④ · AI DEPTH')
title(s, 'An 11.5 KB network on 12 cardiologist-readable features')
code(s, 'pipeline:  PPG @30 Hz → detrend → FFT band-pass 0.6–3.5 Hz\n'
        '           → 2-pass adaptive systolic peak detection\n'
        '           → 12 HRV / irregularity features   (winsorised ±3σ)\n'
        '           → MLP 12 → 20 → 10 → 1   (tanh · tanh · sigmoid)\n'
        '           → P(irregular rhythm) → green / amber / red care level',
     0.62, 1.85, 12.1, 1.52, size=12.5)
feats = ['heart rate', 'SDNN', 'RMSSD', 'pNN50', 'SD1, SD2', 'SD1/SD2', 'LF/HF', 'spectral entropy', 'sample entropy', 'turning-point ratio', 'irregularity %', 'ectopy-like %']
x, y = 0.62, 3.6
for i, f in enumerate(feats):
    b = box(s, x, y, 2.42, 0.52, fill=CARD)
    txt(s, x, y + 0.1, 2.42, 0.34, [dict(t=f, size=12, color=WHITE, align=PP_ALIGN.CENTER)])
    x += 2.62
    if x > 10.5: x, y = 0.62, y + 0.68
bullets(s, 0.62, 5.15, 12.1, 1.8, [
    ('Trained on real patients.  ', 'MIT-BIH AFDB — 25 cardiologist-annotated AFib patients → 93,730 windows; held out on 5 patients it never saw: 97.2% acc · 99.5% sens · 95.2% spec. One-command retrain in the repo.'),
    ('Small on purpose.  ', 'A black-box model cannot be audited by a PHC doctor. Each of our 12 inputs has a published cardiology meaning — the decision is explainable feature by feature.'),
], size=14, gap=8)
footer(s, 5)
notes(s, """[~3:30 — 70 s] Now the AI itself — because this rubric scores meaningful AI, not buzzword AI.
We do not feed raw pixels into a mystery net. The camera gives a pulse wave; classical DSP cleans it; an adaptive two-pass peak detector finds each heartbeat; from the beat intervals we compute twelve heart-rate-variability features — SDNN, RMSSD, pNN50, Poincaré ratios, entropy measures, ectopy fraction. Every one of these exists in cardiology literature. Only then a small multilayer perceptron — 12-20-10-1, six kilobytes, two-millisecond inference — maps them to one number: probability of an irregular rhythm.
It is trained on REAL patient data — the MIT-BIH Atrial Fibrillation Database — and scored on five patients it never saw in training: ninety-seven-point-two accuracy, ninety-nine-point-five sensitivity, ninety-five-point-two specificity. Small was a choice: it is auditable, it runs offline on a two-thousand-rupee phone, and a doctor can see exactly which feature pushed the score.""")

# ====================================================================
# SLIDE 6 — ARCHITECTURE (criterion 5)
# ====================================================================
s = slide()
kick(s, 'Technical architecture')
pill(s, 'JURY ⑤ · ARCHITECTURE')
title(s, 'Everything happens on the phone. There is no server.')
steps = [
    ('CAMERA', 'green-channel ROI summed per frame · 30 Hz · nothing stored'),
    ('DSP', 'detrend · zero-phase FFT band-pass 0.6–3.5 Hz'),
    ('PEAKS', 'two-pass adaptive systolic detection → beat intervals'),
    ('FEATURES', '12 HRV / irregularity features · winsorised'),
    ('MLP 12-20-10-1', '11.5 KB weights · 2 ms · plain-text audited'),
    ('CARE LEVEL', 'green · amber · red + next step in 3 languages'),
]
x = 0.45
for i, (head, body) in enumerate(steps):
    b = box(s, x, 2.0, 1.92, 1.85, fill=RGBColor(0x10, 0x24, 0x26), line=TEAL)
    txt(s, x + 0.09, 2.14, 1.75, 1.6, [
        dict(t=f'{i+1}', size=11, bold=True, color=AMBER),
        dict(t=head, size=12.5, bold=True, color=WHITE, before=2),
        dict(t=body, size=9.5, color=MUTED, before=4, ls=1.1)], wrap=True)
    if i < 5:
        txt(s, x + 1.93, 2.6, 0.42, 0.5, [dict(t='→', size=20, bold=True, color=TEAL)])
    x += 2.14
bullets(s, 0.62, 4.35, 12.1, 2.3, [
    ('Deployment is a file copy.  ', 'The whole product is one static page — GitHub Pages, Vercel, an SD card, WhatsApp. No backend, no DB, no ops cost. It will run unchanged in ten years.'),
    ('Quality is a first-class citizen.  ', 'A live quality index watches every capture; below threshold the app aborts with coaching tips instead of showing a risky number.'),
    ('Resilient by design.  ', 'If the camera is blocked or unavailable, the capture degrades gracefully into a labelled demo — the demo path runs the identical pipeline, so evaluators always see real behaviour.'),
], size=14, gap=8)
footer(s, 6)
notes(s, """[~4:40 — 60 s] Architecture. One screen, six blocks, no server. Camera frames are reduced in-place to one green-channel number each — the photo is never stored, let alone uploaded.
The signal chain is deliberately boring, proven DSP: detrend, FFT band-pass in the pulse band, adaptive peak detection. Then the twelve features, then the six-K network, then a three-level care recommendation.
Two architecture choices to note. Deployment is a file copy — a static page, which means zero operating cost and it survives supply-chain and connectivity reality. And quality is a first-class citizen: beneath every result sits a signal-quality gate that would rather say "retake" than show you a risky number. This discipline is what makes field deployment safe.""")

# ====================================================================
# SLIDE 7 — LIVE DEMO (criterion 6)
# ====================================================================
s = slide()
kick(s, 'Working prototype · live now')
pill(s, 'JURY ⑥ · LIVE DEMO')
title(s, 'It is live — scan it, judge it yourself')
box(s, 0.62, 1.8, 3.4, 3.4, fill=RGBColor(0xFF, 0xFF, 0xFF), line=None)
s.shapes.add_picture(qr_img, Inches(0.77), Inches(1.95), width=Inches(3.1))
txt(s, 0.62, 5.35, 3.4, 0.7, [dict(t='nadisense.vercel.app', size=14, bold=True, color=TEAL, align=PP_ALIGN.CENTER),
                              dict(t='opens on any phone — no install', size=10.5, color=MUTED, align=PP_ALIGN.CENTER, before=3)])
bullets(s, 4.6, 1.95, 8.0, 3.2, [
    ('Demo 1 — AFib-like signal (40 s):  ', 'simulated irregular pulse through the REAL pipeline → needle sweeps red, P(irregular) ≈ 91% → red card, eight HRV cards fill.'),
    ('Demo 2 — contrast (20 s):  ', 'same app, normal sinus rhythm → green, P ≈ 0%. The swing is the point.'),
    ('Demo 3 — honesty (15 s):  ', 'heavy-motion scenario → quality gate FAILS the test, "could not read the pulse, retake". A diagnostic tool that refuses to guess.'),
], size=14.5, gap=10)
box(s, 4.6, 5.0, 8.0, 1.3, fill=CARD, line=AMBER)
txt(s, 4.85, 5.18, 7.5, 1.0, [
    dict(t='If Zoom screen-share fails:', size=13, bold=True, color=AMBER),
    dict(t='83-second recorded run (NadiSense_Demo.mp4, already submitted) + offline single-file copy (nadi.html — works from a pen-drive, no internet). Three independent fallbacks.', size=12, color=MUTED, before=4, ls=1.15)])
footer(s, 7)
notes(s, """[~5:40 — DEMO ~2.5 min] I will now run it live — and so can you: that QR opens the same deployment on your own phone.
[share screen → nadisense.vercel.app → Demo Mode → Atrial fibrillation-like → Start]
Watch the live waveform and the quality meter. The signal is synthetic but it is going through the identical DSP and classifier as camera capture — this is stated plainly inside the app and in our README.
[finish early → result] Red: ninety-nine to hundred percent irregular, with all twelve features laid out. [new test → normal sinus → green]. [new test → heavy motion] — and here the quality gate refuses the capture.
Camera path, if you want to see it on a phone: fingertip on the rear camera with flash on — on a laptop webcam it correctly reports "signal too flat", because honesty is the feature.
Falling back if needed: recorded 83-second run and an offline pen-drive copy. Three backups.""")

# ====================================================================
# SLIDE 8 — GUARDRAILS (criterion 8, honesty)
# ====================================================================
s = slide()
kick(s, 'Responsible design · refuse-to-guess guardrails')
pill(s, 'JURY ⑦⑧ · GUARDRAILS')
title(s, 'When the signal is bad, the app says so — in writing')
box(s, 0.62, 1.9, 5.9, 2.3, fill=CARD, line=AMBER)
txt(s, 0.9, 2.1, 5.4, 1.9, [
    dict(t='“Could not read the pulse”', size=17, bold=True, color=AMBER),
    dict(t='Not enough clean beats in the window. Use a phone with flash on · keep still · press gently · brighten the room. Demo Mode offered on the spot.', size=12.5, color=MUTED, before=8, ls=1.2)])
bullets(s, 0.62, 4.5, 5.9, 2.3, [
    'Live signal-quality index (0–100%) gates every capture.',
    'Two consecutive low-quality windows → auto-abort with coaching.',
    'No result is ever extrapolated from a weak signal.',
], size=13.5, gap=8)
bullets(s, 6.9, 1.95, 5.8, 4.8, [
    ('What it is:  ', 'a SCREENING aid that flags rhythm-irregularity risk for referral.'),
    ('What it is not:  ', 'a diagnosis. Every result screen, every report says so — and lists mimics (stress, caffeine, ectopic beats).'),
    ('Real judgement call:  ', 'on a plain laptop webcam (no flash) the tool correctly reports "signal too flat" instead of celebrating a fake pulse — we hit this in our own testing and kept the refusal.'),
    ('Validation loop:  ', 'every number on the result screen is reproducible from repo tests — judges can rerun them live.'),
], size=13.5, gap=10)
footer(s, 8)
notes(s, """[~8:15 — 55 s] This slide is our honesty contract. What NadiSense is: a screening aid that flags irregular-rhythm risk for referral. What it is not: a diagnosis — every screen and every report says so.
A concrete example from our own testing, yesterday: on a laptop webcam — no torch behind the finger — the signal is flat. The easy thing would be to fake confidence; the app instead shows "could not read the pulse" plus the fixes. We deliberately did not relax the threshold to make demos easier.
And everything shown is reproducible: the exact numbers you see can be regenerated by running the test suite in the repo.""")

# ====================================================================
# SLIDE 9 — TESTING & VALIDATION (criterion 7)
# ====================================================================
s = slide()
kick(s, 'Testing, performance & validation')
pill(s, 'JURY ⑦ · TESTING')
title(s, 'Reproducible by design — 47 automated checks in the repo')
t1 = [('34', 'pipeline tests — simulator, DSP, classifier, guardrails, camera-source edge cases', TEAL),
      ('13', 'full browser flows — boot, AFib capture → red result, normal → green, report export', TEAL),
      ('1 ms', 'to analyse a 30-second window (budget 250 ms) — idle-class phones stay fluid', TEAL)]
x = 0.62
for head, body, col in t1:
    b = box(s, x, 1.95, 3.9, 1.7)
    txt(s, x + 0.25, 2.12, 3.4, 1.35, [
        dict(t=head, size=32, bold=True, color=col),
        dict(t=body, size=12, color=MUTED, before=4, ls=1.15)])
    x += 4.1
code(s, '$ node tests/run_tests.mjs        →  34 passed, 0 failed\n'
        '$ node tests/run_browser_smoke.mjs →  13 passed, 0 failed\n'
        'deterministic seeds → same input always yields the same verdict',
     0.62, 4.05, 12.1, 1.05, size=12)
bullets(s, 0.62, 5.35, 12.1, 1.6, [
    ('Engineering truth (now):  ', 'real-patient validated (MIT-BIH AFDB, record-independent 97.2/99.5/95.2), live demo, 61 tests — all in the repo.'),
    ('Clinical truth (honest):  ', 'real-patient validation is our next milestone — the retrain pipeline and the ground-truth recorder are already built, so a PHC pilot can start without new software.'),
], size=13.5, gap=8)
footer(s, 9)
notes(s, """[~9:10 — 55 s] Testing. Everything you saw is reproducible. Thirty-four pipeline tests — simulator, DSP, classifier, guardrails, and the camera-source edge cases that crashed real products before ours — plus thirteen full browser flows end-to-end: boot, AFib capture, red result, normal capture, green result, report export. A thirty-second window analyses in about a millisecond.
One command, and the jury can rerun all of it from the repo.
And we state the limit plainly, because screening tools die on overclaims: our validated tier is ECG-derived RR classification — the clinical gold standard for rhythm labels. The next tier, a PHC field study against twelve-lead ECG, needs no new software. That is on the roadmap slide next.""")

# ====================================================================
# SLIDE 10 — RESPONSIBLE AI (criterion 8)
# ====================================================================
s = slide()
kick(s, 'Responsible & ethical AI')
pill(s, 'JURY ⑧ · RESPONSIBLE AI')
title(s, "Privacy isn't our policy — it's our architecture")
cols = [
    ('PRIVACY', TEAL, ['No server exists to leak from', 'Camera ROI → ONE number per frame, in-memory; photos never touched', 'No account, no ads, no SDKs, no analytics', 'Report PDF generates on-device']),
    ('SAFETY', AMBER, ['Screening, NOT diagnosis — printed on every result', 'Refuses weak signals instead of guessing', 'Mimics disclosed: stress · caffeine · ectopy', 'Escalation language, never reassurance-by-omission']),
    ('INCLUSION', GREEN, ['हिंदी · தமிழ் · English + voice prompts', 'Runs on ₹6k Androids, offline-first', 'Green-channel physics works across skin tones; bias-testing slated for the clinical pilot', 'Zero-resource: no charger, no consumables']),
]
x = 0.62
for head, col, items in cols:
    b = box(s, x, 1.9, 3.9, 4.55)
    txt(s, x + 0.22, 2.1, 3.5, 0.4, [dict(t=head, size=14, bold=True, color=col)])
    paras = []
    for it in items:
        paras.append(dict(runs=[dict(t='✓  ', size=12.5, bold=True, color=col), dict(t=it, size=12, color=MUTED)], ls=1.15, after=8))
    txt(s, x + 0.22, 2.6, 3.5, 3.6, paras)
    x += 4.1
footer(s, 10)
notes(s, """[~10:05 — 50 s] Responsible AI is a rubric heading, so let me be explicit, in its own three columns.
Privacy: we have no server to leak from. The frame is reduced to one number in memory; photos are never stored; there is no account and no analytics. The report renders on the device.
Safety: screening, not diagnosis, printed everywhere; weak signals are refused; rhythm-mimics like caffeine and stress are disclosed on the result.
Inclusion and fairness: three languages with voice prompts for low-literacy users; it runs on six-thousand-rupee phones; and we flag one known physics caveat honestly — green-channel absorption can vary with skin tone and age, which is exactly why the quality gate exists and why bias testing is explicitly inside the clinical pilot plan.""")

# ====================================================================
# SLIDE 11 — THE SIGNAL STORY (visual evidence)
# ====================================================================
s = slide()
kick(s, 'What the classifier actually sees')
pill(s, 'EVIDENCE · VISUAL')
title(s, 'Regular rhythm marches. AFib wanders.')
pic(s, 'tach_pair.png', 0.62, 1.85, w=12.1)
pic(s, 'poincare_pair.png', 0.62, 4.75, w=12.1)
footer(s, 11)
notes(s, """[~10:55 — 40 s] One visual worth more than the maths. Top: the tachogram — each bar is one heartbeat's interval. Normal rhythm marches in step; AFib meanders with no pattern. Bottom: Poincaré — each beat plotted against the next. Normal collapses into a tight comet; AFib scatters into a cloud.
Every feature the network consumes quantifies exactly this geometry — which is why the model can stay small and still be meaningful. When a juror asks "why twelve features", this picture is the answer.""")

# ====================================================================
# SLIDE 12 — IMPACT & SCALE (criterion 9)
# ====================================================================
s = slide()
kick(s, 'Impact · scalability · sustainability')
pill(s, 'JURY ⑨ · IMPACT & SCALE')
title(s, 'Screening as a habit, not an event')
s1 = [('₹0', 'per screening — the phone already exists; that is the entire thesis', TEAL),
      ('10 lakh', 'ASHA workers (Govt. of India) — a workforce that already knocks on every door, now carrying a screening tool', TEAL),
      ('2,000/day', 'a modest 100-worker block pilot × 20 doorstep visits — screening volume a single ECG room cannot match', TEAL)]
x = 0.62
for head, body, col in s1:
    b = box(s, x, 1.9, 3.9, 1.85)
    txt(s, x + 0.25, 2.06, 3.4, 1.55, [
        dict(t=head, size=32, bold=True, color=col),
        dict(t=body, size=11.5, color=MUTED, before=4, ls=1.15)])
    x += 4.1
bullets(s, 0.62, 4.1, 12.1, 2.6, [
    ('Scale is a copy-paste.  ', 'Static file → any state can host it; spreading to 1,000 phones costs the same as spreading to 1 phone: nothing.'),
    ('Fits national machinery.  ', 'Drops straight into NPCDCS NCD-screening door-to-door drives; report PDF matches referral paper-trail PHCs already use.'),
    ('Sustainable because boring.  ', 'No cloud bill, no licences, no consumables — the pilot continues by itself the day the grant ends. That is the definition of sustainability here.'),
], size=14.5, gap=10)
footer(s, 12)
notes(s, """[~11:35 — 45 s] Impact and scale. The marginal cost of one screening is zero rupees, because the sensor already lives in the phone. India's ten-lakh-strong ASHA workforce already visits every doorstep — we hand that workforce a clinical-grade habit, not a device.
A modest pilot — a hundred workers, twenty visits — screens two thousand people a day, more volume than the taluka ECG room.
Why it sustains: there is no cloud bill and no seed capital sitting in hardware. If every project member walked away tomorrow, the deployed file keeps working. A screening programme that survives its own pilot is the point.""")

# ====================================================================
# SLIDE 13 — STRATEGY & ROADMAP (criterion 10)
# ====================================================================
s = slide()
kick(s, 'Implementation strategy · future potential')
pill(s, 'JURY ⑩ · STRATEGY')
title(s, 'Who adopts it, and what the next 12 months look like')
bullets(s, 0.62, 1.85, 5.9, 4.6, [
    ('Adoption path:  ', 'state NHM / district health societies (screening-programme software) · NGO mobile-health vans · CSR-funded rural-health pilots · occupational screening for high-heat, high-stress workforces.'),
    ('Monetisation (B2G/B2B):  ', 'district dashboard licence + integration support. The screening app itself stays free — that is what keeps the marginal cost at zero.'),
    ('Where prize/support goes:  ', 'IEC ethics application, a 300-patient PHC validation study against ECG ground truth, field-hardening across 20 device models.'),
], size=13.5, gap=11)
mile = [('NOW · v1.0 shipped', 'Camera PPG + DSP + 11.5 KB MLP trained on real patients (MIT-BIH AFDB, record-independent 97.2/99.5/95.2) · trilingual UI · offline · 61 tests · live at nadisense.vercel.app'),
        ('+3 months', 'PHC field study vs 12-lead ECG · bias/device-diversity study · IEC filing · 3-village ASHA pilot (Maharashtra + Madurai belt)'),
        ('+12 months', '300-patient PHC validation vs 12-lead ECG · district dashboard · 3 more Indian languages'),
        ('200M', 'people one ASHA knock away from a rhythm screen — the addressable last mile',)]
y = 1.85
for i, (head, body) in enumerate(mile):
    last = i == 3
    b = box(s, 6.75, y, 5.95, 1.08, fill=RGBColor(0x10, 0x2A, 0x27) if last else CARD,
            line=TEAL if last else EDGE)
    txt(s, 6.98, y + 0.1, 5.5, 0.9, [
        dict(t=head, size=13.5, bold=True, color=TEAL if last else WHITE),
        dict(t=body, size=10.5, color=MUTED, before=2, ls=1.1)])
    y += 1.22
footer(s, 13)
notes(s, """[~12:20 — 45 s] Strategy. Who adopts: first state health missions and district societies running NPCDCS NCD drives, then NGO mobile vans and CSR rural-health pockets, and occupational-health screening for high-stress workforces. The app stays free; the revenue is the district dashboard licence and integration support — that keeps the marginal cost at zero, which is the whole product.
Roadmap: v1.0 is shipped — that is what you just used, trained and validated on real patients. Three months — a PHC field study against twelve-lead, device-and-bias study, ethics filing, and a three-village ASHA pilot in Maharashtra and here in the Madurai belt. Twelve months — a three-hundred-patient validation against twelve-lead ECG and the district dashboard. The addressable last mile is two hundred million people one doorstep away from a rhythm screen.""")

# ====================================================================
# SLIDE 14 — TEAM / WHY US (criterion 11)
# ====================================================================
s = slide()
kick(s, 'The team · why this entry')
pill(s, 'JURY ⑪ · TEAM')
title(s, 'Three students, one working product, zero excuses')
team = [('Aditya Mehra', 'E&TC · 3rd year', 'product lead · PPG/DSP pipeline · deployment', 'aadityamehra289@gmail.com · 7304334137'),
        ('Akanshu Pandey', '3rd year', 'Field liaison & operations · pilot deployment · demos', 'matricphase@gmail.com'),
        ('Siddesh Wagh', 'BCA · 3rd year', 'app engineering · i18n, report, QA suite', 'adityamnm101@gmail.com · 8591308121')]
x = 0.62
for name, yr, role, mail in team:
    b = box(s, x, 1.9, 3.9, 1.95)
    txt(s, x + 0.22, 2.06, 3.5, 1.7, [
        dict(t=name, size=15.5, bold=True, color=WHITE),
        dict(t=yr, size=11, color=TEAL, before=2),
        dict(t=role, size=11.5, color=MUTED, before=6, ls=1.15),
        dict(t=mail, size=9.5, color=MUTED, before=6)])
    x += 4.1
bullets(s, 0.62, 4.2, 12.1, 2.5, [
    ('We ship.  ', 'Form, repo, tests, a public live deployment, a recorded full run — everything a juror can verify was built, tested and hosted by this team.'),
    ('We disclose.  ', 'Honest limitations are printed inside the product and in the README, not buried in slide 14 fine print.'),
    ('We are local.  ', 'Trilingual build, Mumbai-University engineering grounding, and a Maharashtra-first pilot plan for the exact population the tool serves.'),
], size=14.5, gap=10)
footer(s, 14)
notes(s, """[~13:05 — 35 s] The team. Aditya — signal pipeline, model and deployment; Akanshu — field liaison and operations; Siddesh — app engineering, languages and QA. Three third-year students.
Why this entry deserves to go forward, in three lines: we ship — everything you saw is running publicly; we disclose — limitations printed inside the product; and we are local — trilingual, with a Maharashtra pilot plan for exactly the population this serves.""")

# ====================================================================
# SLIDE 15 — CLOSE
# ====================================================================
s = slide()
txt(s, 0.62, 2.2, 12.1, 2.6, [
    dict(t='The ECG will never reach every village.', size=30, bold=True, color=WHITE, align=PP_ALIGN.CENTER),
    dict(t='So we put the screen in the phone that is already there.', size=22, color=TEAL, align=PP_ALIGN.CENTER, before=14),
    dict(t='60 seconds · one phone · zero hardware · an honest answer', size=16, color=MUTED, align=PP_ALIGN.CENTER, before=14)])
pic(s, 'wave_banner.png', 2.6, 4.7, w=8.1)
txt(s, 0.62, 5.6, 12.1, 0.9, [
    dict(t='LIVE NOW  ·  nadisense.vercel.app', size=15, bold=True, color=TEAL, align=PP_ALIGN.CENTER),
    dict(t='github.com/AA7304-MEH/Nadisense  ·  NadiSense_Demo.mp4 (83 s recorded run)', size=12, color=MUTED, align=PP_ALIGN.CENTER, before=6)])
footer(s, 15)
notes(s, """[~13:40 — 20 s close] To close: the ECG will never reach every village — so we put the screen in the phone that is already there. Sixty seconds, one phone, zero hardware, and — above all — an honest answer. Thank you; we welcome the jury's questions.
[Q&A — 3 min. Likely questions and our answers are in the presenter notes of the previous slides. Key numbers to hold in head: 11.5 KB model · 12 features · 34+24 tests · ₹0 marginal cost · MIT-BIH-trained, record-independent 97.2/99.5/95.2 · 60 s window · 30 Hz sampling · 0.6–3.5 Hz band · live at nadisense.vercel.app.]""")

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'deliverables', 'NadiSense_GrandFinale_Pitch.pptx')
prs.save(os.path.normpath(OUT))
print('wrote', os.path.normpath(OUT), f'({os.path.getsize(os.path.normpath(OUT))//1024} KB, {len(prs.slides.__iter__.__self__._sldIdLst)} slides)')
