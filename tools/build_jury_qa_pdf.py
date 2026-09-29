# build_jury_qa_pdf.py — FINALE_JURY_QA_Master.md -> polished multi-page PDF
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

TEAL = HexColor('#0F766E'); TEALD = HexColor('#115E59'); NAVY = HexColor('#0B1F3A')
INK = HexColor('#1E293B'); MUTED = HexColor('#64748B'); LINE = HexColor('#CBD5E1')
GOLD = HexColor('#B45309')

ROOT = '/home/user/matricphase-technova2026'
MD = f'{ROOT}/deliverables/FINALE_JURY_QA_Master.md'
OUT = f'{ROOT}/deliverables/FINALE_JURY_QA_Master.pdf'

def esc(t):
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = (t.replace('\u20b9', 'Rs ').replace('\u2192', '-&gt;').replace('\u2248', '~')
          .replace('\u00d7', 'x').replace('\u2026', '...').replace('\u2014', ' — ')
          .replace('\u2013', ' - ').replace('\u2018', "'").replace('\u2019', "'")
          .replace('\u201c', '"').replace('\u201d', '"').replace('\u2260', 'not equal,')
          .replace('\u2260,', '\u2260,'))
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\*(.+?)\*', r'<i>\1</i>', t)
    return t

TITLE = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=21, textColor=TEALD, alignment=TA_CENTER, spaceAfter=4)
SUB = ParagraphStyle('s', fontName='Helvetica', fontSize=9.5, textColor=MUTED, alignment=TA_CENTER, spaceAfter=3, leading=12)
SEC = ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=13.5, textColor=NAVY, spaceBefore=14, spaceAfter=4)
Q = ParagraphStyle('q', fontName='Helvetica-Bold', fontSize=10.5, textColor=NAVY, spaceBefore=7, spaceAfter=1, leading=13)
QT = ParagraphStyle('qt', fontName='Helvetica-Bold', fontSize=10.5, textColor=GOLD, spaceBefore=7, spaceAfter=1, leading=13)
A = ParagraphStyle('a', fontName='Helvetica', fontSize=9.8, textColor=INK, leftIndent=10, spaceAfter=3, leading=12.6)
NOTE = ParagraphStyle('n', fontName='Helvetica-Oblique', fontSize=8.4, textColor=GOLD, leftIndent=16, spaceAfter=3, leading=10.5)
ANCH = ParagraphStyle('anch', fontName='Helvetica-Bold', fontSize=9.2, textColor=NAVY, spaceAfter=3, leading=12.5)
HOW = ParagraphStyle('how', fontName='Helvetica-Oblique', fontSize=9, textColor=MUTED, alignment=TA_CENTER, spaceBefore=4, leading=12)

class Doc(SimpleDocTemplate):
    def afterPage(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(LINE); c.setLineWidth(0.5)
        c.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
        c.setFont('Helvetica', 7.5); c.setFillColor(MUTED)
        c.drawString(18 * mm, 10 * mm, 'NadiSense — Jury Q&A Master Brief · Team Agent Matrix · TECHNOVA 2026 Grand Finale')
        c.drawRightString(192 * mm, 10 * mm, f'Page {self.page}')
        c.restoreState()

doc = Doc(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=20 * mm,
          title='NadiSense — Jury Q&A Master (Every Angle)', author='Team Agent Matrix')

el = [Paragraph('NADISENSE', TITLE),
      Paragraph('JURY Q&amp;A MASTER BRIEF — EVERY ANGLE',
                ParagraphStyle('t2', parent=SEC, alignment=TA_CENTER, fontSize=14, spaceBefore=0)),
      Paragraph('Team Agent Matrix · TCET, Mumbai University · TECHNOVA 2026 National Grand Finale · 30 Sept 2026 · TSM Madurai', SUB),
      Paragraph('<b>How to use:</b> land every answer in one sentence first — expand only if the nod comes — then stop. '
                'Gold questions are traps: the trap is the tone, not the question.', HOW),
      Spacer(1, 4), HRFlowable(width='100%', thickness=1, color=TEAL), Spacer(1, 2)]

q_regex = re.compile(r'^\*\*([A-L]\d+\..+?)\*\*\s*(.*)$')
qa = 0
for ln in open(MD, encoding='utf-8').read().split('\n'):
    if ln.startswith('## SECTION'):
        el.append(Spacer(1, 6))
        el.append(Paragraph(esc(ln.replace('## SECTION', 'SECTION')), SEC))
        el.append(HRFlowable(width='100%', thickness=0.6, color=LINE))
    elif ln.startswith('## ANCHOR'):
        el.append(Spacer(1, 8))
        el.append(HRFlowable(width='100%', thickness=1, color=TEAL))
        el.append(Paragraph(esc(ln.replace('## ', '')), SEC))
    elif (m := q_regex.match(ln)):
        qa += 1
        head, note = m.group(1), m.group(2).replace('\u26a0', '').replace('*', '').strip(' .–-')
        block = [Paragraph(esc(head), QT if note else Q)]
        if note:
            block.append(Paragraph('TRAP: ' + esc(note), NOTE))
        el.append(KeepTogether(block))
    elif ln.strip().startswith('>'):
        body = esc(ln.strip()[1:].strip())
        if body:
            el.append(KeepTogether([Paragraph('&bull; ' + body, A)]))
    elif qa > 0 and ln.strip() and '·' in ln and not ln.startswith('#') and not ln.startswith('---'):
        el.append(Paragraph(esc(ln.strip()), ANCH))

doc.build(el)
print(f'wrote {OUT} ({qa} Q&A blocks)')
