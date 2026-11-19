# -*- coding: utf-8 -*-
"""Новый лист журнала 19.11 в копии книги 13.11 без изменения старых листов.

Голоса и воздержания вводятся из лога как фактические числа. Явка и кворум
не выдумываются, один совместный опрос ACT. 299-300 занимает одну строку.
Существующую выходную книгу скрипт не перезаписывает.
"""
import argparse
from copy import copy
from io import BytesIO
import os
import re
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

import make_senat_documents_19_11 as meeting

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "Повестка/13.11.2026/05 Журнал/The Senate of San Andreas 19.xlsx"
OUTPUT = ROOT / "Повестка/19.11.2026/04 Журнал/The Senate of San Andreas 19 - 19.11.2026.xlsx"
OLD_SHEET = "Журнал заседаний 13.11"
SHEET = "Журнал заседаний 19.11"

# Короткие подписи полностью видны в узкой колонке журнала, включая печать.
QUESTION_LABELS = {
    "open": "Открытие заседания",
    "299-300": "ACT. 299 + ACT. 300 - охрана Форта",
    "301": "ACT. 301 - освобождение и выход",
    "302": "ACT. 302 - вызов начальства",
    "303": "ACT. 303 - режим территорий",
    "304": "ACT. 304 - вызов прокурора",
    "305": "ACT. 305 - материалы защиты",
    "306": "ACT. 306 - устные ходатайства",
    "307": "ACT. 307 - сведения адвокату",
    "308": "ACT. 308 - митинги и госслужащие",
    "309": "ACT. 309 - оскорбление представителя власти",
    "cec": "Инициатива - замена члена ЦИК",
    "close": "Закрытие заседания",
}


def events():
    """Все завершённые опросы и пять отзывов, по минуте начала события."""
    records = [(p.start, 0, p.key, p) for p in meeting.POLLS]
    records += [(time, 1, key, None) for key, time in meeting.WITHDRAWN]
    return sorted(records, key=lambda row: (row[0], row[1], row[2]))


def set_style_from(ws, target, source):
    ws[target]._style = copy(ws[source]._style)


