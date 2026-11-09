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

LEAD = ("Настоящим объявляю итоги пленарного заседания Сената штата Сан-Андреас, "
        "состоявшегося 9 ноября 2026 года в городе Лос-Сантос.")

SUMMARY = "Все вопросы повестки дня приняты."

COMMON = [
    "Заседание открыто и признано правомочным: присутствовало не менее половины "
    "действующих сенаторов (часть 1 статьи 9 Конституционного закона «О Сенате штата "
    "Сан-Андреас»).",

    "Общее число действующих сенаторов - 14. Для принятия решения большинством голосов "
    "требовалось 8 голосов, то есть число, превышающее половину общего числа действующих "
    "сенаторов (часть 5 статьи 80 Конституции штата Сан-Андреас).",

    "Заседание проведено под председательством Председателя (Спикера) Сената штата "
    "Сан-Андреас Marcus Nomad.",
]

DECISIONS = [
    "Приняты все вынесенные на голосование законопроекты: ACT. 277, ACT. 278, ACT. 279, "
    "ACT. 280, ACT. 282, ACT. 283, ACT. 284 и ACT. 285.",

    "Принята инициатива об избрании председателя и членов Центральной избирательной "
    "комиссии штата Сан-Андреас.",

    "Отозван законопроект ACT. 281 - инициатором, до голосования.",
]

SENDING = [
    "Принятые законы в течение двух дней направляются в Федеральный Суд штата "
    "Сан-Андреас, а после получения его одобрения - Губернатору штата Сан-Андреас для "
    "подписания и обнародования (часть 3 статьи 80 Конституции штата Сан-Андреас).",

    "Направление принятых законов обеспечивает Председатель (Спикер) Сената штата "
    "Сан-Андреас.",

    "Настоящие итоги не заменяют протокол заседания: при расхождении применяются сведения "
    "протокола.",
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
    for p in doc.paragraphs[4:]:
        p._p.getparent().remove(p._p)

    def push(el):
        sect.addprevious(el)

    push(with_text(proto_body, LEAD))

    summary = with_text(proto_body, SUMMARY)
    pPr = summary.find(qn("w:pPr"))
    if pPr is not None:
        jc = pPr.find(qn("w:jc"))
        if jc is None:
            jc = OxmlElement("w:jc")
            pPr.append(jc)
        jc.set(qn("w:val"), "center")
    for r in summary.findall(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr")
            r.insert(0, rPr)
        b = OxmlElement("w:b")
        rPr.insert(0, b)
    push(summary)

    push(with_text(proto_h1, "ОБЩИЕ СВЕДЕНИЯ"))
    for t in COMMON:
        push(with_text(proto_body, t))
    push(with_text(proto_h1, "РЕШЕНИЯ ЗАСЕДАНИЯ"))
    for t in DECISIONS:
        push(with_text(proto_body, t))
    push(with_text(proto_h1, "НАПРАВЛЕНИЕ ПРИНЯТЫХ ЗАКОНОВ"))
    for t in SENDING:
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
