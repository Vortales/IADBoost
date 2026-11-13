# -*- coding: utf-8 -*-
"""Лист «Журнал заседаний 13.11» в The Senate of San Andreas 19.xlsx.

Лист повторяет вёрстку журнала 28.10.2026: шапка заседания, список сенаторов,
повестка дня и пустые графы голосования с формулами результата.
Исправлены ошибки образца: номер заседания (№ 5), формула «Всего инициатив»,
диапазоны подсчёта. Кворум не объявляется до заполнения графы «Явилось на заседание».
"""
import os
import sys

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
    ("Инициатива об избрании Председателя и членов ЦИК (Merkylka Fair, 62277)", "Инициатива",
     "https://docs.google.com/document/d/1YULp4KtWRA2fbbngZjd2vx6K20C5efhrr8Bbj9ICcOw/edit?tab=t.0"),
    ("Инициатива об избрании Председателя и членов ЦИК (Tommy Harlow, 98650)", "Инициатива",
     "https://docs.google.com/document/d/1tQtVhvKSPt0V62J1pd_SCs_EozbsWh5uhNc6HJdtRsQ/edit?usp=sharing"),
    ("Инициатива о пожизненном лишении Jonny Zakonov права занимать должность сенатора", "Инициатива",
     "https://docs.google.com/document/d/14tCBbXXkNNBvN9fhXjPkocVxydkBPoRSkSQNqsfW3Ss/edit?usp=sharing"),
    ("Инициатива об избрании Afelia Suspect (14077) Вице-Спикером Сената", "Инициатива", None),
]

RESULT = ('=IF(OR(D{r}="Закон или кодекс", D{r}="Инициатива"), '
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


def build():
    wb = openpyxl.load_workbook(XLSX)
    if SHEET in wb.sheetnames:
        del wb[SHEET]

    ref = wb[REF]
    ws = wb.create_sheet(SHEET, wb.sheetnames.index(REF) + 1)
    for col, dim in ref.column_dimensions.items():
        if dim.width:
            ws.column_dimensions[col].width = dim.width

    last_row = 6 + len(AGENDA)          # последняя строка повестки
    last_sen = 4 + len(SENATORS)        # последняя строка списка сенаторов
    assert last_sen <= 21, "список сенаторов выходит за блок A4:B21"

    # --- шапка -------------------------------------------------------
    style(ws, 1, 1, TITLE, FONT_B, LEFT)
    for c in range(2, 10):
        style(ws, 1, c)
    ws.merge_cells("A1:I1")

    style(ws, 2, 1, "Всего сенаторов:", FONT)
    style(ws, 2, 2, "=COUNTA('Реестр сенаторов'!B4:B10,'Реестр сенаторов'!D4:D10,"
                    "'Реестр сенаторов'!B14:B21,'Реестр сенаторов'!D14:D21)", FONT, LEFT)
    for c, v in ((3, None), (4, "=B2"), (5, "Тип заседания"), (6, "Спикер"), (7, "Всего инициатив")):
        style(ws, 2, c, v)
    for c in range(8, 10):
        style(ws, 2, c)

    style(ws, 3, 1, "Явилось на заседание:", FONT)
    style(ws, 3, 2, None, FONT)                     # заполняется на заседании
    style(ws, 3, 3, "Кворум:", FONT)
    style(ws, 3, 4, '=IF(B3="","",IF(B3>=B2/2,"Собран","Не собран"))', FONT)
    style(ws, 3, 5, "Плановое", FONT)
    style(ws, 3, 6, "Marcus Nomad", FONT)
    style(ws, 3, 7, "=COUNTA(C7:C{})".format(last_row), FONT)
    for c in range(8, 10):
        style(ws, 3, c)

    # --- сенаторы ----------------------------------------------------
    style(ws, 4, 1, "Сенаторы на заседании:", FONT, LEFT)
    style(ws, 4, 2)
    ws.merge_cells("A4:B4")
    style(ws, 4, 3, "Протокол заседания", FONT)
    for c in range(4, 10):
        style(ws, 4, c)
    ws.merge_cells("C4:H4")

    style(ws, 5, 3, "Повестка", FONT)
    style(ws, 5, 4)
    ws.merge_cells("C5:D5")
    style(ws, 5, 5, "Голоса", FONT)
    style(ws, 5, 6)
    style(ws, 5, 7)
    ws.merge_cells("E5:G5")
    for c in (8, 9):
        style(ws, 5, c)

    for i, (name, passport) in enumerate(SENATORS):
        r = 5 + i
        style(ws, r, 1, "{} | {}".format(name, passport), FONT, LEFT)
        style(ws, r, 2, i + 1, FONT)
        for c in range(3, 10):
            style(ws, r, c)

    # --- повестка ----------------------------------------------------
    head = ("Инициатива, её суть", "Тип НПА", '"За"', '"Против"', "Воздержался", "Результат", "Статус")
    for i, h in enumerate(head):
        style(ws, 6, 3 + i, h, FONT_B)

    for i, (doc, kind, link) in enumerate(AGENDA):
        r = 7 + i
        c = style(ws, r, 3, doc, FONT_LINK if link else FONT, LEFT)
        if link:
            c.hyperlink = link
        style(ws, r, 4, kind, FONT)
        style(ws, r, 5, None, FONT)
        style(ws, r, 6, None, FONT)
        ws.cell(row=r, column=5).number_format = "0"
        ws.cell(row=r, column=6).number_format = "0"
        style(ws, r, 7, "=$B$3-E{r}-F{r}".format(r=r), FONT)
        style(ws, r, 8, RESULT.format(r=r), FONT)
        style(ws, r, 9, None, FONT)

    # --- оформление результата и проверки ввода ----------------------
    ws.conditional_formatting.add(
        "H7:H{}".format(last_row),
        CellIsRule(operator="equal", formula=['"Принят"'],
                   font=Font(color="FF117372"),
                   fill=PatternFill("solid", start_color="FFD4EDBC", end_color="FFD4EDBC")))
    ws.conditional_formatting.add(
        "H7:H{}".format(last_row),
        CellIsRule(operator="equal", formula=['"Передан в Верховный Суд"'],
                   font=Font(color="FF9D381B"),
                   fill=PatternFill("solid", start_color="FFFFC8AA", end_color="FFFFC8AA")))
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

    dv_status = DataValidation(type="list", allow_blank=True,
                               formula1='"На рассмотрении,Вето/отклонен Судом,Одобрен Судом,'
                                        'Подписан,Другое"')
    dv_status.add("I7:I{}".format(last_row))
    ws.add_data_validation(dv_status)

    ws.sheet_view.showGridLines = False
    wb.save(XLSX)
    print("OK", SHEET, "| строк повестки:", len(AGENDA), "| сенаторов:", len(SENATORS))


if __name__ == "__main__":
    sys.exit(build())