def configure_sheet(ws: Worksheet):
    ws.title = SHEET
    # Не копируем прошлый состав сенаторов, прошлую повестку и формулы.
    for row in ws.iter_rows(min_row=5, max_row=max(22, 6 + len(events())), min_col=1, max_col=13):
        for cell in row:
            if cell.__class__.__name__ == "MergedCell":
                continue
            cell.value = None
            cell.hyperlink = None
            cell.comment = None
    ws["A1"] = "Заседание Сената - 19.11.2026"
    ws["A2"] = "Всего действующих сенаторов:"
    ws["B2"] = meeting.ACTIVE_COUNT
    ws["D2"] = None
    ws["E2"] = "Тип заседания"
    ws["F2"] = "Спикер"
    ws["G2"] = "Вопросов"
    ws["A3"] = "Явилось на заседание:"
    ws["B3"] = None
    ws["C3"] = "Кворум:"
    ws["D3"] = "Не подтверждён"
    ws["E3"] = "Плановое"
    ws["F3"] = "Marcus Nomad"
    ws["G3"] = len(meeting.ITEMS)
    ws["A4"] = "Сведения о явке"
    ws["C4"] = "Журнал голосований и отозванных вопросов"
    ws["C5"] = "Вопрос"
    ws["E5"] = "Голоса"
    ws["A5"] = "Поимённая явка не предоставлена"
    ws["A6"] = "За открытие - 13 голосов"
    ws["A7"] = "Неучастие не равно воздержанию"
    ws["A8"] = "Состав для подсчёта: 16"
    ws["A9"] = "Прежний реестр - исторический"
    ws["A10"] = "Время событий - точность до минуты"
    ws["A11"] = "Голосование ACT. 299-300 общее"
    ws["A12"] = "ACT. 308: проверить название акта"
    ws["A13"] = "Принятие не означает вступление в силу"
    for row in range(5, 14):
        set_style_from(ws, f"A{row}", "A5")

    headings = ("Вопрос", "Тип", '"За"', '"Против"', "Воздержался", "Результат", "Статус",
                "Сенаторов для подсчёта", "Начало", "Окончание", "Вторая ссылка")
    for col, title in enumerate(headings, 3):
        cell = ws.cell(6, col)
        cell._style = copy(ws["C6"]._style)
        cell.value = title
    ws.row_dimensions[6].height = 34
    for col, width in {"A": 39, "B": 12, "C": 48, "D": 25, "E": 10, "F": 12,
                       "G": 15, "H": 23, "I": 21, "J": 20, "K": 13, "L": 15, "M": 19}.items():
        ws.column_dimensions[col].width = width

    link_style = copy(ws["C7"]._style)
    plain_style = copy(ws["H7"]._style)
    numeric_style = copy(ws["E7"]._style)
    for row_num, (start, _, key, poll) in enumerate(events(), 7):
        for col in range(3, 14):
            cell = ws.cell(row_num, col)
            cell._style = copy(numeric_style if col in (5, 6, 10) else plain_style)
        if poll is None:
            item = meeting.ITEM[key]
            values = (QUESTION_LABELS[key], item.kind, None, None, None,
                      "Отозван", None, None, start, None, None)
            url = item.url
            second_url = None
        else:
            values = (QUESTION_LABELS[key], poll.kind, poll.yes, poll.no, poll.abstain,
                      poll.outcome, None, meeting.ACTIVE_COUNT, poll.start, poll.end,
                      "ACT. 300" if poll.second_url else None)
            url, second_url = poll.url, poll.second_url
        for col, value in enumerate(values, 3):
            ws.cell(row_num, col).value = value
        if url:
            ws.cell(row_num, 3).hyperlink = url
            ws.cell(row_num, 3)._style = copy(link_style)
        if second_url:
            ws.cell(row_num, 13).hyperlink = second_url
            ws.cell(row_num, 13)._style = copy(link_style)
        ws.row_dimensions[row_num].height = max(28, 17 * ((len(str(values[0])) + 42) // 43))

    ws.freeze_panes = "C7"
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 80
    ws.print_options.horizontalCentered = True
    ws.print_area = f"A1:M{6 + len(events())}"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A3


def lookup_sheet_parts(archive, sheet_name):
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_doc = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    rel_pkg = "http://schemas.openxmlformats.org/package/2006/relationships"
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    sheets = workbook.findall(f".//{{{main}}}sheet")
    target = next((sheet for sheet in sheets if sheet.get("name") == sheet_name), None)
    if target is None:
        raise ValueError(f"Лист {sheet_name!r} не найден")
    relid = target.get(f"{{{rel_doc}}}id")
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relation = next((r for r in rels.findall(f"{{{rel_pkg}}}Relationship") if r.get("Id") == relid), None)
    if relation is None or not relation.get("Type", "").endswith("/worksheet"):
        raise ValueError("Не найдена связь с новым листом")
    part = relation.get("Target").lstrip("/")
    if not part.startswith("xl/"):
        part = "xl/" + part
    parent, name = part.rsplit("/", 1)
    return part, f"{parent}/_rels/{name}.rels"


def append_once(data, closing, fragment):
    if data.count(closing) != 1:
        raise ValueError(f"Неожиданная структура XLSX: {closing!r}")
    return data.replace(closing, fragment + closing, 1)


def build(output=OUTPUT, template=TEMPLATE):
    meeting.validate_source()
    output, template = Path(output), Path(template)
    if output.exists():
        raise FileExistsError(f"Выходная книга уже существует; автоматическое перезаписывание запрещено: {output}")
    source_bytes = template.read_bytes()
    workbook = openpyxl.load_workbook(BytesIO(source_bytes))
    if OLD_SHEET not in workbook.sheetnames or SHEET in workbook.sheetnames:
        raise ValueError("Исходная книга не соответствует ожидаемой структуре")
    ws = workbook.copy_worksheet(workbook[OLD_SHEET])
    configure_sheet(ws)
    built_buffer = BytesIO()
    workbook.save(built_buffer)
    built_buffer.seek(0)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with ZipFile(BytesIO(source_bytes)) as source, ZipFile(built_buffer) as built:
            if source.read("xl/styles.xml") != built.read("xl/styles.xml"):
                raise ValueError("Новый лист изменил общие стили исходной книги")
            new_sheet, new_links = lookup_sheet_parts(built, SHEET)
            if new_sheet in source.namelist() or new_links in source.namelist() or new_links not in built.namelist():
                raise ValueError("Неверные внутренние имена нового листа")
            wb_xml = source.read("xl/workbook.xml")
            rel_xml = source.read("xl/_rels/workbook.xml.rels")
            content_xml = source.read("[Content_Types].xml")
            sheet_ids = [int(v) for v in re.findall(rb'sheetId="(\d+)"', wb_xml)]
            rel_ids = [int(v) for v in re.findall(rb'Id="rId(\d+)"', rel_xml)]
            if not sheet_ids or not rel_ids or b"<bookViews" in wb_xml or wb_xml.count(b"<sheets>") != 1:
                raise ValueError("Неподдерживаемая структура исходной книги")
            sheet_id, rel_id = max(sheet_ids) + 1, max(rel_ids) + 1
            sheet_entry = (f'<sheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                           f'name="{SHEET}" sheetId="{sheet_id}" state="visible" r:id="rId{rel_id}"/>').encode("utf-8")
            wb_xml = append_once(wb_xml, b"</sheets>", sheet_entry)
            # При открытии первой отображается именно новая ведомость, а не старый реестр.
            view = f'<bookViews><workbookView activeTab="{len(sheet_ids)}"/></bookViews>'.encode("ascii")
            wb_xml = wb_xml.replace(b"<sheets>", view + b"<sheets>", 1)
            # Область печати хранится в workbook.xml, а не в XML листа.
            if wb_xml.count(b"<definedNames/>") != 1:
                raise ValueError("Неподдерживаемые именованные диапазоны исходной книги")
            print_name = (f'<definedNames><definedName name="_xlnm.Print_Area" '
                          f'localSheetId="{len(sheet_ids)}">\'{SHEET}\'!$A$1:$M${6 + len(events())}'
                          '</definedName></definedNames>').encode("utf-8")
            wb_xml = wb_xml.replace(b"<definedNames/>", print_name, 1)
            rel_entry = (f'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                         f'Target="/{new_sheet}" Id="rId{rel_id}"/>').encode("utf-8")
            rel_xml = append_once(rel_xml, b"</Relationships>", rel_entry)
            content_entry = (f'<Override PartName="/{new_sheet}" '
                             'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>').encode("utf-8")
            content_xml = append_once(content_xml, b"</Types>", content_entry)
            replacements = {"xl/workbook.xml": wb_xml, "xl/_rels/workbook.xml.rels": rel_xml,
                            "[Content_Types].xml": content_xml}
            fd, temp_path = tempfile.mkstemp(prefix=".senate-19-", suffix=".xlsx", dir=output.parent)
            os.close(fd)
            with ZipFile(temp_path, "w") as result:
                result.comment = source.comment
                for info in source.infolist():
                    result.writestr(info, replacements.get(info.filename, source.read(info.filename)))
                result.writestr(new_sheet, built.read(new_sheet))
                result.writestr(new_links, built.read(new_links))
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, output)
        temp_path = None
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
    print("OK", output, "| событий:", len(events()), "| вопросов:", len(meeting.ITEMS))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    build(args.output)
