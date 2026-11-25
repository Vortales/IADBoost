# -*- coding: utf-8 -*-
"""Собрать восстановленные протоколы к делу № 105 из сохранённых сведений.

Это новые документы, а не подлинники, составленные на заседаниях. Результаты и
состав по спорным источникам специально не объединяются в «бесспорную» версию.
Исходные файлы не перезаписываются. Существующие выходные DOCX защищены от
перезаписи: для явного пересоздания нужен --force. Требуется python-docx.
"""
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import quote

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parent.parent
OUT = (ROOT / 'Компромат на Jonny Zakonov' / 'Текущая работа' /
       'Иск № 105 и связанные дела' / 'Ответ суду и протоколы')
HEAD = 'dc0700a7efaf35d0ddc0e11e3a4da5ede64fbe2a'
OLD = 'f60265bdf5d45a9dc2082daa6ca351340f5b04be'


def git_source(path, revision=HEAD, anchor=''):
    return f'https://github.com/Vortales/IADBoost/blob/{revision}/{quote(path, safe="/")}{anchor}'


HISTORY = git_source('Замена сенатора (история с датами).txt')
REG_OLD = git_source('Компромат на Jonny Zakonov/Обращения и жалобы от Jonny Zakonov/4/Единый реестр Штата Сан-Андреас.xlsx')
REG_LATER = git_source('Компромат на Jonny Zakonov/Единый реестр Штата Сан-Андреас.xlsx')
JOURNAL_13 = git_source('Повестка/13.11.2026/05 Журнал/The Senate of San Andreas 19.xlsx')
JOURNAL_19 = git_source('Повестка/19.11.2026/04 Журнал/The Senate of San Andreas 19 - 19.11.2026.xlsx')
DRAFT_09 = git_source('Сенат/Протокол заседания (09.11.2026)/Вариант Б - Протокол заседания Сената 09.11.2026 (составлен 12.11.2026).docx')
ARCHIVE = git_source('Компромат на Jonny Zakonov/Текущая работа/Общие исходные материалы из архива/Discord голосования.md')
LAW = git_source('Законодательная база/Конституция штата Сан-Андреас.json', OLD)
CHANNEL = 'https://discord.com/channels/1514607659758653560/1515423283606982776'
TOPIC_09 = 'https://discord.com/channels/1514607659758653560/1569385787621900359'
TOPIC_13 = 'https://discord.com/channels/1514607659758653560/1570830679107706950'
TOPIC_19 = 'https://discord.com/channels/1514607659758653560/1573006980019130522'
RESULT_09 = 'https://forum.majestic-rp.ru/posts/11776655/'
RESULT_13 = 'https://forum.majestic-rp.ru/posts/11793679/'
RESULT_19 = 'https://forum.majestic-rp.ru/posts/11822528/'

# Этот список находится в проекте, составленном 12.11, а не в подтверждённом
# первичном журнале 09.11. В частности, назначения SANG известны из сообщений 10.11.
ROSTER_09 = [
    ('Weazel News', 'Jhonny Scoutezaki', '164317'),
    ('Weazel News', 'Kasandriia Scout', '160955'),
    ('LSPD', 'Afelia Suspect', '14077'),
    ('LSPD', 'Socrat Wild', '96031'),
    ('LSCSD', 'Marcus Nomad', '85028'),
    ('LSCSD', 'Aliya Nomad', '131485'),
    ('FIB', 'Eric Killa', '104068*'),
    ('FIB', 'Pravik Killa', '2759'),
    ('SANG', 'Asher Keat', '68553**'),
    ('SANG', 'Hunter Keates', '122338**'),
    ('EMS', 'Kiray Fair', '37492'),
    ('EMS', 'Himeno Kartonkina', '23899'),
    ('Government', 'Maras Shakyr', '63823*'),
    ('Government', 'Meow Killa', '4638'),
    ('Партия «Патриоты Америки»', 'Makima Killa', '864'),
    ('Партия «Возрождение»', 'Jonny Zakonov', '55454'),
]

