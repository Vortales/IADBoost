# -*- coding: utf-8 -*-
"""Исправленные инициативы SANG ACT. 299-300 по действующему срезу.

Каждый документ собирается отдельно по образцу ACT. 260. Номера сохранены;
дата и подпись исправленных версий не заявляются без подтверждения.
"""
import argparse
from pathlib import Path

from docx import Document

import billkit
from build_acts302_312 import APP, APP_TITLE, edited, excerpt, new_part
from make_acts import build

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Законопроекты" / "Инициативы SANG"
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
        "выходу и предоставляет достаточное время для выхода. Лицо, исполняющее требование "
        "и не задержанное, сопровождается военнослужащим до выхода через контрольно-пропускной "
        "пункт, если это не препятствует пресечению непосредственной угрозы жизни или здоровью."
    )
    part7 = excerpt(guard[4], "ч. 7 При обнаружении постороннего лица", "\nч. 8")
    corrected7 = (
        "ч. 7. Военнослужащий вправе потребовать от лица, незаконно находящегося на Форте-Занкудо "
        "или Авианосце, покинуть объект. По основаниям статьи 16 [[B]]Процессуального кодекса "
        "штата Сан-Андреас[[/B]] военнослужащий вправе задержать лицо за нарушение на Форте "
        "или около него либо против сотрудника Национальной гвардии и передать сотрудникам FIB, "
        "LSPD или LSCSD по статье 10 настоящего Закона. Задержание допускается при пресечении "
        "нарушения, продолжающемся преследовании лица в действующем розыске, по ордеру или "
        "решению суда. Задержание военнослужащих за военные преступления, а также задержание "
        "при военном или чрезвычайном положении регулируются законодательством.\n"
        "Огнестрельное оружие применяется по основаниям статьи 8 настоящего Закона в порядке "
        "статьи 37 указанного Кодекса. Невыполнение требования само по себе не дает права на "
        "стрельбу. Если промедление не создает непосредственной угрозы жизни или здоровью, "
        "военнослужащий предупреждает лицо о намерении применить оружие и дает возможность ответить."
    )
    rows299 = [new_part(APP_TITLE, "Статья 4, пункт «а», примечание 1.1", app4,
                        "Примечание 1.1:", new_note)]
    rows300 = [edited(SANG_TITLE, "Статья 2, часть 7", part7, [
        ("R", part7, corrected7),
    ])]
    result = []
    for num, folder, title, section1, rows in (
        (299, "ACT. 299 - выход с территории Форта",
         APP_TITLE, "Законопроект уточняет порядок выхода с территории Форта-Занкудо.", rows299),
        (300, "ACT. 300 - охрана военных объектов",
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
            # Строка сравнения целиком помещается на странице без потери условий.
            bill["table_font_size"] = 11.5
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
        clear_attest(outdir / bill["file"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", type=int, choices=(299, 300), metavar="НОМЕР")
    main(only=parser.parse_args().only)
