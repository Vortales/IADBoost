# -*- coding: utf-8 -*-
"""Итоги пленарного заседания Сената — официальное сообщение Спикера.

Собирается из образца заявления-инициативы (Book Antiqua, шапка Сената).
Итоги — из файла «Результаты сената.txt» (ссылки в документ не переносятся).
"""
import copy
import glob
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = glob.glob(os.path.join(ROOT, "*инициатива*(1).docx"))[0]
OUT = os.path.join(ROOT, "Сенат/Итоги пленарного заседания (09.11.2026)",
                   "Итоги пленарного заседания Сената — 09.11.2026.docx")

SUBTITLE = "официальное сообщение по итогам пленарного заседания Сената штата Сан-Андреас"

LEAD = ("Настоящим Председатель (Спикер) Сената штата Сан-Андреас Marcus Nomad объявляет "
        "итоги пленарного заседания Сената штата Сан-Андреас, состоявшегося 9 ноября 2026 года.")

COMMON = [
    "Заседание открыто и признано правомочным: на заседании присутствовало не менее половины "
    "действующих сенаторов (часть 1 статьи 9 Конституционного закона «О Сенате штата "
    "Сан-Андреас»).",

    "Общее число действующих сенаторов, определённое председательствующим перед началом "
    "голосований, — 14.",

    "Для принятия решения большинством голосов требовалось 8 голосов — число, превышающее "
    "половину общего числа действующих сенаторов (часть 5 статьи 80 Конституции штата "
    "Сан-Андреас).",

    "Заседание проведено под председательством Председателя (Спикера) Сената штата "
    "Сан-Андреас Marcus Nomad.",
]

ROWS = [
    ("Инициатива об избрании председателя и членов Центральной избирательной комиссии "
     "штата Сан-Андреас", "7", "6", "1", "Не принята"),
    ("Законопроект ACT. 277", "8", "3", "2", "Принят"),
    ("Законопроект ACT. 278", "9", "4", "1", "Принят"),
    ("Законопроект ACT. 279", "11", "2", "1", "Принят"),
    ("Законопроект ACT. 280", "11", "1", "2", "Принят"),
    ("Законопроект ACT. 281", "—", "—", "—", "Отозван"),
    ("Законопроект ACT. 282", "12", "0", "2", "Принят"),
    ("Законопроект ACT. 283", "7", "5", "1", "Не принят"),
    ("Законопроект ACT. 284", "11", "1", "1", "Принят"),
    ("Законопроект ACT. 285", "12", "0", "1", "Принят"),
]

DECISIONS = [
    "Приняты 7 законопроектов: ACT. 277, ACT. 278, ACT. 279, ACT. 280, ACT. 282, ACT. 284, "
    "ACT. 285.",

    "Не набрали необходимого числа голосов и считаются отклонёнными: инициатива об избрании "
    "председателя и членов Центральной избирательной комиссии штата Сан-Андреас (7 голосов "
    "«за» при необходимых 8) и законопроект ACT. 283 (7 голосов «за» при необходимых 8).",

    "Законопроект ACT. 281 отозван инициатором и на голосование не ставился.",

    "Результаты голосования по каждому вопросу определены по числу голосов «за», «против» и "
    "«воздержался» и занесены в протокол заседания.",
]

SENDING = [
    "Принятые законы в течение двух дней направляются в Федеральный Суд штата Сан-Андреас, а "
    "после получения его одобрения — Губернатору штата Сан-Андреас для подписания и "
    "обнародования (часть 3 статьи 80 Конституции штата Сан-Андреас).",

    "Направление принятых законов обеспечивает Председатель (Спикер) Сената штата Сан-Андреас.",
]

FINAL = [
    "Настоящие итоги являются официальным сообщением Председателя (Спикера) Сената штата "
    "Сан-Андреас и доводятся до сведения сенаторов, Губернатора штата Сан-Андреас и "
    "заинтересованных лиц.",

    "Итоги не заменяют протокол заседания: при расхождении применяются сведения протокола.",
]

SIGN = ["С уважением,", "Marcus Nomad", "Председатель (Спикер) Сената штата Сан-Андреас"]

HEAD = ["№", "Вопрос", "«За»", "«Против»", "«Воздержался»", "Решение"]
WIDTHS = [0.9, 6.9, 1.6, 1.8, 2.2, 2.3]


