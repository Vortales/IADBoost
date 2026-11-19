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
import posixpath
import re
import shutil
import zipfile

from docx import Document
from lxml import etree
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
        p.paragraph_format.widow_control = True
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
    """Удаляет неиспользуемые встроенные шрифты шаблона и их связи.

    В документе после normalize_fonts используется только Times New Roman.
    Не сохраняем чужие встроенные Century Schoolbook, Calibri и другие шрифты
    в каждом новом DOCX; возможное встраивание Times New Roman сохраняем.
    """
    tmp = path + ".tmp"
    table_name = "word/fontTable.xml"
    rels_name = "word/_rels/fontTable.xml.rels"
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    doc_rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        table = etree.fromstring(src.read(table_name))
        for font in list(table):
            if font.tag == qn("w:font") and font.get(qn("w:name")) != FONT:
                table.remove(font)
        used_ids = {el.get(f"{{{doc_rel_ns}}}id") for el in table.iter()
                    if el.get(f"{{{doc_rel_ns}}}id")}
        table_data = etree.tostring(table, encoding="UTF-8", xml_declaration=True, standalone=True)
        removed = set()
        rels_data = None
        if rels_name in src.namelist():
            rels = etree.fromstring(src.read(rels_name))
            for rel in list(rels):
                if (rel.tag == f"{{{rel_ns}}}Relationship"
                        and rel.get("Type", "").endswith("/font")
                        and rel.get("Id") not in used_ids):
                    target = posixpath.normpath(posixpath.join("word", rel.get("Target", "")))
                    if not target.startswith("word/fonts/"):
                        raise ValueError(f"Неожиданный путь встроенного шрифта: {target}")
                    removed.add(target)
                    rels.remove(rel)
            if len(rels):
                rels_data = etree.tostring(rels, encoding="UTF-8", xml_declaration=True, standalone=True)
        for item in src.infolist():
            if item.filename in removed:
                continue
            if item.filename == table_name:
                data = table_data
            elif item.filename == rels_name:
                if rels_data is None:
                    continue
                data = rels_data
            else:
                data = src.read(item.filename)
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

    keep_rows = set(bill.get("keep_rows_together", ()))
    for left, right in bill["rows"]:
        tr = copy.deepcopy(template_tr)
        # Короткую новую норму и явно указанные короткие строки держим целиком;
        # длинные сравнительные строки должны свободно переходить на следующую страницу.
        locator = left.split("\n", 2)[1] if keep_rows else None
        if ((left.endswith("В действующей редакции отсутствует.") and len(right) < 1200)
                or locator in keep_rows):
            tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        tbl._tbl.append(tr)
        cells = tr.findall(qn("w:tc"))
        cell_size = bill.get("table_font_size", 12)
        fill_cell(_Cell(cells[0], tbl), left, size=cell_size)
        fill_cell(_Cell(cells[1], tbl), right, size=cell_size)

    normalize_fonts(doc)
    if bill.get("clear_template_metadata"):
        # Шаблон содержит данные и даты своего автора, а не нового проекта.
        props = doc.core_properties
        props.author = ""
        props.last_modified_by = ""
        for local_name in ("created", "modified"):
            element = props._element.find(f"{{http://purl.org/dc/terms/}}{local_name}")
            if element is not None:
                props._element.remove(element)
    path = f"{outdir}/{bill['file']}"
    doc.save(path)
    clean_font_table(path)
    print("OK", bill["file"])
