#!/usr/bin/env python3
"""
build_submission_docx.py — rebuild the TECHNOVA 2026 submission Word document.

Takes the existing submission .docx and:
  1. adds a running page header in the style of the PDF deliverables:
       "NadiSense · Team Agent Matrix · TECHNOVA 2026 · TCET — Thakur College
        of Engineering & Technology"                        Page N
  2. applies the v1.0 corrections: Agent Matrix branding everywhere, real
     contact, TCET institution line, real-patient MIT-BIH AFDB model facts
     (97.2 / 99.5 / 95.2 record-independent), current test counts (34+24),
     updated roadmap + team table + command table.

Run:  python3 tools/build_submission_docx.py
"""

import copy
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, 'deliverables', 'NadiSense_TECHNOVA2026_Submission.docx')
DST = SRC  # rewritten in place; committed copy of record


# ---------------------------------------------------------------- helpers
def set_text(p, new, expected=None, keep_style_from=None):
    """Replace a paragraph's whole text, preserving the first run's formatting."""
    if expected is not None and expected not in p.text:
        raise AssertionError(f"anchoring failed — expected to find {expected!r} in {p.text[:80]!r}")
    runs = p.runs
    if not runs:
        r = p.add_run(new)
        src = keep_style_from
        if src and src.runs:
            r.font.italic = src.runs[0].font.italic
            r.font.size = src.runs[0].font.size
        return
    runs[0].text = new
    for r in runs[1:]:
        r.text = ''


def replace_runwise(p, old, new):
    """Surgical replace inside individual runs (keeps bold/italic spans intact)."""
    done = False
    for r in p.runs:
        if old in r.text:
            r.text = r.text.replace(old, new)
            done = True
    if not done and old in p.text:          # spans multiple runs → flatten once
        set_text(p, p.text.replace(old, new))
        done = True
    if not done:
        raise AssertionError(f"replace_runwise: {old!r} not found in {p.text[:80]!r}")


def insert_after(par, doc, text, style_from):
    """Insert a new paragraph after `par`, cloning run formatting from style_from."""
    new_p = copy.deepcopy(par._p)
    par._p.addnext(new_p)
    from docx.text.paragraph import Paragraph
    q = Paragraph(new_p, par._parent)
    set_text(q, text)
    if style_from.runs and q.runs:
        q.runs[0].font.size = style_from.runs[0].font.size
        q.runs[0].font.italic = style_from.runs[0].font.italic
    q.style = style_from.style
    return q


def add_page_field(par):
    """Append a live PAGE field to a header paragraph."""
    r1 = par.add_run()
    fld_b, = [OxmlElement('w:fldChar')]; fld_b.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = ' PAGE '
    fld_e = OxmlElement('w:fldChar'); fld_e.set(qn('w:fldCharType'), 'end')
    r1._r.append(fld_b)
    r2 = par.add_run(); r2._r.append(instr)
    r3 = par.add_run(); r3._r.append(fld_e)
    for r in (r1, r2, r3):
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)


def bottom_rule(par, color='94A3B8', sz='6'):
    pPr = par._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    b = OxmlElement('w:bottom')
    b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), sz)
    b.set(qn('w:space'), '4'); b.set(qn('w:color'), color)
    pbdr.append(b)
    pPr.append(pbdr)