def with_text(proto, text):
    el = copy.deepcopy(proto)
    runs = el.findall(qn("w:r"))
    keep = None
    for r in runs:
        t = r.find(qn("w:t"))
        if t is not None and keep is None and (t.text or "").strip():
            keep = r
        else:
            el.remove(r)
    if keep is None:
        raise ValueError("в абзаце-образце нет текстового прогона")
    for child in list(keep):
        if child.tag not in (qn("w:rPr"), qn("w:t")):
            keep.remove(child)
    t = keep.find(qn("w:t"))
    t.text = text
    t.set(qn("xml:space"), "preserve")
    return el


def cell_borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "808080")
        borders.append(el)
    tcPr.append(borders)


def cell_shade(cell, color="EDEDED"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def style_cell(cell, text, bold=False, center=True, size=10.5):
    p = cell.paragraphs[0]
    for old in list(p.runs):          # пустой прогон от cell.text = ""
        old._r.getparent().remove(old._r)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(1)
    pf.space_after = Pt(1)
    pf.line_spacing = 1.0
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Book Antiqua"
    rpr = run._element.get_or_add_rPr()
    rpr.rFonts.set(qn("w:eastAsia"), "Book Antiqua")
    rpr.rFonts.set(qn("w:cs"), "Book Antiqua")
    cell_borders(cell)


def add_results_table(doc):
    t = doc.add_table(rows=1, cols=len(HEAD))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    for i, name in enumerate(HEAD):
        c = t.rows[0].cells[i]
        style_cell(c, name, bold=True)
        cell_shade(c)
        c.width = Cm(WIDTHS[i])
    for n, (q, za, pr, vo, res) in enumerate(ROWS, 1):
        cells = t.add_row().cells
        vals = [str(n), q, za, pr, vo, res]
        for i, v in enumerate(vals):
            style_cell(cells[i], v, bold=(i == 5 and v != "Принят"), center=(i != 1))
            cells[i].width = Cm(WIDTHS[i])
    return t


def main():
    doc = Document(SRC)
    ps = doc.paragraphs
    proto_body, proto_h1 = ps[5]._p, ps[12]._p
    proto_sign = [ps[24]._p, ps[25]._p, ps[26]._p]

    for p, txt in ((ps[1], "ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ"), (ps[2], SUBTITLE),
                   (ps[3], "9 ноября 2026 года, г. Лос-Сантос")):
        new = with_text(p._p, txt)
        p._p.addprevious(new)
        p._p.getparent().remove(p._p)

    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    for p in doc.paragraphs[4:]:      # начиная с обращения «Уважаемые сенаторы!»
        p._p.getparent().remove(p._p)

    def push(el):
        sect.addprevious(el)

    push(with_text(proto_body, LEAD))
    push(with_text(proto_h1, "ОБЩИЕ СВЕДЕНИЯ"))
    for t in COMMON:
        push(with_text(proto_body, t))
    push(with_text(proto_h1, "РЕЗУЛЬТАТЫ ГОЛОСОВАНИЯ"))
    push(with_text(proto_body, "Итоги голосования по вопросам повестки дня:"))
    add_results_table(doc)
    push(with_text(proto_h1, "РЕШЕНИЯ ЗАСЕДАНИЯ"))
    for t in DECISIONS:
        push(with_text(proto_body, t))
    push(with_text(proto_h1, "НАПРАВЛЕНИЕ ПРИНЯТЫХ ЗАКОНОВ"))
    for t in SENDING:
        push(with_text(proto_body, t))
    push(with_text(proto_h1, "ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ"))
    for t in FINAL:
        push(with_text(proto_body, t))
    for proto, t in zip(proto_sign, SIGN):
        push(with_text(proto, t))
    push(with_text(proto_sign[0], "9 ноября 2026 года"))

    for p in doc.sections[0].footer.paragraphs:
        for r in list(p.runs):
            if r._r.find(qn("w:drawing")) is not None and r._r.find(qn("w:t")) is None:
                r._r.getparent().remove(r._r)

    cp = doc.core_properties
    cp.author = "Marcus Nomad"
    cp.last_modified_by = "Marcus Nomad"
    cp.title = "Итоги пленарного заседания Сената штата Сан-Андреас"
    cp.subject = "Пленарное заседание 9 ноября 2026 года"
    doc.save(OUT)
    print("OK", OUT)


if __name__ == "__main__":
    main()
