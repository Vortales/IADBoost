# -*- coding: utf-8 -*-
"""Лист «Журнал заседаний 13.11» в The Senate of San Andreas 19.xlsx.

Лист повторяет вёрстку журнала 28.10.2026: шапка заседания, список сенаторов,
повестка и пустые графы голосования. Для каждого законопроекта число сенаторов,
учитываемых при голосовании, вводится отдельно; итоги инициатив проверяются вручную.
Число присутствующих и кворум также вводятся на заседании, а не предполагаются.
Остальные части книги сохраняются без изменений.
"""
import io
import math
import os
import posixpath
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET

import openpyxl
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(os.path.dirname(HERE), "Повестка", "The Senate of San Andreas 19.xlsx")
SHEET = "Журнал заседаний 13.11"
REF = "Журнал заседаний 28.10"

TITLE = "Заседание №5 (13.11.2026)"

SENATORS = [
    ("Jhonny Scoutezaki", 164317),
    ("Dmitry Grayrat", 40117),
    ("Afelia Suspect", 14077),
    ("Socrat Wild", 96031),
    ("Umka Nomad", 87727),
    ("Aliya Nomad", 131485),
    ("Eric Killa", 104068),
    ("Kennych Killa", 49429),
    ("Asher Keat", 68553),
    ("Hunter Keates", 122338),
    ("Kiray Fair", 37492),
    ("Himeno Kartonkina", 23899),
    ("Maras Shakyr", 63823),
    ("Meow Killa", 4638),
    ("Makima Killa", 864),
    ("Merkylka Fair", 62277),
]

# (документ, тип НПА, ссылка или None)
AGENDA = [
    ("ACT. 286", "Закон или кодекс",
     "https://docs.google.com/document/d/1ZRNpNoA-WGSzs1XSKASZjbp2prjZAUjU1HjNgDwy0i8/edit?usp=sharing"),
    ("ACT. 287", "Закон или кодекс",
     "https://docs.google.com/document/d/1dXWPbDmI9fJsHuwKzcJvS31evK4FG1BNVKsP6ciNyu8/edit?usp=sharing"),
    ("ACT. 288", "Конституционный закон",
     "https://docs.google.com/document/d/145W9syp1qu6w8-eueMf_8BJ9a4xubO0WZ0MKvX23xI0/edit?usp=sharing"),
    ("ACT. 289", "Закон или кодекс",
     "https://docs.google.com/document/d/1SElyNlHoizePYw795sIpyQsQa1bq9izXdkzKIXmWQ3U/edit?usp=sharing"),
    ("ACT. 290", "Конституционный закон",
     "https://docs.google.com/document/d/1yoVbXuwnPCzUfKpgqSERxdmf9XhrNXOnz2bEPdbHpD0/edit?usp=sharing"),
    ("ACT. 291", "Закон или кодекс",
     "https://docs.google.com/document/d/1G8DGOjEW7VDXD714TEhYo3EDQvaWkpxJtZM065bE1yI/edit?usp=sharing"),
    ("ACT. 292", "Конституционный закон",
     "https://docs.google.com/document/d/1HOLOB7m74DMWWPOuqQS9tZ4g5DQQiSiQ-at2Y1jGtrI/edit?usp=sharing"),
    ("ACT. 293", "Закон или кодекс",
     "https://docs.google.com/document/d/13gqMydlY85PShbWdHNEbbiEwcOSiXVAUKI1MiPbOQts/edit?usp=sharing"),
    ("ACT. 294", "Закон или кодекс",
     "https://docs.google.com/document/d/1PL1yzFsOUE9zDlZQ8VDSA8TBbMVtWrdlHSbJeTpEe_Q/edit?usp=sharing"),
    ("ACT. 295", "Закон или кодекс",
     "https://docs.google.com/document/d/1UeiQzWdCS7PU_6PwmpZv1g4boCbJ-kNwpgPKYwUsmjI/edit?usp=sharing"),
    ("ACT. 296", "Закон или кодекс",
     "https://docs.google.com/document/d/1VyKvlJMgr4pk3hhefDjlWGdvqgdDnR8xNLtfOfQxCSM/edit?usp=sharing"),
    ("ACT. 297", "Закон или кодекс",
     "https://docs.google.com/document/d/1Byp9S1pQjKglD8Z4WztkTxXsEX3FICMlUio-Sd5qUbk/edit?usp=sharing"),
    ("Инициатива об избрании Председателя и членов ЦИК (Merkylka Fair, 62277)", "Инициатива",
     "https://docs.google.com/document/d/1YULp4KtWRA2fbbngZjd2vx6K20C5efhrr8Bbj9ICcOw/edit?tab=t.0"),
    ("Инициатива об избрании Председателя и членов ЦИК (Tommy Harlow, 98650)", "Инициатива",
     "https://docs.google.com/document/d/1tQtVhvKSPt0V62J1pd_SCs_EozbsWh5uhNc6HJdtRsQ/edit?usp=sharing"),
    ("Инициатива о пожизненном лишении Jonny Zakonov права занимать должность сенатора", "Инициатива",
     "https://docs.google.com/document/d/14tCBbXXkNNBvN9fhXjPkocVxydkBPoRSkSQNqsfW3Ss/edit?usp=sharing"),
    ("Инициатива об избрании Afelia Suspect (14077) Вице-Спикером Сената", "Инициатива", None),
]