# Перечень имён именно из заранее заполненного листа 13.11, а не отметки явки.
ROSTER_13 = [
    ('Weazel News', 'Jhonny Scoutezaki', '164317'),
    ('Weazel News', 'Dmitry Grayrat', '40117'),
    ('LSPD', 'Afelia Suspect', '14077'),
    ('LSPD', 'Socrat Wild', '96031'),
    ('LSCSD', 'Umka Nomad', '87727'),
    ('LSCSD', 'Aliya Nomad', '131485'),
    ('FIB', 'Eric Killa', '104068*'),
    ('FIB', 'Kennych Killa', '49429'),
    ('SANG', 'Asher Keat', '68553'),
    ('SANG', 'Hunter Keates', '122338'),
    ('EMS', 'Kiray Fair', '37492'),
    ('EMS', 'Himeno Kartonkina', '23899'),
    ('Government', 'Maras Shakyr', '63823*'),
    ('Government', 'Meow Killa', '4638'),
    ('Партия «Патриоты Америки»', 'Makima Killa', '864'),
    ('Партия «Возрождение»', 'Merkylka Fair', '62277'),
]

# Поздний срез реестра без подтверждённой истории на момент 19.11.
ROSTER_19 = [
    ('Weazel News', 'Jhonny Scoutezaki', '164317'),
    ('Weazel News', 'Dmitry Grayrat', '40117'),
    ('LSPD', 'Socrat Wild', '96031'),
    ('LSCSD', 'Sanya Nomad', '64890'),
    ('LSCSD', 'Aliya Nomad', '131485'),
    ('FIB', 'Eric Killa', '64370*'),
    ('FIB', 'Jacob Killa', '57474'),
    ('SANG', 'Asher Keat', '68553'),
    ('SANG', 'Hunter Keates', '122338'),
    ('EMS', 'Nansy Casta', '155707'),
    ('EMS', 'Himeno Kartonkina', '23899'),
    ('Government', 'Nine Killua', '43317*'),
    ('Government', 'Styort Killa', '4701'),
    ('Офис Генерального прокурора', 'Pravik Killaz', '91999'),
    ('Вице-губернатор', 'Qwikus Killa', '11736'),
    ('Партия «Патриоты Америки»', 'Makima Killa', '864'),
]

# Временные интервалы помещаются в одной строке даже при подстановке шрифта.
VOTE_WIDTHS = [2.7, 5.8, 1.8, 2.7, 4.1]

# Время 09.11 - отметка сообщения во вторичной выгрузке, не время закрытия опроса.
VOTES_09 = [
    ('19:19:15', 'Открытие заседания', '16*', '16 / 0 / 0', 'По выгрузке'),
    ('19:22:25', 'Тема заявления об освобождении Спикера; вопрос «Голосование»', '?', '6 / 7 / 1', 'Статус не установлен'),
    ('19:33:45', 'Освобождение Tommy Harlow и закрытие заседания', '?', '5 / 6 / 2', 'По выгрузке'),
    ('19:53:48', 'Освобождение Tommy Harlow и закрытие заседания', '?', '6 / 6 / 1', 'По выгрузке'),
    ('19:58:50', 'Закрытие заседания', '?', '5 / 9 / 0', 'По выгрузке'),
    ('20:15:36', 'Освобождение Tommy Harlow и избрание Marcus Nomad Спикером', '16*', '14 / 0 / 0', 'По выгрузке'),
    ('20:23:29', 'ACT. 277', '14**', '8 / 3 / 2', 'Принят по итогам'),
    ('20:38:57', 'ACT. 278', '14**', '9 / 4 / 1', 'Принят по итогам'),
    ('20:44:06', 'ACT. 279', '14**', '11 / 2 / 1', 'Принят по итогам'),
    ('20:47:00', 'ACT. 280 (в выгрузке вопрос «80»)', '14**', '11 / 1 / 2', 'Принят по итогам'),
    ('20:50:17', 'ACT. 282', '14**', '12 / 0 / 2', 'Принят по итогам'),
    ('20:57:27', 'Инициатива о ЦИК', '14**', '7 / 6 / 0***', 'Не принята по итогам'),
    ('21:02:01', 'ACT. 283', '14**', '7 / 5 / 1', 'Не принят по итогам'),
    ('21:12:10', 'ACT. 284', '14**', '11 / 1 / 1', 'Принят по итогам'),
    ('21:19:23', 'ACT. 285', '14**', '12 / 0 / 1', 'Принят по итогам'),
    ('21:22:32', 'Тема «Закрытие Сената»; вопрос не распознан', '?', '14 / 0 / 0', 'По выгрузке'),
]