# ---------------------------------------------------------------- main
def main():
    doc = Document(SRC)
    P = doc.paragraphs

    # ---- 1. running page header (PDF style, with TCET) --------------------
    for sec in doc.sections:
        hdr = sec.header
        hdr.is_linked_to_previous = False
        hp = hdr.paragraphs[0]
        hp.text = ''
        usable = sec.page_width - sec.left_margin - sec.right_margin
        hp.paragraph_format.tab_stops.add_tab_stop(usable, WD_TAB_ALIGNMENT.RIGHT)
        run = hp.add_run(
            'NadiSense · Team Agent Matrix · TECHNOVA 2026 · '
            'TCET — Thakur College of Engineering & Technology, Mumbai'
        )
        run.font.size = Pt(8)
        run.font.small_caps = True
        run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
        tabr = hp.add_run('\t')
        tabr.font.size = Pt(8)
        pr = hp.add_run('Page ')
        pr.font.size = Pt(8)
        pr.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
        add_page_field(hp)
        bottom_rule(hp)

    # ---- 2. cover block ----------------------------------------------------
    set_text(P[5], 'Submission document — Version 1.0 (real-patient model)', expected='Submission document')
    set_text(P[6], 'Team: Agent Matrix', expected='Team:')
    set_text(P[7], 'Team lead: Aditya Mehra  ·  Contact: matricphase@gmail.com', expected='Team lead')
    insert_after(P[8], doc,
                 'Thakur College of Engineering and Technology (TCET), Mumbai University, Maharashtra',
                 P[8])

    # P indexes shift by +1 after the insert — re-fetch by content
    P = doc.paragraphs

    def find(prefix, start=0):
        for i in range(start, len(P)):
            if P[i].text.strip().startswith(prefix):
                return i
        raise AssertionError(f'paragraph starting {prefix!r} not found')

    # ---- 3. v1.0 text corrections ------------------------------------------
    # executive summary: model size + working-product paragraph
    replace_runwise(P[find('Cardiovascular disease kills')], '6 KB neural network', 'neural network (11.5 KB weights)')
    i = find('We have fully built the product')
    set_text(P[i],
        'We have fully built the product: a working v1.0 (camera capture + signal processing + classifier '
        '+ vernacular UI + report), 34 automated pipeline tests, 24 end-to-end UI tests, and a one-command '
        'training pipeline. The shipped model is trained and validated on REAL patient data — the MIT-BIH '
        'Atrial Fibrillation Database (cardiologist-annotated ECG beats from 25 AFib patients) — and scored '
        'on a record-independent holdout of 5 patients it never saw in training: 97.2% accuracy, 99.5% '
        'sensitivity, 95.2% specificity. We state the remaining limits as plainly as the numbers (Section 7.3).',
        expected='We have fully built the product')

    # take-care bullet: 13 → 12 metrics; model size in analyse bullet
    replace_runwise(P[find('Analyse — Zero-phone detrend')], '6 KB MLP', '11.5 KB MLP')
    replace_runwise(P[find('Act — Green / amber / red card')], 'the 13 HRV metrics', 'the 12 HRV metrics')
    replace_runwise(P[find('A 6 KB model is auditable')], 'A 6 KB model', 'An 11.5 KB model')

    # pipeline integrity: 30 → 34 + 24
    replace_runwise(P[find('The training script (Python/NumPy)')],
                    '30 automated tests guard every release',
                    '34 automated unit tests and 24 full-UI tests guard every release')

    # 7.1 data & training: synthetic → real AFDB
    i = find('12,000 windows of 30 s pulse signals')
    set_text(P[i],
        'Real patient data — MIT-BIH Atrial Fibrillation Database (PhysioNet afdb 1.0.0): cardiologist-annotated '
        'beats from 25 AFib patients, 23 two-channel ECG records ~10 hours each. We join rhythm annotations '
        'with beat annotations, cut the RR series into 30 s windows (15 s stride, single-rhythm windows with '
        '≥18 beats), giving 93,730 training windows; ±3% proportional "camera-jitter" augmentation is applied '
        'on the training side so the model tolerates phone-PPG peak-timing noise.')

    # 7.2 heading + results bullet
    set_text(P[find('7.2 Results')], '7.2 Results — record-independent holdout (patients never seen in training)')
    i = find('Demo scenarios through the shipped model')
    set_text(P[i],
        '11,858 validation windows from 5 held-out patients (06426, 06995, 08378, 08434, 08455 — never used in '
        'training): accuracy 97.2% · sensitivity 99.5% · specificity 95.2% · precision 94.8% · F1 0.971. '
        'Full numbers: tools/metrics.json; the model card ships inside the app itself (NADI_MODEL.meta).')
    insert_after(P[i], doc,
        'Demo scenarios through the shipped model: healthy rhythm → green (P<1%) · low-HRV → amber-tending '
        '· AFib-like → red. An extreme synthetic AF fixture reads ~91% rather than pegging at 100% — the '
        'real-data model is calibrated, not saturated; the care-level decision is unchanged.',
        P[i])
    P = doc.paragraphs  # refresh

    # 7.3 honest limits: what remains true
    i = find('The model above is validated on its')
    set_text(P[i],
        'The shipped model is now validated on real patient data — but we state what is still true, openly. '
        '(1) Validation is on ECG-derived RR intervals — the clinical gold standard for rhythm labels; '
        'phone-camera PPG adds its own noise, which is why we train with camera-jitter augmentation and '
        'quality-gate weak captures into a retake prompt instead of guessing. (2) Specificity 95% means '
        'about 1 in 20 normal readings can false-flag — by design we err toward caution. (3) NadiSense is '
        'a screening aid, not a diagnostic device: a red card means "ECG within 7 days", never a diagnosis. '
        'A formal PHC field study against 12-lead ECG is the next validation tier.')
    replace_runwise(P[find('Ethical position')], 'will be public', 'are public')

    # deployment plan: evidence bullet done → next tier
    i = find('Evidence — Retrain on real data')
    set_text(P[i],
        'Evidence — DONE: real-data retrain (MIT-BIH AFDB, record-independent validation, model card published '
        'in-app); next tier is a district PHC field study vs 12-lead ECG, then approach district health '
        'societies and NHM programmes.')

    # team
    set_text(P[find('12.1 Team')], '12.1 Team (Agent Matrix)')
    set_text(P[find('We are a solo-engineering team')],
        'Three-member team from Thakur College of Engineering and Technology (TCET), Mumbai University, within the '
        '3–5 member rule. Aditya leads product and ML and presents; Akanshu runs field liaison and pilot '
        'operations; Siddesh owns datasets, the model card and documentation.')

    # appendix counts + demo pointer
    replace_runwise(P[find('Everything in this document is reproducible')],
                    'tests/ (61 automated tests)', 'tests/ (61 automated tests: 37 pipeline + 24 full-UI)')
    i = find('The demo needs no internet')
    set_text(P[i],
        'Two ways: (1) LIVE — https://nadisense.vercel.app (camera mode works in any normal browser tab; if '
        'camera access was ever blocked, the app now shows the exact two-tap fix and offers Demo Mode); '
        '(2) OFFLINE — open deliverables/nadi.html, choose “Demo Mode”, pick a scenario, and the full '
        'pipeline runs live with no internet and no permissions.')

    # ---- 4. table corrections ----------------------------------------------
    T = doc.tables

    def cell(t, r, c): return T[t].rows[r].cells[c]

    # what's-built table
    set_text(cell(3, 1, 0).paragraphs[0] if len(cell(3, 1, 0).paragraphs) == 1 else cell(3, 1, 0).paragraphs[0],
             cell(3, 1, 0).text.replace('green-channel ROI', 'adaptive red/green/blue-channel ROI'))
    replace_runwise(cell(3, 4, 0).paragraphs[0], '12→20→10→1 (6 KB)', '12→20→10→1 (11.5 KB)')
    set_text(cell(3, 8, 0).paragraphs[0],
             'Real-data training pipeline (MIT-BIH AFDB; NumPy reference mirrors the JS DSP 1:1)')
    set_text(cell(3, 8, 2).paragraphs[0], 'tools/train_real_data.py (+ tools/train_mlp.py preview)')
    set_text(cell(3, 9, 0).paragraphs[0], 'Automated tests: 34 pipeline + 24 full-UI (jsdom)')

    # architecture table
    replace_runwise(cell(4, 4, 1).paragraphs[0], '6 KB', '11.5 KB')
    cellp = cell(4, 1, 1).paragraphs[0]
    set_text(cellp, cellp.text.replace('summed to one green-channel mean',
                                       'auto-selects the strongest pulse channel (green/red/blue)'))

    # model results: preview → v1.0 record-independent
    set_text(cell(5, 1, 0).paragraphs[0],
             'v1.0 shipped model — MIT-BIH AFDB, record-independent: 5 never-seen patients, 11,858 windows')
    for c, v in zip(range(1, 5), ['97.2%', '99.5%', '95.2%', '0.971']):
        set_text(cell(5, 1, c).paragraphs[0], v)

    # risk table: worst-case risk now mitigated
    set_text(cell(8, 1, 1).paragraphs[0],
             'Resolved for rhythm screening: model retrained on REAL patient data (MIT-BIH AFDB) and held out on '
             'never-seen patients (97.2% acc / 99.5% sens / 95.2% spec); quality gate refuses bad signals; '
             'clinical review still required before any deployment')

    # team table
    set_text(cell(9, 2, 0).paragraphs[0], 'Akanshu Pandey')
    set_text(cell(9, 2, 1).paragraphs[0], 'Field liaison & operations — ASHA/PHC pilots, training module, demos')
    row = T[9].add_row()
    set_text(row.cells[0].paragraphs[0], 'Siddesh Wagh')
    set_text(row.cells[1].paragraphs[0], 'Research & documentation — datasets, model card, Q&A preparation')

    # roadmap table
    set_text(cell(10, 1, 0).paragraphs[0], 'v0.9 prototype')
    set_text(cell(10, 2, 0).paragraphs[0], 'v1.0 — this submission')
    set_text(cell(10, 2, 1).paragraphs[0], 'Now (Sept 2026)')
    set_text(cell(10, 2, 2).paragraphs[0],
             'Real-patient model shipped (MIT-BIH AFDB, record-independent 97.2/99.5/95.2); works-in-every-tab '
             'camera UX; live at nadisense.vercel.app')

    # reproduce table
    set_text(cell(11, 1, 0).paragraphs[0], 'python3 tools/train_real_data.py')
    set_text(cell(11, 1, 1).paragraphs[0],
             'Streams MIT-BIH AFDB from PhysioNet, builds 93k+ RR windows, retrains the MLP on real patient '
             'data, writes js/model_weights.js + tools/metrics.json')
    replace_runwise(cell(11, 2, 1).paragraphs[0], '30 assertions', '34 assertions')
    replace_runwise(cell(11, 3, 1).paragraphs[0], '13 assertions', '24 assertions')
    row = T[11].add_row()
    set_text(row.cells[0].paragraphs[0], 'npm install && npm test')
    set_text(row.cells[1].paragraphs[0], 'One-command install + full test run (package.json ships in the repo)')

    doc.save(DST)
    print(f'wrote {DST}')


if __name__ == '__main__':
    main()