# Для каждого голосования J - вручную установленное число сенаторов, подлежащих
# учёту по применимой норме. Решение по инициативе требует отдельной проверки.
RESULT = ('=IF(OR(NOT(ISNUMBER(E{r})),NOT(ISNUMBER(F{r}))),"Не рассмотрен",'
          'IF(OR(NOT(ISNUMBER($B$3)),NOT(ISNUMBER(J{r}))),"Укажите явку и число сенаторов",'
          'IF($D$3<>"Собран","Проверьте кворум",'
          'IF(OR(E{r}<0,F{r}<0,J{r}<1,$B$3<0,MOD(E{r},1)<>0,MOD(F{r},1)<>0,'
          'MOD(J{r},1)<>0,MOD($B$3,1)<>0,E{r}+F{r}>$B$3,E{r}+F{r}>J{r}),'
          '"Проверьте данные",'
          'IF(D{r}="Инициатива","Итог проверить вручную",'
          'IF(D{r}="Закон или кодекс",IF(E{r}>J{r}/2,"Принят Сенатом","Отклонён"),'
          'IF(D{r}="Конституционный закон",IF(E{r}>=ROUNDUP(J{r}*2/3,0),'
          '"Принят Сенатом","Отклонён"),'
          'IF(D{r}="Пересмотр Конституции",IF(E{r}>=ROUNDUP(J{r}*3/4,0),'
          '"Принят Сенатом","Отклонён"),"Проверьте тип"))))))))')

ABSTENTIONS = ('=IF(OR(NOT(ISNUMBER($B$3)),NOT(ISNUMBER(E{r})),NOT(ISNUMBER(F{r}))),"",'
               'IF($B$3-E{r}-F{r}<0,"Проверьте голоса",$B$3-E{r}-F{r}))')

# Прежние формулы принимаются только для безопасного обновления незаполненного листа.
LEGACY_RESULT = ('=IF(OR(D{r}="Закон или кодекс", D{r}="Инициатива"), '
                 'IF(AND(ISNUMBER(E{r}),ISNUMBER(F{r})), '
                 'IF(AND(E{r}=0,F{r}=0), "Отозван", '
                 'IF(E{r}=F{r}, "Спикер, примите решение", '
                 'IF(E{r}>F{r}, "Принят", "Отклонён"))), "Не рассмотрен"), '
                 'IF(OR(D{r}="Конституционный закон", D{r}="Пересмотр Конституции"), '
                 'IF(AND(ISNUMBER(E{r}),ISNUMBER(F{r})), '
                 'IF(AND(E{r}=0,F{r}=0), "Отозван", '
                 'IF(AND(E{r}=F{r},E{r}>=$D$2*2/3), "Спикер, примите решение", '
                 'IF(AND(E{r}>F{r},E{r}>=$D$2*2/3), "Передан в Верховный Суд", "Отклонён"))), '
                 '"Не рассмотрен"), "Отклонён"))')

