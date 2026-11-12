# -*- coding: utf-8 -*-
"""Протокол заседания Сената 09.11.2026: два варианта.

Вариант А - постановление Сената от 12.11.2026 о подтверждении итогов.
Вариант Б - протокол, составленный 12.11.2026 по журналу голосований.
Оба собираются из образца заявления-инициативы (Book Antiqua, шапка Сената).
"""
import copy
import glob
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = glob.glob(os.path.join(ROOT, "*инициатива*(1).docx"))[0]
OUTDIR = os.path.join(ROOT, "Сенат", "Протокол заседания (09.11.2026)")
OUT_A = os.path.join(OUTDIR, "Вариант А - Постановление Сената о подтверждении итогов 09.11.2026.docx")
OUT_B = os.path.join(OUTDIR, "Вариант Б - Протокол заседания Сената 09.11.2026 (составлен 12.11.2026).docx")

# ---------------------------------------------------------------- состав
SENATORS = [
    ("Weazel News", "Jhonny Scoutezaki", "164317"),
    ("Weazel News", "Kasandriia Scout", "160955"),
    ("Полицейский департамент г. Лос-Сантос", "Afelia Suspect", "14077"),
    ("Полицейский департамент г. Лос-Сантос", "Socrat Wild", "96031"),
    ("Департамент шерифа о. Блэйн", "Marcus Nomad", "85028"),
    ("Департамент шерифа о. Блэйн", "Aliya Nomad", "131485"),
    ("Федеральное расследовательское бюро", "Eric Killa", "104068"),
    ("Федеральное расследовательское бюро", "Pravik Killa", "2759"),
    ("Национальная гвардия штата Сан-Андреас", "Asher Keat", "68553"),
    ("Национальная гвардия штата Сан-Андреас", "Hunter Keates", "122338"),
    ("Экстренная медицинская служба штата Сан-Андреас", "Kiray Fair", "37492"),
    ("Экстренная медицинская служба штата Сан-Андреас", "Himeno Kartonkina", "23899"),
    ("Правительство штата Сан-Андреас", "Maras Shakyr", "63823"),
    ("Правительство штата Сан-Андреас", "Meow Killa", "4638"),
    ("Консервативная партия «Патриоты Америки»", "Makima Killa", "864"),
    ("Республиканская партия «Возрождение»", "Jonny Zakonov", "55454"),
]

VOTES = [
    ("1", "Открытие заседания", "19:19", "19:33", "16", "0", "0", "9", "Принято"),
    ("2", "Освободить Tommy Harlow от должности Председателя (Спикера) Сената и закрыть заседание",
     "19:53", "20:53", "6", "6", "1", "9", "Не принято"),
    ("3", "Закрытие заседания", "19:53", "20:58", "5", "9", "0", "9", "Не принято"),
    ("4", "Освободить Tommy Harlow от должности Председателя (Спикера) Сената и избрать "
          "Marcus Nomad Председателем (Спикером) Сената",
     "20:15", "20:17", "14", "0", "0", "9", "Принято"),
]

BODY = "Book Antiqua"
DARK = RGBColor(0x1F, 0x1F, 0x1F)


# ---------------------------------------------------------------- утилиты
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


def set_center(el):
    pPr = el.find(qn("w:pPr"))
    if pPr is None:
        return el
    jc = pPr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        pPr.append(jc)
    jc.set(qn("w:val"), "center")
    return el


def set_bold(el):
    for r in el.findall(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr")
            r.insert(0, rPr)
        if rPr.find(qn("w:b")) is None:
            rPr.insert(0, OxmlElement("w:b"))
    return el


def borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "808080")
        b.append(el)
    tcPr.append(b)


def shade(cell, color="E8E8E8"):
    tcPr = cell._tc.get_or_add_tcPr()
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear")
    s.set(qn("w:color"), "auto")
    s.set(qn("w:fill"), color)
    tcPr.append(s)


def put(cell, text, bold=False, size=9, align="left"):
    cell.text = ""
    for r in list(cell.paragraphs[0].runs):
        r._r.getparent().remove(r._r)
    p = cell.paragraphs[0]
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
    pf = p.paragraph_format
    pf.space_before = Pt(1)
    pf.space_after = Pt(1)
    pf.line_spacing = 1.0
    r = p.add_run(text)
    r.bold = bold
    r.font.name = BODY
    r.font.size = Pt(size)
    r.font.color.rgb = DARK
    r._element.rPr.rFonts.set(qn("w:eastAsia"), BODY)
    borders(cell)