# Время и результаты - опубликованные итоги соответствующей даты, точность до минуты.
VOTES_13 = [
    ('19:00-19:05', 'Открытие заседания', '16', '13 / 0 / 1', 'Открыто'),
    ('19:08-19:10', 'Инициатива о Jonny Zakonov и партии «Возрождение»', '16', '10 / 2 / 3', 'Поддержана'),
    ('19:13-19:14', 'Инициатива Губернатора о составе ЦИК', '15', '10 / 2 / 3', 'Поддержана'),
    ('19:21-19:23', 'ACT. 286', '15', '5 / 9 / 1', 'Не принят'),
    ('19:25-19:27', 'ACT. 287', '15', '10 / 0 / 2', 'Принят'),
    ('19:29-19:30', 'ACT. 288', '15', '10 / 0 / 1', 'Принят'),
    ('19:31-19:34', 'ACT. 298', '15', '10 / 0 / 2', 'Принят'),
    ('19:34-19:40', 'ACT. 289', '15', '9 / 0 / 3', 'Принят'),
    ('19:41-19:42', 'ACT. 290', '15', '10 / 0 / 0', 'Принят'),
    ('19:45-19:48', 'ACT. 291', '15', '3 / 0 / 8', 'Не принят'),
    ('19:48-19:50', 'ACT. 292', '15', '10 / 0 / 1', 'Принят'),
    ('19:50-19:53', 'ACT. 293', '15', '9 / 0 / 2', 'Принят'),
    ('19:56-20:22', 'ACT. 294', '15', '2 / 1 / 8', 'Не принят'),
    ('20:24-20:54', 'ACT. 295', '15', '1 / 0 / 10', 'Не принят'),
    ('20:33-20:54', 'ACT. 296', '15', '8 / 0 / 1', 'Принят'),
    ('20:35-20:42', 'ACT. 297', '15', '8 / 0 / 2', 'Принят'),
    ('20:45-20:52', 'Избрание Afelia Suspect Вице-Спикером', '15', '8 / 0 / 0', 'Избрана'),
    ('20:53-20:54', 'Закрытие заседания', '14', '9 / 0 / 0', 'Закрыто'),
]

VOTES_19 = [
    ('19:08-19:11', 'Открытие заседания', '16', '13 / 0 / 0', 'Открыто'),
    ('19:18-19:19', 'ACT. 299 и ACT. 300 - общий опрос', '16', '4 / 8 / 1', 'Не приняты'),
    ('19:28-19:33', 'ACT. 301', '16', '4 / 7 / 1', 'Не принят'),
    ('19:34-19:35', 'ACT. 303', '16', '1 / 10 / 0', 'Не принят'),
    ('19:36-19:43', 'ACT. 308', '16', '10 / 1 / 3', 'Принят Сенатом'),
    ('19:38-19:44', 'Инициатива о замене члена ЦИК', '16', '9 / 1 / 0', 'Поддержана'),
    ('19:39-19:43', 'ACT. 309', '16', '12 / 1 / 1', 'Принят Сенатом'),
    ('19:44-19:48', 'Закрытие заседания', '16', '10 / 1 / 1', 'Закрыто'),
]


def font(run, size=10.5, bold=False, color='202C28'):
    run.font.name = 'Times New Roman'
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def setup(date):
    doc = Document()
    # Шаблон python-docx содержит даты 2013 года. Они не относятся к этому
    # документу; не выдаём их за дату подготовки реконструкции.
    props = doc.core_properties
    for tag in ('dcterms:created', 'dcterms:modified'):
        element = props._element.find(qn(tag))
        if element is not None:
            props._element.remove(element)
    props.author = ''
    props.title = f'Восстановленный протокол заседания Сената {date}'
    props.subject = 'Последующая реконструкция по сохранившимся материалам'
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(1.75), Cm(1.65)
    section.left_margin, section.right_margin = Cm(1.8), Cm(1.8)
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.07
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(footer.add_run(f'СЕНАТ ШТАТА САН-АНДРЕАС  |  {date}  |  стр. '), 8, color='687A71')
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), 'PAGE')
    footer._p.append(fld)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run('СЕНАТ ШТАТА САН-АНДРЕАС'), 10, True, '34604A')
    p.paragraph_format.space_after = Pt(4)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run('ПРОТОКОЛ ЗАСЕДАНИЯ СЕНАТА'), 16, True, '173D2B')
    p.paragraph_format.space_after = Pt(1)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run(f'{date}  |  г. Лос-Сантос'), 11, True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run('Восстановлен по сохранившимся материалам для представления суду'), 10, True, '74552A')
    p.paragraph_format.space_after = Pt(8)
    return doc


def paragraph(doc, text, bold_lead=None):
    p = doc.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        font(p.add_run(bold_lead), bold=True)
        font(p.add_run(text[len(bold_lead):]))
    else:
        font(p.add_run(text))
    return p


def heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(4)
    font(p.add_run(text.upper()), 11, True, '285942')


def cell_text(cell, text, bold=False, small=False):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.0
    font(p.add_run(str(text)), 8.5 if small else 9, bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.style = 'Table Grid'
    # Задаём как сетку, так и ширину ячеек: иначе Word может сохранить в
    # tblGrid равные столбцы и проигнорировать заданные для ячеек пропорции.
    for column, width in zip(t.columns, widths):
        column.width = Cm(width)
    for i, (cell, width) in enumerate(zip(t.rows[0].cells, widths)):
        cell.width = Cm(width)
        cell_text(cell, headers[i], True, True)
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), 'E5EEE8')
        cell._tc.get_or_add_tcPr().append(shading)
    trpr = t.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement('w:tblHeader')
    repeat.set(qn('w:val'), 'true')
    trpr.append(repeat)
    for row in rows:
        cells = t.add_row().cells
        for cell, value, width in zip(cells, row, widths):
            cell.width = Cm(width)
            cell_text(cell, value, small=True)
        trpr = t.rows[-1]._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def link(doc, label, url):
    p = doc.add_paragraph(style='Normal')
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.space_after = Pt(2)
    relationship = doc.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement('w:hyperlink')
    h.set(qn('r:id'), relationship)
    run = OxmlElement('w:r')
    properties = OxmlElement('w:rPr')
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '176347')
    properties.append(color)
    underline = OxmlElement('w:u')
    underline.set(qn('w:val'), 'single')
    properties.append(underline)
    run.append(properties)
    text = OxmlElement('w:t')
    text.text = label
    run.append(text)
    h.append(run)
    p._p.append(h)


def final_signature(doc):
    heading(doc, 'Подтверждение составителя')
    paragraph(doc, 'Документ подготовлен после заседания по перечисленным материалам. '
              'Он не подтверждает, что именно эта редакция велась или подписывалась во время заседания, '
              'и не заменяет первичные записи голосований, подлинники решений и доказательства явки.')
    paragraph(doc, 'Дата подготовки восстановленной версии: ____________________.')
    paragraph(doc, 'Спикер Сената: Marcus Nomad, номер паспорта 85028 (после проверки полномочий и сведений).')
    paragraph(doc, 'Подпись: ____________________    Дата подписания: ____________________')


def roster_table(doc, roster, mode):
    if mode == '13':
        rows = [(org, f'{name}\n{number}', 'Не явился*' if name == 'Merkylka Fair' else 'Присутствовал*')
                for org, name, number in roster]
        table(doc, ['Орган / партия', 'Указанное лицо / номер паспорта', 'Явка по пояснению*'], rows, [5.1, 6.7, 5.3])
    else:
        rows = [(org, f'{name}\n{number}', 'Не установлена') for org, name, number in roster]
        table(doc, ['Орган / партия', 'Лицо в источнике / номер паспорта', 'Фактическая явка'], rows, [5.1, 6.7, 5.3])


def common_source_note(doc):
    paragraph(doc, 'Число действующих сенаторов для подсчёта не тождественно числу присутствующих или голосовавших. '
              'Неявка, опоздание и воздержание сами по себе не являются основанием исключения из состава. '
              'Основания исключения и применимая на дату редакция закона подлежат проверке.')