NEW_METADATA = {
    "ACT. 294": "ЗГП Gogal Killaz, номер паспорта 63823; 17:34, дата не указана. Ссылка ведёт к исходной редакции; исправленный DOCX подготовлен отдельно.",
    "ACT. 295": "ЗГП Gogal Killaz, номер паспорта 63823; 17:34. Дата размещения в исходной записи не указана.",
    "ACT. 296": "ЗГП Gogal Killaz, номер паспорта 63823; 17:35. Дата размещения в исходной записи не указана.",
    "ACT. 297": "ЗГП Gogal Killaz, номер паспорта 63823; 17:35. Дата размещения в исходной записи не указана.",
}

THIN = Side(style="thin")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FONT = Font(name="Times New Roman", size=12)
FONT_B = Font(name="Times New Roman", size=12, bold=True)
FONT_LINK = Font(name="Times New Roman", size=12, bold=True, color="FF0000FF", underline="single")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)


def style(ws, row, col, value=None, font=FONT, align=CENTER):
    c = ws.cell(row=row, column=col)
    if value is not None:
        c.value = value
    c.font = font
    c.alignment = align
    c.border = BORDER
    return c


def sheet_parts(archive):
    """Определить внутренние имена XML листа по связям книги, не по его индексу."""
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    doc_rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    pkg_rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    sheet = next((s for s in workbook.findall(".//{%s}sheet" % main_ns)
                  if s.get("name") == SHEET), None)
    if sheet is None:
        raise ValueError("Лист не найден в структуре XLSX: " + SHEET)
    rid = sheet.get("{%s}id" % doc_rel_ns)
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel = next((r for r in rels.findall("{%s}Relationship" % pkg_rel_ns)
                if r.get("Id") == rid), None)
    if rel is None or not rel.get("Type", "").endswith("/worksheet"):
        raise ValueError("Не найдена связь с листом " + SHEET)
    target = rel.get("Target")
    part = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
    parent, name = posixpath.split(part)
    return part, posixpath.join(parent, "_rels", name + ".rels")


def save_only_sheet(wb, path):
    """Заменить только XML целевого листа и его ссылок; остальные части ZIP не менять."""
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    temp_path = None
    try:
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(output) as built:
            old_sheet, old_rels = sheet_parts(source)
            new_sheet, new_rels = sheet_parts(built)
            for part in ("xl/styles.xml", "xl/workbook.xml", "xl/_rels/workbook.xml.rels",
                         "[Content_Types].xml"):
                if source.read(part) != built.read(part):
                    raise ValueError("Изменилась общая часть книги: " + part)
            if old_rels not in source.namelist() or new_rels not in built.namelist():
                raise ValueError("Отсутствуют связи гиперссылок целевого листа")
            rels = ET.fromstring(source.read(old_rels))
            if any(not r.get("Type", "").endswith("/hyperlink") for r in rels):
                raise ValueError("У листа есть дополнительные объекты: автоматическая пересборка остановлена")
            sheet_xml = built.read(new_sheet)
            # Кэш счётчика виден и в просмотрщиках, которые не пересчитывают формулы.
            formula = "COUNTA(C7:C{})".format(6 + len(AGENDA)).encode("ascii")
            uncached = b"<f>" + formula + b"</f><v></v>"
            cached = b"<f>" + formula + b"</f><v>" + str(len(AGENDA)).encode("ascii") + b"</v>"
            if sheet_xml.count(uncached) != 1:
                raise ValueError("Не удалось подготовить кэш счётчика вопросов")
            sheet_xml = sheet_xml.replace(uncached, cached, 1)
            replacement = {old_sheet: sheet_xml, old_rels: built.read(new_rels)}
            fd, temp_path = tempfile.mkstemp(prefix=".senate-", suffix=".xlsx", dir=os.path.dirname(path))
            os.close(fd)
            with zipfile.ZipFile(temp_path, "w") as result:
                result.comment = source.comment
                for info in source.infolist():
                    data = replacement.get(info.filename)
                    result.writestr(info, source.read(info.filename) if data is None else data)
        os.chmod(temp_path, os.stat(path).st_mode & 0o777)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def check_existing_sheet(ws):
    """Не стирать заполненный журнал или вручную изменённый список вопросов."""
    if ws["B3"].value is not None:
        raise ValueError("Лист уже содержит данные заседания: B3")
    legacy_quorum = '=IF(B3="","",IF(B3>=B2/2,"Собран","Не собран"))'
    if ws["D3"].value not in (None, legacy_quorum):
        raise ValueError("Лист уже содержит данные заседания: D3")
    for r in range(7, max(ws.max_row, 6 + len(AGENDA)) + 1):
        for col in (5, 6, 9, 10):
            if ws.cell(r, col).value is not None:
                raise ValueError("Лист уже содержит введённые данные: " + ws.cell(r, col).coordinate)
        allowed_g = (None, "=$B$3-E{r}-F{r}".format(r=r), ABSTENTIONS.format(r=r))
        allowed_h = (None, LEGACY_RESULT.format(r=r), RESULT.format(r=r))
        for col, allowed in ((7, allowed_g), (8, allowed_h)):
            if ws.cell(r, col).value not in allowed:
                raise ValueError("Лист уже содержит введённые данные: " + ws.cell(r, col).coordinate)
    for i, (name, passport) in enumerate(SENATORS, 5):
        if ws.cell(i, 1).value != "{} | {}".format(name, passport) or ws.cell(i, 2).value != i - 4:
            raise ValueError("Список сенаторов изменён вручную: строка " + str(i))
    before = [entry for entry in AGENDA if entry[0] not in NEW_METADATA]
    existing = [(ws.cell(r, 3).value, ws.cell(r, 4).value,
                 ws.cell(r, 3).hyperlink.target if ws.cell(r, 3).hyperlink else None)
                for r in range(7, ws.max_row + 1) if ws.cell(r, 3).value is not None]
    if existing not in (before, AGENDA):
        raise ValueError("Список вопросов или ссылок изменён вручную; автоматическая пересборка остановлена")