def table(doc, head, rows, widths, center_cols=()):
    t = doc.add_table(rows=1, cols=len(head))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    for i, h in enumerate(head):
        put(t.rows[0].cells[i], h, bold=True, align="center")
        shade(t.rows[0].cells[i])
        t.rows[0].cells[i].width = Cm(widths[i])
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            put(cells[i], v, align="center" if i in center_cols else "left")
            cells[i].width = Cm(widths[i])
    return t


def spacer(doc, pts=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(pts)
    p.paragraph_format.line_spacing = 1.0
    return p


# ---------------------------------------------------------------- сборка
def new_doc():
    doc = Document(SRC)
    ps = doc.paragraphs
    proto = {"title": ps[1]._p, "subtitle": ps[2]._p, "date": ps[3]._p,
             "body": ps[5]._p, "h1": ps[12]._p,
             "sign": [ps[24]._p, ps[25]._p, ps[26]._p]}
    sect = doc.element.body.find(qn("w:sectPr"))
    for p in doc.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    return doc, proto, sect


def push(sect, el):
    sect.addprevious(el)


def write_head(doc, proto, sect, title, subtitle, date_line):
    doc.paragraphs[0].runs[0].text = "СЕНАТ ШТАТА САН-АНДРЕАС"
    for key, txt in (("title", title), ("subtitle", subtitle), ("date", date_line)):
        push(sect, with_text(proto[key], txt))


def add_italic_note(sect, proto, text):
    el = with_text(proto["date"], text)
    for r in el.findall(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr")
            r.insert(0, rPr)
        if rPr.find(qn("w:i")) is None:
            rPr.append(OxmlElement("w:i"))
    pPr = el.find(qn("w:pPr"))
    if pPr is not None:
        jc = pPr.find(qn("w:jc"))
        if jc is not None:
            jc.set(qn("w:val"), "both")
    push(sect, el)


# ---------------------------------------------------------------- вариант А
def build_a():
    doc, proto, sect = new_doc()
    write_head(doc, proto, sect, "ПОСТАНОВЛЕНИЕ",
               "о подтверждении итогов пленарного заседания Сената штата Сан-Андреас",
               "12 ноября 2026 года, г. Лос-Сантос")

    push(sect, with_text(proto["body"],
         "Настоящим Сенат штата Сан-Андреас подтверждает сведения о проведении, составе "
         "Сената и результатах голосований пленарного заседания, состоявшегося 9 ноября "
         "2026 года, на основании журнала голосований, сохранившего время и результаты "
         "каждого опроса."))

    push(sect, with_text(proto["h1"], "ОСНОВАНИЯ"))
    for t in (
        "Часть 5 статьи 80 Конституции штата Сан-Андреас предусматривает, что общее число "
        "действующих сенаторов определяется председательствующим непосредственно перед "
        "началом каждого голосования и фиксируется в протоколе заседания с указанием "
        "оснований исключения сенаторов из подсчёта.",

        "В ходе заседания 9 ноября 2026 года отдельный протокол не составлялся. Сведения о "
        "составе Сената и результатах голосований сохранились в журнале голосований, "
        "содержащем время начала и завершения каждого опроса, число поданных голосов и "
        "распределение голосов.",

        "Восстановление утраченных сведений о заседании не изменяет содержания принятых на "
        "нём решений и не является их повторным принятием. Настоящее постановление "
        "подтверждает только фактическую сторону: кто заседал, сколько сенаторов было и как "
        "распределились голоса.",
    ):
        push(sect, with_text(proto["body"], t))

    push(sect, with_text(proto["h1"], "СОСТАВ СЕНАТА"))
    push(sect, with_text(proto["body"],
         "На момент открытия заседания действующими сенаторами являлись шестнадцать лиц, "
         "перечисленных ниже. Председательствующий Tommy Harlow полномочий сенатора не имел "
         "на основании части 3 статьи 3 Конституционного закона «О Сенате штата "
         "Сан-Андреас»."))
    table(doc, ["№", "Орган или партия", "Сенатор", "ID"],
          [(str(i), s[0], s[1], s[2]) for i, s in enumerate(SENATORS, 1)],
          [1.0, 7.5, 5.1, 2.1], center_cols=(0, 3))
    spacer(doc)

    push(sect, with_text(proto["h1"], "ГОЛОСОВАНИЯ"))
    table(doc, ["№", "Вопрос", "Начало", "Конец", "За", "Против", "Воздерж.", "Нужно", "Итог"],
          VOTES, [0.7, 5.7, 1.2, 1.2, 0.9, 1.3, 1.5, 1.3, 1.9],
          center_cols=(0, 2, 3, 4, 5, 6, 7, 8))
    spacer(doc)
    push(sect, with_text(proto["body"],
         "Порог принятия решения - девять голосов: половина от шестнадцати составляет восемь, "
         "требуется превышение, то есть девять (часть 5 статьи 80 Конституции штата "
         "Сан-Андреас)."))

    push(sect, with_text(proto["h1"], "СЕНАТ ПОСТАНОВЛЯЕТ"))
    for t in (
        "1. Подтвердить сведения о проведении, составе Сената и результатах голосований "
        "пленарного заседания Сената штата Сан-Андреас от 9 ноября 2026 года согласно "
        "таблицам, приведённым в настоящем постановлении.",

        "2. Установить, что общее число действующих сенаторов на момент открытия заседания "
        "составляло шестнадцать, для принятия решения требовалось девять голосов.",

        "3. Установить, что после избрания Marcus Nomad Председателем (Спикером) Сената "
        "штата Сан-Андреас он утратил полномочия сенатора на основании части 3 статьи 3 "
        "Конституционного закона «О Сенате штата Сан-Андреас», в связи с чем общее число "
        "действующих сенаторов сократилось до пятнадцати.",

        "4. Признать, что результаты голосований, приведённые в настоящем постановлении, не зависят от "
        "способа подсчёта: при шестнадцати действующих сенаторах порог составляет девять "
        "голосов, при пятнадцати - восемь; решение об избрании Marcus Nomad Председателем "
        "(Спикером) Сената принято четырнадцатью голосами при любом из указанных порогов.",

        "5. Настоящее постановление вступает в силу с момента принятия и действует "
        "непосредственно (часть 1 статьи 11 Конституционного закона «О Сенате штата "
        "Сан-Андреас»).",
    ):
        push(sect, with_text(proto["body"], t))

    push(sect, with_text(proto["h1"], "ПРИМЕЧАНИЕ"))
    push(sect, with_text(proto["body"],
         "Настоящее постановление составлено 12 ноября 2026 года и не является протоколом, "
         "составленным в ходе заседания. Оно фиксирует восстановленные сведения и не "
         "заменяет журнал голосований, который хранится в неизменном виде."))

    push(sect, with_text(proto["sign"][0], "Председатель (Спикер) Сената"))
    push(sect, with_text(proto["sign"][1], "Marcus Nomad"))
    push(sect, with_text(proto["sign"][2], "штата Сан-Андреас"))
    push(sect, with_text(proto["sign"][0], "12 ноября 2026 года"))

    for p in doc.sections[0].footer.paragraphs:
        for r in list(p.runs):
            if r._r.find(qn("w:drawing")) is not None and r._r.find(qn("w:t")) is None:
                r._r.getparent().remove(r._r)

    cp = doc.core_properties
    cp.author = "Marcus Nomad"
    cp.last_modified_by = "Marcus Nomad"
    cp.title = "Постановление Сената о подтверждении итогов заседания 09.11.2026"
    cp.subject = "Пленарное заседание 9 ноября 2026 года"
    doc.save(OUT_A)
    print("OK", OUT_A)


# ---------------------------------------------------------------- вариант Б
def build_b():
    doc, proto, sect = new_doc()
    write_head(doc, proto, sect, "ПРОТОКОЛ",
               "пленарного заседания Сената штата Сан-Андреас",
               "9 ноября 2026 года, г. Лос-Сантос")
    add_italic_note(sect, proto,
                    "Составлен 12 ноября 2026 года по журналу голосований. "
                    "В ходе заседания протокол не велся.")

    push(sect, with_text(proto["h1"], "I. МЕСТО, ВРЕМЯ И ФОРМА ПРОВЕДЕНИЯ"))
    for t in (
        "Место проведения - зал заседаний Сената штата Сан-Андреас, г. Лос-Сантос.",
        "Дата проведения - 9 ноября 2026 года. Заседание назначено 7 ноября 2026 года.",
        "Форма проведения - пленарное заседание с голосованием через электронную систему "
        "опроса.",
        "Заседание открыто в 19:19 и признано правомочным: в голосовании об открытии "
        "участвовали шестнадцать сенаторов, что превышает половину общего числа действующих "
        "сенаторов (часть 1 статьи 9 Конституционного закона «О Сенате штата Сан-Андреас»).",
        "Председательствующий - Tommy Harlow, Председатель (Спикер) Сената штата "
        "Сан-Андреас, паспорт 98650. Полномочий сенатора не имел на основании части 3 "
        "статьи 3 Конституционного закона «О Сенате штата Сан-Андреас».",
    ):
        push(sect, with_text(proto["body"], t))

    push(sect, with_text(proto["h1"], "II. СОСТАВ СЕНАТА"))
    push(sect, with_text(proto["body"],
         "Общее число действующих сенаторов на момент открытия заседания - шестнадцать. "
         "Оснований для исключения сенаторов из подсчёта не устанавливалось."))
    table(doc, ["№", "Орган или партия", "Сенатор", "ID"],
          [(str(i), s[0], s[1], s[2]) for i, s in enumerate(SENATORS, 1)],
          [1.0, 7.5, 5.1, 2.1], center_cols=(0, 3))
    spacer(doc)

    push(sect, with_text(proto["h1"], "III. ВОПРОСЫ, ПОСТАВЛЕННЫЕ НА ГОЛОСОВАНИЕ"))
    for t in (
        "1. Открытие заседания - внесён председательствующим в 19:19.",
        "2. Досрочное освобождение Tommy Harlow от должности Председателя (Спикера) Сената "
        "и закрытие заседания - внесён председательствующим в 19:53.",
        "3. Закрытие заседания - внесён председательствующим в 19:53.",
        "4. Досрочное освобождение Tommy Harlow от должности Председателя (Спикера) Сената и "
        "избрание Marcus Nomad Председателем (Спикером) Сената - внесён председательствующим "
        "в 20:15.",
        "Инициатива сенатора Jonny Zakonov об избрании Председателя Сената и его заместителя "
        "на голосование не ставилась. Инициатива опубликована в разделе предложений Сената "
        "9 ноября 2026 года в 19:00 и повторно в 19:43. Подписей более чем половины "
        "действующих сенаторов под инициативой не имелось, в связи с чем обязанность "
        "включить её в повестку дня в качестве внеочередного вопроса, предусмотренная частью "
        "4 статьи 9 Конституционного закона «О Сенате штата Сан-Андреас», не возникла.",
    ):
        push(sect, with_text(proto["body"], t))

    push(sect, with_text(proto["h1"], "IV. РЕЗУЛЬТАТЫ ГОЛОСОВАНИЙ"))
    table(doc, ["№", "Вопрос", "Начало", "Конец", "За", "Против", "Воздерж.", "Нужно", "Итог"],
          VOTES, [0.7, 5.7, 1.2, 1.2, 0.9, 1.3, 1.5, 1.3, 1.9],
          center_cols=(0, 2, 3, 4, 5, 6, 7, 8))
    spacer(doc)
    push(sect, with_text(proto["body"],
         "Порог принятия решения - девять голосов: половина от шестнадцати составляет восемь, "
         "требуется превышение, то есть девять (часть 5 статьи 80 Конституции штата "
         "Сан-Андреас)."))

    push(sect, with_text(proto["h1"], "V. РЕШЕНИЯ"))
    for t in (
        "1. Заседание открыто и признано правомочным.",
        "2. Предложение о досрочном освобождении Tommy Harlow от должности Председателя "
        "(Спикера) Сената и закрытии заседания не принято: шесть голосов «за», шесть "
        "«против», один «воздержался» при необходимых девяти.",
        "3. Предложение о закрытии заседания не принято: пять голосов «за», девять «против» "
        "при необходимых девяти. Заседание продолжено.",
        "4. Tommy Harlow досрочно освобождён от должности Председателя (Спикера) Сената, "
        "Marcus Nomad избран Председателем (Спикером) Сената штата Сан-Андреас: четырнадцать "
        "голосов «за», ноль «против», ноль «воздержавшихся» при необходимых девяти. Решение "
        "принято единогласно.",
        "5. Полномочия Председателя (Спикера) Сената переданы Marcus Nomad в 20:19.",
    ):
        push(sect, with_text(proto["body"], t))

    push(sect, with_text(proto["h1"], "VI. ОСОБЫЕ ОТМЕТКИ"))
    for t in (
        "В 19:45 председательствующий потребовал от сотрудников Секретной службы вывести "
        "сенатора Jonny Zakonov из зала заседаний. Требование основано на пункте «и» части 4 "
        "статьи 3 и части 4 статьи 15 Конституционного закона «О Сенате штата Сан-Андреас». "
        "Предупреждение не выносилось.",

        "После вывода из зала сенатор Jonny Zakonov вернулся в зал заседаний по "
        "собственному решению. Распоряжение председательствующего об освобождении помещения "
        "им не исполнено.",

        "В 20:10 в зале заседаний сенатор Jonny Zakonov применил наручники к сотруднику "
        "Секретной службы, осуществлявшему сопровождение Губернатора штата Сан-Андреас. "
        "Сотрудник был освобождён через 30 секунд. Начальство сотрудника и сотрудник Офиса "
        "Генерального прокурора не вызывались (статья 19 Процессуального кодекса штата "
        "Сан-Андреас).",

        "В 20:15 сенатор Jonny Zakonov участвовал в голосовании об избрании Marcus Nomad "
        "Председателем (Спикером) Сената. Решение об отстранении сенатора от участия в "
        "заседании не принималось, полномочия сенатора не приостанавливались.",
    ):
        push(sect, with_text(proto["body"], t))

    push(sect, with_text(proto["h1"], "VII. ПОРЯДОК СОСТАВЛЕНИЯ"))
    push(sect, with_text(proto["body"],
         "Настоящий протокол составлен 12 ноября 2026 года, после окончания заседания, на "
         "основании журнала голосований, содержащего время и результаты каждого опроса. "
         "Записи в журнал голосований не вносились и не изменялись. Протокол не является "
         "документом, составленным в ходе заседания, и не заменяет журнал голосований."))
    push(sect, with_text(proto["body"],
         "Сведения об отсутствии предупреждения, о возврате в зал заседаний и о применении "
         "наручников внесены на основании видеозаписей, указанных в приложении к настоящему "
         "протоколу."))

    push(sect, with_text(proto["h1"], "ПРИЛОЖЕНИЕ"))
    for t in (
        "1. Журнал голосований пленарного заседания 9 ноября 2026 года.",
        "2. Видеозапись заседания: https://youtu.be/FhIWsJXvVP4.",
        "3. Видеозапись, представленная сенатором Jonny Zakonov: "
        "https://www.youtube.com/watch?v=d_sLY2Ty6XQ (запись начата в 19:45:26).",
    ):
        push(sect, with_text(proto["body"], t))

    push(sect, with_text(proto["sign"][0], "Председатель (Спикер) Сената"))
    push(sect, with_text(proto["sign"][1], "Marcus Nomad"))
    push(sect, with_text(proto["sign"][2], "штата Сан-Андреас"))
    push(sect, with_text(proto["sign"][0], "12 ноября 2026 года"))

    for p in doc.sections[0].footer.paragraphs:
        for r in list(p.runs):
            if r._r.find(qn("w:drawing")) is not None and r._r.find(qn("w:t")) is None:
                r._r.getparent().remove(r._r)

    cp = doc.core_properties
    cp.author = "Marcus Nomad"
    cp.last_modified_by = "Marcus Nomad"
    cp.title = "Протокол пленарного заседания Сената 09.11.2026"
    cp.subject = "Пленарное заседание 9 ноября 2026 года"
    doc.save(OUT_B)
    print("OK", OUT_B)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    build_a()
    build_b()


if __name__ == "__main__":
    main()
