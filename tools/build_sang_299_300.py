# -*- coding: utf-8 -*-
"""Исправленные инициативы SANG ACT. 299-300 по действующему срезу.

Каждый документ собирается отдельно по образцу ACT. 260. Номера сохранены;
дата и подпись исправленных версий не заявляются без подтверждения.
"""
import argparse
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

import billkit
from legal_sources import APP, APP_TITLE, edited, excerpt, new_part
from make_acts import build

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Законопроекты"
# Дата и согласование исправленной редакции не подтверждены.
DATE = ""
SANG = "Закон О Национальной Гвардии штата Сан-Андреас"
SANG_TITLE = "Закон «О Национальной Гвардии штата Сан-Андреас»"


def specs():
    appendix = billkit.load(APP)
    guard = billkit.load(SANG)
    app4 = appendix[7]
    # Подтверждаем место вставки, не повторяя неизменённое примечание 1 в таблице.
    excerpt(app4, "Примечание 1: Вокруг территории Форта Занкудо", "\nб)\n")
    new_note = (
        "Примечание 1.1: Военнослужащий, требующий от лица, не имеющего законных оснований "
        "для нахождения на территории Форта-Занкудо за контрольно-пропускным пунктом, "
        "покинуть ее, обозначает принадлежность к Национальной гвардии, указывает путь к "
        "выходу и предоставляет достаточное время для выхода с учетом установленных законом "
        "сроков. Лицо, исполняющее требование "
        "и не задержанное, сопровождается военнослужащим до выхода через контрольно-пропускной "
        "пункт, если это не препятствует пресечению непосредственной угрозы жизни или здоровью."
    )
    part7 = excerpt(guard[4], "ч. 7 При обнаружении постороннего лица", "\nч. 8")
    corrected7 = (
        "ч. 7. При незаконном нахождении на Форте-Занкудо или Авианосце военнослужащий вправе "
        "потребовать уйти, указав путь. Незадержанному дается достаточное время с учетом установленных "
        "законом сроков; на Форте военнослужащий сопровождает его до КПП, если это не препятствует "
        "пресечению непосредственной угрозы жизни или здоровью.\n"
        "По основаниям и в порядке [[B]]Процессуального кодекса штата Сан-Андреас[[/B]] и статьи 10 "
        "настоящего Закона военнослужащий вправе задержать лицо за нарушение на Форте, около него или "
        "против сотрудника Национальной гвардии с передачей сотрудникам FIB, LSPD или LSCSD. "
        "Задержание допускается при пресечении нарушения, продолжающемся преследовании лица "
        "в действующем розыске, по ордеру или решению суда. Задержание военнослужащих за военные "
        "преступления и задержание при военном или чрезвычайном положении регулируются законом.\n"
        "При отражении нападения на Форт государственные служащие не применяют наручники; после "
        "его окончания причастные лица могут быть задержаны на законных основаниях.\n"
        "Огнестрельное оружие применяется по статье 8 настоящего Закона в порядке указанного Кодекса. "
        "Невыполнение требования уйти само по себе не является основанием для применения оружия. "
        "Если промедление не создает непосредственной угрозы жизни или здоровью, лицо предупреждается "
        "о применении оружия и получает возможность ответить и исполнить требование."
    )
    rows299 = [new_part(APP_TITLE, "Статья 4, пункт «а», примечание 1.1", app4,
                        "Примечание 1.1:", new_note)]
    rows300 = [edited(SANG_TITLE, "Статья 2, часть 7", part7, [
        ("R", part7, corrected7),
    ])]
    result = []
    for num, folder, title, section1, rows in (
        (299, "Законопроекты 299 - выход с территории Форта",
         APP_TITLE, "Законопроект уточняет порядок выхода с территории Форта-Занкудо.", rows299),
        (300, "Законопроекты 300 - охрана военных объектов",
         SANG_TITLE, "Законопроект уточняет меры при незаконном нахождении на военных объектах.", rows300),
    ):
        result.append((folder, billkit.bill(
            num, DATE, f"ACT.{num}.{title}.docx",
            f"о внесении изменений в [[B]]{title}[[/B]]",
            section1, f"SECTION. 2. ВНЕСЕНИЕ ПРАВКИ В {title}", rows,
        )))
    for _, bill in result:
        bill["clear_template_metadata"] = True
        if bill["num"] == 300:
            # Объединенная редакция сохраняет читаемость и помещается на странице.
            bill["table_font_size"] = 10.5
    return result


def clear_attest(path):
    """Оставляет место для подписи, не выдавая исходное удостоверение за согласование правок."""
    doc = Document(path)
    found = []
    for section in doc.sections:
        for paragraph in section.footer.paragraphs:
            if "Attest: Marcus Nomad" not in paragraph.text:
                continue
            runs = paragraph.runs
            start = next(i for i, run in enumerate(runs) if "Attest:" in run.text)
            tail = "".join(run.text for run in runs[start:])
            if tail.count("Attest: Marcus Nomad") != 1:
                raise ValueError("Неожиданный колонтитул шаблона")
            runs[start].text = tail.replace("Attest: Marcus Nomad", "Attest: __________________")
            for run in runs[start + 1:]:
                run.text = ""
            found.append(paragraph)
    if len(found) != 1:
        raise ValueError("Не удалось однозначно сохранить подпись автора")
    doc.save(path)


def trim_terminal_paragraph(path):
    """Не создаёт пустую страницу после последней строки таблицы."""
    doc = Document(path)
    tail = doc.tables[0]._tbl.getnext()
    if (tail is not None and tail.tag == qn("w:p") and not "".join(tail.itertext())
            and tail.getnext() is not None and tail.getnext().tag == qn("w:sectPr")):
        tail.getparent().remove(tail)
        doc.save(path)


def main(only=None):
    bills = specs()
    if only is not None and only not in {bill["num"] for _, bill in bills}:
        raise ValueError(f"Нет проекта ACT. {only}")
    for directory, bill in bills:
        if only is not None and bill["num"] != only:
            continue
        outdir = OUT / directory
        outdir.mkdir(parents=True, exist_ok=True)
        build(bill, str(outdir))
        path = outdir / bill["file"]
        clear_attest(path)
        if bill["num"] == 300:
            trim_terminal_paragraph(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", type=int, choices=(299, 300), metavar="НОМЕР")
    main(only=parser.parse_args().only)