def build_09():
    d = setup('9 ноября 2026 года')
    heading(d, '1. Происхождение и порядок восстановления')
    paragraph(d, 'Настоящий протокол составлен после заседания по опубликованным итогам, '
              'сохранённой вторичной выгрузке электронных голосований и проекту протокола от 12 ноября. '
              'Статус подписанного оригинала проекта 12 ноября не подтверждён. Этот документ не является '
              'заверенной копией протокола, который вёлся во время заседания.')
    paragraph(d, 'Заседание назначалось на 09.11.2026 в 19:00. По доступным материалам сначала '
              'председательствовал Tommy Harlow, затем Marcus Nomad; объём их полномочий и законность созыва '
              'оспариваются и должны оцениваться с учётом решения суда по делу № 97.')
    heading(d, '2. Состав и явка')
    paragraph(d, 'В неподтверждённом проекте 12.11 перечислены 16 лиц. Ниже приведён именно его список, '
              'а не проверенный поимённый список явки или бесспорный состав на 09.11. Голосование 16 '
              'учётных записей об открытии не заменяет проверку личности, мандатов и присутствия.')
    roster_table(d, ROSTER_09, '09')
    paragraph(d, '* В источниках есть расхождения: Eric Killa указан с номерами 104068 и 64370; '
              'номер 63823 встречается при обозначениях Maras Shakyr и Gogal Killaz. Тождество и право голоса требуют проверки. '
              '** Заявления о представителях SANG Asher Keat и Hunter Keates в истории датированы 10.11; '
              'их включение в проект за 09.11 не подтверждает полномочия на 09.11.')
    paragraph(d, 'В истории заявлений указаны замены 09.11: EMS - Enzo Casta → Kiray Fair в 18:23 '
              'и Marco Casta → Himeno Kartonkina в 18:38; Government - Pravik Killa → Maras Shakyr '
              'в 18:57; FIB - Eric Killa → Pravik Killa в 19:03 и Kennych Killa → Eric Killa '
              'в 20:24. Это время заявлений, а не подтверждение их исполнения; совпадение имени '
              'Pravik в заявлениях от разных органов и номера 63823 требует отдельной проверки.')
    paragraph(d, 'Проект 12.11 указывает 16 сенаторов до избрания Marcus и 15 после его избрания. '
              'Опубликованные итоги по законопроектам указывают 14 действующих сенаторов. '
              'Основание и момент перехода от 15 к 14 по имеющимся копиям не установлены; '
              '14 нельзя автоматически считать доказанным числом перед каждым голосованием.')
    common_source_note(d)
    heading(d, '3. Зафиксированные голосования')
    paragraph(d, 'В таблице указано время сообщения в архивной выгрузке (MSK, UTC+3), '
              'а не доказанное время начала или окончания опроса. Итоги - по указанному в строке источнику. '
              'Состав: 16* - по проекту 12.11; 14** - общее число в опубликованных итогах, точный момент не установлен; '
              '«?» - число перед данным голосованием не установлено.')
    table(d, ['Отметка', 'Вопрос', 'Состав', 'За / против / возд.', 'Сведения'], VOTES_09, VOTE_WIDTHS)
    paragraph(d, 'Выгрузка указывает по открытию 16 видимых учётных записей «за»: '
              'pravikkk, pifpafo, insideofdead, socrat_1hp, izverus, chiefgov, xaqqk, '
              'kasandriia, voblovna, sky_992, afeliami, jhonnyycc, .h1meno., al.zaru, .gogal, uhge. '
              'Это список аккаунтов в конкретном опросе, а не удостоверенный поимённый список явки.')
    paragraph(d, 'По объединённому вопросу об избрании видимые записи «за»: pravikkk, insideofdead, '
              'socrat_1hp, izverus, chiefgov, xaqqk, kasandriia, voblovna, afeliami, jhonnyycc, '
              '.h1meno., al.zaru, .gogal, uhge. Отсутствие аккаунта в этом опросе не доказывает '
              'неявку его владельца на заседание.')
    paragraph(d, 'Проект протокола 12.11 указывает окончание двух вопросов об освобождении Harlow '
              'и закрытии в 20:53 и 20:58; в выгрузке сообщения по вопросам с теми же результатами '
              'имеют отметки 19:53:48 и 19:58:50. Совпадение опросов, часовые пояса и причину '
              'расхождения необходимо проверить; время сообщения не устанавливает время окончания.')
    paragraph(d, '*** По ЦИК опубликовано 7 / 6 / 0, старый исходный список содержит 7 / 6 / 1, '
              'архивная выгрузка одноимённого опроса - 8 / 6 / 0. Тождество опросов и причину '
              'расхождения следует проверить по оригиналам. ACT. 281 в итогах указан отозванным.')
    paragraph(d, 'По объединённому вопросу об освобождении Tommy Harlow и избрании Marcus Nomad '
              'в архивной выгрузке отражены 14 голосов «за», 0 «против», 0 «воздержался». '
              'Это не отдельный подписанный акт об избрании и не проверенный оригинал опроса. '
              'Пункт 3.3 опубликованных итогов указывает, что итоги не заменяют протокол.')
    paragraph(d, 'По словам Marcus Nomad, учётная запись uhge относится к Jonny Zakonov; она указана '
              'среди голосовавших «за» по объединённому вопросу. Независимое соответствие аккаунта '
              'лицу не подтверждено. Учётная запись jhonnyycc не отождествляется здесь с Jonny Zakonov.')
    heading(d, '4. Источники и приложения для проверки')
    link(d, 'Опубликованные итоги 09.11', RESULT_09)
    link(d, 'Вторичная выгрузка голосований и список видимых аккаунтов', ARCHIVE)
    link(d, 'Тема заседания и объединённый вопрос об избрании', TOPIC_09)
    link(d, 'Канал электронных голосований', CHANNEL)
    link(d, 'Проект протокола 09.11, составленный 12.11; статус подписания не подтверждён', DRAFT_09)
    link(d, 'История заявлений о замене представителей', HISTORY)
    link(d, 'Срез Конституции: ч. 5 ст. 80 (редакцию на дату необходимо проверить)', LAW)
    link(d, 'Указ № 0012 о назначении заседания', 'https://forum.majestic-rp.ru/threads/kabinet-spiker-senata.3364868/post-11768805')
    link(d, 'Решение суда по делу № 97', 'https://forum.majestic-rp.ru/posts/11830060/')
    link(d, 'Видеозапись 1 - содержание и полнота независимо не проверены', 'https://www.youtube.com/watch?v=FhIWsJXvVP4')
    link(d, 'Видеозапись 2 - содержание и полнота независимо не проверены', 'https://www.youtube.com/watch?v=d_sLY2Ty6XQ')
    final_signature(d)
    return d