def build():
    wb = openpyxl.load_workbook(XLSX)
    if SHEET in wb.sheetnames:
        check_existing_sheet(wb[SHEET])
        del wb[SHEET]

    ref = wb[REF]
    ws = wb.create_sheet(SHEET, wb.sheetnames.index(REF) + 1)
    for col, dim in ref.column_dimensions.items():
        if dim.width:
            ws.column_dimensions[col].width = dim.width
    ws.column_dimensions["J"].width = 22

    last_row = 6 + len(AGENDA)          # последняя строка повестки
    last_sen = 4 + len(SENATORS)        # последняя строка списка сенаторов
    assert last_sen <= 21, "список сенаторов выходит за блок A4:B21"

    # --- шапка -------------------------------------------------------
    style(ws, 1, 1, TITLE, FONT_B, LEFT)
    for c in range(2, 11):
        style(ws, 1, c)
    ws.merge_cells("A1:J1")

    style(ws, 2, 1, "Всего сенаторов:", FONT)
    style(ws, 2, 2, "=COUNTA('Реестр сенаторов'!B4:B10,'Реестр сенаторов'!D4:D10,"
                    "'Реестр сенаторов'!B14:B21,'Реестр сенаторов'!D14:D21)", FONT, LEFT)
    for c, v in ((3, None), (4, "=B2"), (5, "Тип заседания"), (6, "Спикер"), (7, "Всего вопросов")):
        style(ws, 2, c, v)
    for c in range(8, 11):
        style(ws, 2, c)

    style(ws, 3, 1, "Явилось на заседание:", FONT)
    style(ws, 3, 2, None, FONT)                     # заполняется на заседании
    style(ws, 3, 3, "Кворум:", FONT)
    style(ws, 3, 4, None, FONT)                     # подтверждается вручную
    style(ws, 3, 5, "Плановое", FONT)
    style(ws, 3, 6, "Marcus Nomad", FONT)
    style(ws, 3, 7, "=COUNTA(C7:C{})".format(last_row), FONT)
    for c in range(8, 11):
        style(ws, 3, c)

    # --- сенаторы ----------------------------------------------------
    style(ws, 4, 1, "Сенаторы на заседании:", FONT, LEFT)
    style(ws, 4, 2)
    ws.merge_cells("A4:B4")
    style(ws, 4, 3, "Протокол заседания", FONT)
    for c in range(4, 11):
        style(ws, 4, c)
    ws.merge_cells("C4:H4")

    style(ws, 5, 3, "Повестка", FONT)
    style(ws, 5, 4)
    ws.merge_cells("C5:D5")
    style(ws, 5, 5, "Голоса", FONT)
    style(ws, 5, 6)
    style(ws, 5, 7)
    ws.merge_cells("E5:G5")
    for c in (8, 9, 10):
        style(ws, 5, c)

    for i, (name, passport) in enumerate(SENATORS):
        r = 5 + i
        style(ws, r, 1, "{} | {}".format(name, passport), FONT, LEFT)
        style(ws, r, 2, i + 1, FONT)
        for c in range(3, 11):
            style(ws, r, c)

    # --- повестка ----------------------------------------------------
    head = ("Инициатива, её суть", "Тип НПА", '"За"', '"Против"', "Воздержался", "Результат", "Статус",
            "Сенаторов для подсчёта")
    for i, h in enumerate(head):
        style(ws, 6, 3 + i, h, FONT_B)
    ws.row_dimensions[6].height = 34

    for i, (doc, kind, link) in enumerate(AGENDA):
        r = 7 + i
        c = style(ws, r, 3, doc, FONT_LINK if link else FONT, LEFT)
        if link:
            c.hyperlink = link
            if doc in NEW_METADATA:
                c.hyperlink.tooltip = NEW_METADATA[doc]
        style(ws, r, 4, kind, FONT)
        style(ws, r, 5, None, FONT)
        style(ws, r, 6, None, FONT)
        ws.cell(row=r, column=5).number_format = "0"
        ws.cell(row=r, column=6).number_format = "0"
        style(ws, r, 7, ABSTENTIONS.format(r=r), FONT)
        style(ws, r, 8, RESULT.format(r=r), FONT)
        style(ws, r, 9, None, FONT)
        style(ws, r, 10, None, FONT)                # число для каждого вопроса вводится вручную
        ws.cell(row=r, column=10).number_format = "0"
        ws.row_dimensions[r].height = max(24, 16 * math.ceil(len(doc) / 24))

    # --- оформление результата и проверки ввода ----------------------
    ws.conditional_formatting.add(
        "H7:H{}".format(last_row),
        CellIsRule(operator="equal", formula=['"Принят Сенатом"'],
                   font=Font(color="FF117372"),
                   fill=PatternFill("solid", start_color="FFD4EDBC", end_color="FFD4EDBC")))
    ws.conditional_formatting.add(
        "H7:H{}".format(last_row),
        CellIsRule(operator="equal", formula=['"Отклонён"'],
                   font=Font(color="FFB80248"),
                   fill=PatternFill("solid", start_color="FFFFCFC9", end_color="FFFFCFC9")))

    dv_type = DataValidation(type="list", allow_blank=True,
                             formula1='"Инициатива,Конституционный закон,Пересмотр Конституции,'
                                      'Закон или кодекс"')
    dv_type.add("D7:D{}".format(last_row))
    ws.add_data_validation(dv_type)

    dv_kind = DataValidation(type="list", allow_blank=True,
                             formula1='"Плановое,Внеплановое,Большинство"')
    dv_kind.add("E3")
    ws.add_data_validation(dv_kind)

    dv_quorum = DataValidation(type="list", allow_blank=True, formula1='"Собран,Не собран"')
    dv_quorum.add("D3")
    ws.add_data_validation(dv_quorum)

    dv_total = DataValidation(type="whole", operator="between", allow_blank=True,
                              formula1="1", formula2="$B$2", showErrorMessage=True)
    dv_total.errorTitle = "Проверьте число сенаторов"
    dv_total.error = "Введите целое число от 1 до числа сенаторов в реестре."
    dv_total.add("J7:J{}".format(last_row))
    ws.add_data_validation(dv_total)

    dv_status = DataValidation(type="list", allow_blank=True,
                               formula1='"На рассмотрении,Вето/отклонен Судом,Одобрен Судом,'
                                        'Подписан,Другое"')
    dv_status.add("I7:I{}".format(last_row))
    ws.add_data_validation(dv_status)

    ws.sheet_view.showGridLines = False
    save_only_sheet(wb, XLSX)
    print("OK", SHEET, "| строк повестки:", len(AGENDA), "| сенаторов:", len(SENATORS))


if __name__ == "__main__":
    sys.exit(build())
