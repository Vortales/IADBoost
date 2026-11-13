# -*- coding: utf-8 -*-
"""Генератор законопроектов по образцу ACT. 260.

Клонирует оформление шаблона и заменяет содержательную часть.

Разметка текста:
  [[R]]…[[/R]] — действующий текст (красная заливка);
  [[G]]…[[/G]] — новая редакция (зелёная заливка);
  [[B]]…[[/B]] — полужирный (названия законов и кодексов).

Шрифт всего документа приводится к Times New Roman.
"""
import copy
import os
import re
import shutil
import zipfile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.table import _Cell

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "Законопроекты", "_ШАБЛОН",
                        "ACT.260.Закон об охоте и рыбалке (лицензия FISHING).docx")
RED, GREEN = "F4CCCC", "D9EAD3"
FONT = "Times New Roman"
TOKEN = re.compile(r"\[\[(/?)(R|G|B)\]\]")


def parse_line(text):
    """Делит строку на сегменты (текст, заливка, полужирный)."""
    segs, pos, fill, bold = [], 0, None, False
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            segs.append((text[pos:m.start()], fill, bold))
        closing, tag = m.group(1) == "/", m.group(2)
        if tag == "B":
            bold = not closing
        else:
            fill = None if closing else (RED if tag == "R" else GREEN)
        pos = m.end()
    if pos < len(text):
        segs.append((text[pos:], fill, bold))
    return segs


def add_run(p, text, fill=None, bold=False, size=12):
    r = p.add_run(text)
    r.font.name = FONT
    rFonts = r._r.rPr.find(qn("w:rFonts"))
    for attr in ("w:eastAsia", "w:hAnsi", "w:cs"):
        rFonts.set(qn(attr), FONT)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    rPr = r._r.get_or_add_rPr()
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(int(size * 2)))
    rPr.append(szCs)
    if fill:
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill)
        rPr.append(shd)


def _lines(text):
    """Разбивает размеченный текст на строки, сохраняя (текст, заливка, жирный)."""
    lines = [[]]
    for seg, fill, bold in parse_line(text):
        for k, part in enumerate(seg.split("\n")):
            if k:
                lines.append([])
            if part:
                lines[-1].append((part, fill, bold))
    return lines


def fill_cell(cell, text, size=12):
    for p in list(cell.paragraphs):
        p._p.getparent().remove(p._p)
    for line in _lines(text):
        p = cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.widow_control = False
        p.paragraph_format.line_spacing = 1.0
        for seg, fill, bold in line:
            add_run(p, seg, fill, bold, size)


def set_par_rich(p, text, size=None, bold=False, keep_alignment=True):
    """Заменяет содержимое абзаца размеченным текстом.

    Дополнительные строки (\\n) добавляются отдельными абзацами с тем же
    форматированием. bold=True — весь текст полужирный, если не снят [[/B]].
    """
    if size is None:
        size = p.runs[0].font.size.pt if p.runs and p.runs[0].font.size else 12
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    lines = _lines(text)
    target = p
    for i, line in enumerate(lines):
        if i:
            new_p = copy.deepcopy(p._p)
            target._p.addnext(new_p)
            from docx.text.paragraph import Paragraph
            target = Paragraph(new_p, p._parent)
        for seg, fill, b in line:
            add_run(target, seg, fill, bold or b, size)
    return target


def normalize_fonts(doc):
    """Times New Roman для всего документа: текст, знаки абзацев, колонтитулы."""
    def fix_root(root):
        for el in root.iter(qn("w:rFonts")):
            for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                el.set(qn(attr), FONT)

    fix_root(doc.element.body)
    fix_root(doc.styles.element)
    for s in doc.sections:
        for part in (s.header, s.footer, s.first_page_header, s.first_page_footer,
                     s.even_page_header, s.even_page_footer):
            try:
                fix_root(part._element)
            except Exception:
                pass


def clean_font_table(path):
    """Убирает из fontTable.xml шрифты, которые больше не используются."""
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/fontTable.xml":
                text = data.decode("utf-8")
                text = re.sub(r'<w:font w:name="Century Schoolbook">.*?</w:font>', "", text, flags=re.S)
                data = text.encode("utf-8")
            dst.writestr(item, data)
    shutil.move(tmp, path)


def build(bill, outdir="."):
    doc = Document(TEMPLATE)
    ps = doc.paragraphs
    set_par_rich(ps[0], f"ACT. {bill['num']}", bold=True)
    set_par_rich(ps[3], bill["date"])
    set_par_rich(ps[6], bill["subtitle"])
    set_par_rich(ps[9], bill["section1"])
    set_par_rich(ps[10], bill["section2"], bold=True)

    tbl = doc.tables[0]
    template_tr = copy.deepcopy(tbl.rows[1]._tr)
    for row in list(tbl.rows)[1:]:
        tbl._tbl.remove(row._tr)

    for left, right in bill["rows"]:
        tr = copy.deepcopy(template_tr)
        tbl._tbl.append(tr)
        cells = tr.findall(qn("w:tc"))
        fill_cell(_Cell(cells[0], tbl), left)
        fill_cell(_Cell(cells[1], tbl), right)

    normalize_fonts(doc)
    path = f"{outdir}/{bill['file']}"
    doc.save(path)
    clean_font_table(path)
    print("OK", bill["file"])