def build_13():
    d = setup('13 ноября 2026 года')
    heading(d, '1. Источники и порядок восстановления')
    paragraph(d, 'Документ составлен после заседания по опубликованным итогам, сохранённой переписке '
              'о голосованиях, проекту протокола и подготовленному листу журнала. Лист содержит '
              '16 предварительно внесённых имён, включая Merkylka, под заголовком «Сенаторы на заседании»; '
              'общее число явившихся и отдельные отметки не заполнены. Если считать список отметкой явки, '
              'включение Merkylka расходится с приведённым ниже пояснением. Председательствующий по итогам - '
              'Спикер Marcus Nomad, номер паспорта 85028.')
    heading(d, '2. Предварительный состав и сведения о явке')
    paragraph(d, 'По пояснению Спикера, из сенаторов не явилась только Merkylka Fair; остальные '
              'сенаторы присутствовали. Ниже перечислены лица из подготовленного листа журнала 13.11. '
              'Их персональные отметки следуют из этого общего пояснения только при условии подтверждения, '
              'что именно они входили в состав в соответствующее время. Журнал не содержит независимых '
              'отметок явки, а одно заявление о замене не подтверждает момент её исполнения.')
    roster_table(d, ROSTER_13, '13')
    paragraph(d, '* «Присутствовал» / «не явился» - сведения по пояснению Спикера, не отметки '
              'первичной регистрации. Eric Killa обозначен номером 104068 в старом реестре и 64370 '
              'в истории заявлений. Номер 63823 встречается при обозначениях Maras Shakyr и Gogal Killaz; '
              'сопоставление лиц и актуальных мандатов следует подтвердить.')
    paragraph(d, 'В истории заявлены замены: Jonny Zakonov → Merkylka Fair 11.11 в 10:30; '
              'Marcus Nomad → Sanya Nomad 12.11 в 18:19; 13.11 Pravik Killa → Kennych Killa '
              'в 17:00, Kasandriia Scout → Dmitry Grayrat в 17:17 и Sanya Nomad → Umka Nomad '
              'в 17:21. Отдельно 13.11 в 20:52 заявлена замена от Government '
              'Gogal Killaz, номер 63823, → Qwikus Killa. Она совпадает с периодом нескольких '
              'голосований. Время внесения каждой замены в реестр и её правовые последствия '
              'по представленным копиям не подтверждены.')
    common_source_note(d)
    heading(d, '3. Число для подсчёта и результаты')
    paragraph(d, 'Опубликованные итоги указывают: до голосования о Jonny и партии - 16, после него - 15, '
              'после избрания Afelia Suspect Вице-Спикером - 14. Сокращение с 16 до 15 связывается '
              'в итогах с принятыми мерами; представитель партии, основания и правомерность исключения '
              'требуют проверки. Само отсутствие Merkylka не исключало её из числа действующих сенаторов.')
    paragraph(d, 'Состав в таблице воспроизводит подготовленный проект: определяется перед началом '
              'каждого опроса. Например, ACT. 296 начат в 20:33 при указанных 15 и закончился после '
              'опроса по Afelia (20:45-20:52); поэтому нельзя механически подставлять 14 по времени окончания. '
              'Сопоставление с действовавшей редакцией нормы и полномочиями Afelia остаётся необходимым.')
    paragraph(d, 'Интервалы и результаты взяты из опубликованных итогов с точностью до минуты; '
              'часовой пояс итогов нужно подтвердить по исходным сообщениям. Некоторые опросы пересекались.')
    paragraph(d, 'Для принятия конституционного закона сохранённая редакция Конституции требует '
              'две трети действующих сенаторов: 10 голосов при составе 15 или 11 при составе 16. '
              'По итогам ACT. 288 получил 10 голосов «за»; необходимо проверить применимую редакцию '
              'нормы, состав перед опросом и правомерность его уменьшения.')
    table(d, ['Время', 'Вопрос', 'Состав', 'За / против / возд.', 'По итогам'], VOTES_13, VOTE_WIDTHS)
    paragraph(d, 'По вторичной выгрузке в опросе об открытии видны 13 записей «да»: '
              'izverus, xaqqk, voblovna, zarke_, sky_992, afeliami, jhonnyycc, .h1meno., '
              'mlorv, al.zaru, .gogal, pavelrestl, dl344; воздержалась запись insideofdead. '
              'Это данные одного опроса, а не поимённая регистрация явки; принадлежность аккаунтов '
              'и право каждого голоса подлежат проверке.')
    paragraph(d, 'По инициативе о Jonny и партии опубликованные итоги связывают 10 / 2 / 3 с обеими мерами; '
              'в выгрузке тема названа по личной мере, а текст вопроса передан только как «Инициатива». '
              'Точный охват и законность каждой меры требуется установить по оригиналу и оформленным решениям.')
    heading(d, '4. Нерассмотренные инициативы')
    paragraph(d, 'Инициатива Merkylka Fair о ЦИК не рассматривалась. По пояснению Спикера, '
              'Merkylka не явилась, поэтому представить её инициативу было некому. '
              'При этом в опубликованных итогах нерассмотрение обеих инициатив связывается '
              'с отстранением партии. Эти сведения приведены вместе для проверки судом.')
    paragraph(d, 'Инициатива о рассмотрении вопроса о специальном прокуроре также не рассматривалась. '
              'В сохранённом тексте инициатором названа Merkylka Fair; Jonny Zakonov разместил ссылку '
              '11.11 в 09:23, заявление о его замене датировано 10:30, а Merkylka подтвердила '
              'представление в 23:55. Сопоставление времени предполагает одинаковый часовой пояс '
              'исходных сообщений. Само размещение ссылки не доказывает, что Jonny выступал '
              'самостоятельным инициатором после завершённой замены.')
    heading(d, '5. Источники')
    link(d, 'Опубликованные итоги заседания 13.11', RESULT_13)
    link(d, 'Подготовленный журнал 13.11 - без заполненных отметок явки', JOURNAL_13)
    link(d, 'Архивная копия реестра, размещённая 12.11', REG_OLD)
    link(d, 'Заявления о замене представителей с датами', HISTORY)
    link(d, 'Вторичная выгрузка электронных голосований', ARCHIVE)
    link(d, 'Тема голосования об открытии', TOPIC_13)
    link(d, 'Инициатива Merkylka о ЦИК', 'https://docs.google.com/document/d/1YULp4KtWRA2fbbngZjd2vx6K20C5efhrr8Bbj9ICcOw/edit?tab=t.0')
    link(d, 'Инициатива Merkylka о специальном прокуроре', 'https://docs.google.com/document/d/1w1DoJKVzdqG6RI8ZwLgpDtIsF3fbsp4Mo0LXBs5BS3M/edit?tab=t.0')
    link(d, 'Переписка об инициативе и голосованиях 13.11', git_source('Повестка/13.11.2026/06 Исходные данные/Результаты.txt'))
    final_signature(d)
    return d


def build_19():
    d = setup('19 ноября 2026 года')
    heading(d, '1. Источники и порядок восстановления')
    paragraph(d, 'Документ составлен после заседания по опубликованным итогам, сохранённым '
              'сообщениям об опросах, подготовленному журналу и поздней копии реестра. '
              'Поимённая регистрация явки и историческая версия реестра на каждое голосование '
              'не представлены. По итогам председательствовал Спикер Marcus Nomad, номер паспорта 85028.')
    heading(d, '2. Состав и явка')
    paragraph(d, 'Итоги и подготовленный лист журнала указывают 16 действующих сенаторов для подсчёта. '
              'Поимённо явившиеся и отсутствовавшие в них не установлены; 13 голосов за открытие '
              'не доказывают поимённую явку. Ниже - 16 имён из более позднего сохранённого реестра. '
              'Он помогает ориентироваться, но не подтверждает автоматически состав или явку на 19.11.')
    roster_table(d, ROSTER_19, '19')
    paragraph(d, '* Eric Killa в позднем реестре указан с номером 64370, в старом - 104068. '
              'Номер 43317 в позднем реестре указан за Nine Killua, а в заявлении 19.11 - за Valentin Litvin. '
              'Тождество лиц и момент отражения записей необходимо проверить; они здесь не предполагаются.')
    paragraph(d, 'В истории заявлений указаны: 15.11 в 23:32 Umka Nomad → Sanya Nomad; '
              '18.11 в 15:35 Pravik Killaz и в 16:19 Qwikus Killa заявлены как новые представители; '
              '19.11 в 15:33 Kiray Fair → Nansy Casta, в 17:32 - Valentin Litvin на свободное место '
              'и в 17:44 Meow Killa → Styort Killa. В 19:05 заявлена замена Kennych Killa → Jacob Killa; '
              'в 20:39 Jhonny Scoutezaki → Aurel Mavrody (по отметке после опубликованного '
              'интервала закрытия 19:44-19:48). Время и правомерность исполнения каждой заявки '
              'не подтверждены одним фактом её подачи.')
    paragraph(d, 'В опубликованных итогах указано, что в опросе по ACT. 309 Jacob Killa голосовал '
              'против. Это сведения об участии в конкретном опросе, а не полноценная регистрация '
              'присутствия всех сенаторов на заседании.')
    common_source_note(d)
    heading(d, '3. Голосования')
    paragraph(d, 'Интервалы и итоги в таблице воспроизведены из опубликованных результатов '
              'с точностью до минуты; часовой пояс следует проверить по оригиналам. Состав 16 указан '
              'по итогам для подсчёта, а не как число присутствовавших. Опросы частично совпадали по времени.')
    table(d, ['Время', 'Вопрос', 'Состав', 'За / против / возд.', 'По итогам'], VOTES_19, VOTE_WIDTHS)
    paragraph(d, 'Во вторичной выгрузке по открытию видны 13 учётных записей «за»: '
              'pravikkk, hau337, socrat_1hp, ossaula, voblovna, zarke_, sky_992, .h1meno., '
              'hs223, al.zaru, cyberbadlink, pipupipuq, pavelrestl. Их принадлежность лицам '
              'и право голоса требуют проверки; список не заменяет регистрацию явки и не позволяет '
              'считать не упомянутых в этом опросе отсутствовавшими.')
    paragraph(d, 'ACT. 302, 304 и 305 по итогам отозваны в 19:39, ACT. 306 и 307 - в 19:40; '
              'отдельные голосования по ним в представленном логе не зафиксированы. '
              'Результат по ACT. 299 и 300 относится к одному общему опросу.')
    paragraph(d, 'В материалах ACT. 308 название изменяемого акта требует сверки. По инициативе '
              'о замене члена ЦИК указана кандидатура Arkasha Justice вместо Angel Insomnia; '
              'отдельное оформление решения не подтверждено. Принятие законопроекта Сенатом '
              'не подтверждает судебного одобрения, подписания или вступления в силу.')
    heading(d, '4. Источники')
    link(d, 'Опубликованные итоги заседания 19.11', RESULT_19)
    link(d, 'Подготовленный лист журнала 19.11', JOURNAL_19)
    link(d, 'Более поздняя копия единого реестра', REG_LATER)
    link(d, 'История заявлений о заменах', HISTORY)
    link(d, 'Сохранённые сообщения и результаты опросов 19.11', git_source('Повестка/19.11.2026/19.11.26.txt'))
    link(d, 'Вторичная выгрузка электронных голосований', ARCHIVE)
    link(d, 'Тема голосования об открытии', TOPIC_19)
    final_signature(d)
    return d


def main(argv=None):
    parser = ArgumentParser(description='Подготовить восстановленные протоколы к делу № 105')
    parser.add_argument('--output-dir', type=Path, default=OUT, help='папка для новых DOCX')
    parser.add_argument('--force', action='store_true',
                        help='перезаписать существующие файлы; ручные правки и подписи будут потеряны')
    args = parser.parse_args(argv)
    targets = [(args.output_dir / f'Протокол {date} - восстановленные сведения.docx', build)
               for date, build in [('09.11.2026', build_09), ('13.11.2026', build_13), ('19.11.2026', build_19)]]
    existing = [path for path, _ in targets if path.exists()]
    if existing and not args.force:
        parser.error('Файлы уже существуют. Чтобы не потерять ручные правки и подписи, '
                     'укажите другую --output-dir или явно задайте --force.')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for out, build in targets:
        build().save(out)
        print(out)


if __name__ == '__main__':
    main()
