# -*- coding: utf-8 -*-
"""Итоги и протокол заседания 13.11.2026: один набор данных для PNG и BB-кода.

Данные опросов проверяются по неизменённому логу до записи результатов.
Предметы ACT. 288, 296 и 298 сверены с оригиналами по ссылкам из лога.
Принятие ACT. 296 и 298, а также причины нерассмотрения двух инициатив
подтверждены пользователем. При пересборке PNG требуются настоящие Times New
Roman Regular, Bold и Italic: SENATE_FONT_DIR=/путь python3 ...; файлы шрифтов
в репозиторий не включаются.
"""
from dataclasses import dataclass
from pathlib import Path
import os
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SESSION = ROOT / "Повестка" / "13.11.2026"
SOURCE = SESSION / "06 Исходные данные" / "Результаты.txt"
RESULT_DIR = SESSION / "03 Итоги"
PROTOCOL_DIR = SESSION / "04 Протокол"
RESULT_PNG = RESULT_DIR / "Итоги пленарного заседания Сената 13.11.2026.png"
RESULT_BB = RESULT_DIR / "Итоги пленарного заседания Сената 13.11.2026 - BB-код.txt"
PROTOCOL_PNG = PROTOCOL_DIR / "Протокол заседания Сената 13.11.2026.png"
PROTOCOL_BB = PROTOCOL_DIR / "Протокол заседания Сената 13.11.2026 - BB-код.txt"
ASSETS = ROOT / "Обращения" / "IAD — отзыв вето (Губернатор Harlow)" / "assets"
LOGO_URL = "https://i.ibb.co/zVnGyqQv/1.png"


@dataclass(frozen=True)
class Poll:
    key: str
    anchor: str
    raw_poll: str
    start: str
    end: str
    yes: int
    no: int
    abstain: int
    active: int                  # непосредственно перед началом данного опроса
    threshold: str               # прочерк, если применимый порог не установлен
    outcome: str
    kind: str                    # служебное, инициатива, закон, конституционный
    title: str                   # допустимо только локальное выделение [B]...[/B]
    meta: str
    url: str = ""
    detail: str = ""            # важные сведения для читателя рядом с вопросом

    @property
    def total(self):
        return self.yes + self.no + self.abstain

    @property
    def interval(self):
        return f"{self.start}-{self.end}"


SPEAKER = "Спикер Сената Marcus Nomad, номер паспорта 85028"
GOVERNOR = "Губернатор Tommy Harlow, номер паспорта 98650"
DEPUTY_PROSECUTOR = "Заместитель Генерального прокурора Gogal Killaz, номер паспорта 63823"

# Порядок - по времени начала голосования, а не по номеру документа или
# завершению. Опросы ACT. 295 и 296 пересекаются с избранием Вице-Спикера.
POLLS = (
    Poll("open", "Открытие Сената 13.11.26", "Открытие саната", "19:00", "19:05",
         13, 0, 1, 16, "-", "Открыто", "служебное",
         "[B]Открытие заседания Сената[/B]", SPEAKER,
         detail="Всего 14 голосов: да - 93%, нет - 0%, воздержался - 7%."),
    Poll("jonny", "ИНИЦИАТИВА о пожизненном лишении Jonny Zakonov права занимать должность сенатора",
         "Инициатива", "19:08", "19:10", 10, 2, 3, 16, "-", "Поддержана", "инициатива",
         "[B]Инициатива[/B] о пожизненном лишении Jonny Zakonov права занимать должность сенатора "
         "и отстранении Республиканской партии «Возрождение» от участия в заседаниях Сената",
         GOVERNOR + "; Jonny Zakonov, номер паспорта 55454",
         "https://docs.google.com/document/d/14tCBbXXkNNBvN9fhXjPkocVxydkBPoRSkSQNqsfW3Ss/edit?usp=sharing"),
    Poll("cec_governor", "ИНИЦИАТИВА об избрании Председателя и членов Центральной избирательной комиссии штата Сан-Андреас",
         "Инициатива", "19:13", "19:14", 10, 2, 3, 15, "-", "Поддержана", "инициатива",
         "[B]Инициатива[/B] об избрании председателя и членов Центральной избирательной комиссии штата Сан-Андреас",
         GOVERNOR,
         "https://docs.google.com/document/d/1tQtVhvKSPt0V62J1pd_SCs_EozbsWh5uhNc6HJdtRsQ/edit?usp=sharing",
         "Предложены: Qwikus Killa, номер паспорта 11736, - председатель; "
         "Pravik Killaz, номер паспорта 91999 (фамилия также указана как Killa), "
         "и Angel Insomnia - члены комиссии; номер паспорта Angel Insomnia не установлен."),
    Poll("286", "АСТ 286", "286", "19:21", "19:23", 5, 9, 1, 15, "8", "Не принят", "закон",
         "[B]ACT. 286[/B] - изменения законодательства об Экстренной медицинской службе",
         "Сенатор Kiray Fair, номер паспорта 37492",
         "https://docs.google.com/document/d/1ZRNpNoA-WGSzs1XSKASZjbp2prjZAUjU1HjNgDwy0i8/edit?usp=sharing"),
    Poll("287", "ACT. 287", "287", "19:25", "19:27", 10, 0, 2, 15, "8", "Принят", "закон",
         "[B]ACT. 287[/B] - изменения законодательства об адвокатуре", GOVERNOR,
         "https://docs.google.com/document/d/1dXWPbDmI9fJsHuwKzcJvS31evK4FG1BNVKsP6ciNyu8/edit?usp=sharing"),
    Poll("288", "ACT. 288", "288", "19:29", "19:30", 10, 0, 1, 15, "10", "Принят", "конституционный",
         "[B]ACT. 288[/B] - принятие нового [B]Конституционного закона «О Сенате штата Сан-Андреас»[/B] "
         "взамен действующего", GOVERNOR,
         "https://docs.google.com/document/d/145W9syp1qu6w8-eueMf_8BJ9a4xubO0WZ0MKvX23xI0/edit?usp=sharing"),
    Poll("298", "ACT. 298", "298", "19:31", "19:34", 10, 0, 2, 15, "8", "Принят", "закон",
         "[B]ACT. 298[/B] - изменение срока выдачи розыска по оперативно-розыскным мероприятиям "
         "в [B]Законе «Об оперативно-розыскной деятельности штата Сан-Андреас»[/B]", GOVERNOR,
         "https://docs.google.com/document/d/1Kd6vFGwMso03ZaQL8uWo5msZoh8GM_au2vE5JwgDqR4/edit?tab=t.0"),
    Poll("289", "ACT. 289", "289", "19:34", "19:40", 9, 0, 3, 15, "8", "Принят", "закон",
         "[B]ACT. 289[/B] - адвокат и закрытые территории", SPEAKER,
         "https://docs.google.com/document/d/1SElyNlHoizePYw795sIpyQsQa1bq9izXdkzKIXmWQ3U/edit?usp=sharing"),
    Poll("290", "ACT. 290", "290", "19:41", "19:42", 10, 0, 0, 15, "10", "Принят", "конституционный",
         "[B]ACT. 290[/B] - единое наименование должности Спикера Сената", SPEAKER,
         "https://docs.google.com/document/d/1yoVbXuwnPCzUfKpgqSERxdmf9XhrNXOnz2bEPdbHpD0/edit?usp=sharing"),
    Poll("291", "ACT. 291", "291", "19:45", "19:48", 3, 0, 8, 15, "8", "Не принят", "закон",
         "[B]ACT. 291[/B] - прилегающая территория Форта Занкудо", SPEAKER,
         "https://docs.google.com/document/d/1G8DGOjEW7VDXD714TEhYo3EDQvaWkpxJtZM065bE1yI/edit?usp=sharing"),
    Poll("292", "ACT. 292", "292", "19:48", "19:50", 10, 0, 1, 15, "10", "Принят", "конституционный",
         "[B]ACT. 292[/B] - полномочия сенатора при приостановлении деятельности партии", SPEAKER,
         "https://docs.google.com/document/d/1HOLOB7m74DMWWPOuqQS9tZ4g5DQQiSiQ-at2Y1jGtrI/edit?usp=sharing"),
    Poll("293", "ACT. 293", "293", "19:50", "19:53", 9, 0, 2, 15, "8", "Принят", "закон",
         "[B]ACT. 293[/B] - контроль деятельности политических партий", SPEAKER,
         "https://docs.google.com/document/d/13gqMydlY85PShbWdHNEbbiEwcOSiXVAUKI1MiPbOQts/edit?usp=sharing",
         "Воздержались Jhonny Scoutezaki, номер паспорта 164317, "
         "и Dmitriy Grayrat, номер паспорта 40117."),
    Poll("294", "ACT. 294", "294", "19:56", "20:22", 2, 1, 8, 15, "8", "Не принят", "закон",
         "[B]ACT. 294[/B] - вызов прокурора адвокатом при задержании", DEPUTY_PROSECUTOR,
         "https://docs.google.com/document/d/1PL1yzFsOUE9zDlZQ8VDSA8TBbMVtWrdlHSbJeTpEe_Q/edit?usp=sharing",
         "До голосования опубликованы исходная и исправленная редакции; какая из них "
         "вынесена на голосование, не установлено."),
    Poll("295", "ACT. 295", "295", "20:24", "20:54", 1, 0, 10, 15, "8", "Не принят", "закон",
         "[B]ACT. 295[/B] - круг лиц, подлежащих защите, и условия ответственности", DEPUTY_PROSECUTOR,
         "https://docs.google.com/document/d/1UeiQzWdCS7PU_6PwmpZv1g4boCbJ-kNwpgPKYwUsmjI/edit?usp=sharing"),
    Poll("296", "ACT 296", "296", "20:33", "20:54", 8, 0, 1, 15, "8", "Принят", "закон",
         "[B]ACT. 296[/B] - исправление отсылки в пункте «в» части 1 статьи 20 "
         "[B]Процессуального кодекса штата Сан-Андреас[/B] на часть 1 статьи 16", DEPUTY_PROSECUTOR,
         "https://docs.google.com/document/d/1VyKvlJMgr4pk3hhefDjlWGdvqgdDnR8xNLtfOfQxCSM/edit?usp=sharing"),
    Poll("297", "ACT 297", "297", "20:35", "20:42", 8, 0, 2, 15, "8", "Принят", "закон",
         "[B]ACT. 297[/B] - изменения дорожного законодательства", DEPUTY_PROSECUTOR,
         "https://docs.google.com/document/d/1Byp9S1pQjKglD8Z4WztkTxXsEX3FICMlUio-Sd5qUbk/edit?usp=sharing"),
    Poll("vice", "Инициатива об избрании Afelia Suspect 14077 на должность Вице-Спикера (зам председателя) Сената",
         "Иницивтива", "20:45", "20:52", 8, 0, 0, 15, "8", "Избрана", "инициатива",
         "[B]Инициатива[/B] об избрании Afelia Suspect Вице-Спикером Сената",
         GOVERNOR + "; Afelia Suspect, номер паспорта 14077"),
    Poll("close", "Закрытие заседания 13.11.26", "Закрытие", "20:53", "20:54",
         9, 0, 0, 14, "-", "Закрыто", "служебное",
         "[B]Закрытие заседания Сената[/B]", SPEAKER,
         detail="Всего 9 голосов: за - 100%, против - 0%, воздержался - 0%."),
)

BY_KEY = {poll.key: poll for poll in POLLS}
SUBSTANTIVE = tuple(p for p in POLLS if p.kind != "служебное")
# В итогах показаны и открытие, и закрытие в порядке начала голосований.
RESULT_POLLS = (BY_KEY["open"],) + SUBSTANTIVE + (BY_KEY["close"],)
UNVOTED_CEC_URL = "https://docs.google.com/document/d/1YULp4KtWRA2fbbngZjd2vx6K20C5efhrr8Bbj9ICcOw/edit?tab=t.0"
SPECIAL_PROSECUTOR_URL = "https://docs.google.com/document/d/1w1DoJKVzdqG6RI8ZwLgpDtIsF3fbsp4Mo0LXBs5BS3M/edit?tab=t.0"
REVISED_294_URL = "https://docs.google.com/document/d/1es8SpMm30VyHhDh2d7-O3DfKDjAxkcJRdYFojrvp4OE/edit?usp=sharing"

# Эти два заголовка разделяют темы в источнике, даже если опроса в них нет.
UNVOTED_ANCHORS = (
    "Инициатива о рассмотрении вопроса о назначении специального прокурора",
    "Инициатива об избрании Председателя и членов Центральной избирательной комиссии штата Сан-Андреас",
)

# У этих вопросов нет времени голосования: они перечисляются отдельно, не
# включаются в хронологию опросов и не получают вымышленных голосов.
UNCONSIDERED = (
    ("[B]Инициатива[/B] сенатора Merkylka Fair, номер паспорта 62277, "
     "об избрании председателя и членов Центральной избирательной комиссии штата Сан-Андреас",
     UNVOTED_CEC_URL),
    ("[B]Инициатива[/B] сенатора Merkylka Fair, номер паспорта 62277, о рассмотрении "
     "вопроса о назначении специального прокурора; опубликована Jonny Zakonov, "
     "номер паспорта 55454", SPECIAL_PROSECUTOR_URL),
)
UNCONSIDERED_REASON = (
    "Обе инициативы не рассматривались и на голосование не выносились в связи с "
    "отстранением Республиканской партии «Возрождение» после голосования по "
    "инициативе о Jonny Zakonov. Инициатива об избрании ЦИК, внесённая Губернатором, "
    "рассмотрена отдельно и указана в таблице."
)

RESULT_INTRO = (
    "Пленарное заседание Сената штата Сан-Андреас состоялось 13 ноября 2026 года "
    "под председательством Спикера Сената Marcus Nomad, номер паспорта 85028.",
    "До голосования по инициативе о Jonny Zakonov для подсчёта учитывались 16 сенаторов; "
    "после него - 15. После избрания Afelia Suspect Вице-Спикером - 14.",
    "Голосования приведены в порядке начала; указано время начала и окончания. "
    "Неучастие не приравнивается к воздержанию.",
)

PROTOCOL_INTRO = (
    "Дата и место проведения - 13 ноября 2026 года, зал заседаний Сената штата Сан-Андреас, "
    "Капитолий, г. Лос-Сантос. Председательствующий - Спикер Сената Marcus Nomad, "
    "номер паспорта 85028.",
    "Протокол составлен по записям электронных опросов и сведениям о ходе заседания. "
    "Время начала и окончания голосований приведено по журналу с точностью до минуты. "
    "Вопросы расположены по времени начала; "
    "часть голосований проводилась одновременно.",
    "В опросе об открытии зафиксировано 14 голосов. Для кворума при 16 действующих "
    "сенаторах необходимо присутствие не менее 8. При принадлежности поданных голосов "
    "действующим сенаторам кворум обеспечен; поимённая явка в логе не приведена.",
    "До завершения инициативы о Jonny Zakonov для подсчёта учитывались 16 сенаторов, "
    "после неё - 15. В 20:52 избрана Afelia Suspect, номер паспорта 14077: при избрании "
    "её полномочия сенатора прекращаются, после чего учитываются 14 сенаторов "
    "(часть 4 статьи 4 [B]Конституционного закона «О Сенате штата Сан-Андреас»[/B]). "
    "Порядок фиксации состава - часть 5 статьи 80 [B]Конституции штата Сан-Андреас[/B].",
)

# Публикуются только общие итоги и существенное для граждан различие между
# принятием законопроекта и вступлением закона в силу. Сведения о кандидатах,
# поимённых голосах и документах размещены рядом с соответствующими вопросами.
ENACTMENT_NOTE = (
    "Принятие законопроекта Сенатом не означает его судебного одобрения, подписания, "
    "обнародования или вступления в силу."
)
RESULT_NOTES = (
    "По итогам голосований приняты 9 законопроектов, не приняты - 4.",
    ENACTMENT_NOTE,
)
PROTOCOL_NOTES = (ENACTMENT_NOTE,)


def validate_polls_against_log(path=SOURCE):
    """Сверить время и все три числа с соответствующими темами Discord-лога."""
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    anchors = set(UNVOTED_ANCHORS) | {poll.anchor for poll in POLLS}
    locations = {}
    for pos, line in enumerate(lines):
        if line in anchors and line not in locations:
            locations[line] = pos
    missing = anchors - locations.keys()
    if missing:
        raise ValueError(f"В логе не найдены заголовки: {sorted(missing)}")
    sorted_positions = sorted(locations.values())
    for poll in POLLS:
        begin = locations[poll.anchor]
        end_section = next((i for i in sorted_positions if i > begin), len(lines))
        section = lines[begin:end_section]
        starts = []
        for i, line in enumerate(section):
            if line != poll.raw_poll:
                continue
            recent = section[max(0, i - 6):i]
            if any(re.search(rf"—\s*{re.escape(poll.start)}\s*$", v) for v in recent):
                starts.append(i)
        if len(starts) != 1:
            raise ValueError(f"{poll.key}: не найден однозначный опрос начала {poll.start}")
        start = starts[0]
        try:
            finish = section.index("Опрос завершён", start)
        except ValueError as exc:
            raise ValueError(f"{poll.key}: нет завершённого опроса") from exc
        block = section[start + 1:finish]
        labels = (("За", "Да"), ("Против", "Нет", "Протиив"), ("Воздержался",))
        positions = []
        for candidates in labels:
            matches = [i for i, line in enumerate(block) if line in candidates]
            if len(matches) != 1:
                raise ValueError(f"{poll.key}: отсутствует или повторяется вариант {candidates}")
            positions.append(matches[0])
        if positions != sorted(positions):
            raise ValueError(f"{poll.key}: варианты опроса расположены не по порядку")
        counts = []
        for i, pos in enumerate(positions):
            right = positions[i + 1] if i + 1 < len(positions) else len(block)
            nums = [int(m.group(1)) for line in block[pos + 1:right]
                    if (m := re.match(r"^(\d+)\s+голос(?:ов|а)?$", line))]
            if not nums:
                raise ValueError(f"{poll.key}: отсутствует число голосов после {block[pos]}")
            counts.append(nums[0])
            if i == 2 and (len(nums) < 2 or nums[-1] != poll.total):
                raise ValueError(f"{poll.key}: общее число голосов не совпадает: {nums}")
        if tuple(counts) != (poll.yes, poll.no, poll.abstain):
            raise ValueError(f"{poll.key}: расхождение голосов: {counts}")
        ended = [line for line in section[finish + 1:] if line.startswith("Опрос пользователя")]
        expected_end = f"«{poll.raw_poll}» завершён. — {poll.end}"
        if not ended or expected_end not in ended[0]:
            raise ValueError(f"{poll.key}: время завершения не подтверждено")
        if poll.total > poll.active:
            raise ValueError(f"{poll.key}: число голосов превышает учтённый состав")
    if [p.start for p in POLLS] != sorted(p.start for p in POLLS):
        raise ValueError("Вопросы не отсортированы по времени начала")
    required_293 = "wn / jhonny scoutezaki / 164317 и wn / dmitriy grayrat / 40117"
    if required_293 not in text:
        raise ValueError("Персональные голоса по ACT. 293 не подтверждены логом")
    return True


# Размеры BB-кода: основной текст и важные сведения 5, источник вопроса 3, заголовки 6.
BB_BODY_SIZE = 5
BB_META_SIZE = 3
BB_HEADING_SIZE = 6
BB_REJECTED_COLOR = "rgb(210, 55, 55)"


def bb_text(value):
    return f"[SIZE={BB_BODY_SIZE}]{value}[/SIZE]"


def bb_header(title):
    return (f'[CENTER]\n[IMG width="320px"]{LOGO_URL}[/IMG]\n\n'
            f'[I][B][COLOR=rgb(97, 189, 109)][SIZE={BB_HEADING_SIZE}]STATE of SAN ANDREAS[/SIZE][/COLOR][/B][/I]\n'
            f'[B][I][COLOR=rgb(97, 189, 109)][SIZE={BB_HEADING_SIZE}]OFFICE of THE SPEAKER of THE SENATE[/SIZE][/COLOR][/I][/B]\n\n'
            f'[I][B][SIZE={BB_HEADING_SIZE}]{title}[/SIZE][/B][/I]\n'
            f'[B][I][SIZE={BB_HEADING_SIZE}]13 ноября 2026 года[/SIZE][/I][/B]\n[/CENTER]\n\n')


def bb_heading(title):
    return f"[CENTER][B][I][SIZE={BB_HEADING_SIZE}]{title}[/SIZE][/I][/B][/CENTER]\n\n"


def bb_question(poll):
    # По ACT. 294 отдельно подписываем обе ссылки: неизвестно, какую редакцию голосовали.
    title = (f"[URL='{poll.url}']{poll.title}[/URL]"
             if poll.url and poll.key != "294" else poll.title)
    parts = [bb_text(title), f"[SIZE={BB_META_SIZE}]{poll.meta}[/SIZE]"]
    if poll.detail:
        parts.append(bb_text(poll.detail))
    if poll.key == "294":
        parts.append(bb_text(f"[URL='{poll.url}']Исходная редакция[/URL]; "
                             f"[URL='{REVISED_294_URL}']исправленная редакция[/URL]"))
    return "\n".join(parts)


def bb_cell(value, width=None, center=False, wrap_size=True):
    attr = f' width="{width}%"' if width else ""
    content = bb_text(value) if wrap_size else str(value)
    body = f"[CENTER]{content}[/CENTER]" if center else content
    return f"[td{attr}]{body}[/td]"


def bb_table(protocol=False):
    if protocol:
        headings = (("Время начала - окончания", 13), ("Вопрос", 35), ("Состав", 8),
                    ("За", 5), ("Против", 7), ("Воздержался", 9), ("Порог", 8), ("Итог", 15))
        entries = POLLS
    else:
        headings = (("Время начала - окончания", 14), ("Вопрос", 41), ("За", 7), ("Против", 8),
                    ("Воздержался", 12), ("Итог", 18))
        entries = RESULT_POLLS
    out = ['[TABLE width="100%"]', '[TR]']
    out.extend(bb_cell(f"[B][I]{t}[/I][/B]", width, True) for t, width in headings)
    out.append('[/TR]')
    for poll in entries:
        values = ([poll.interval, bb_question(poll), poll.active, poll.yes, poll.no,
                   poll.abstain, poll.threshold, poll.outcome] if protocol else
                  [poll.interval, bb_question(poll), poll.yes, poll.no, poll.abstain, poll.outcome])
        out.append('[TR]')
        for i, value in enumerate(values):
            if i == len(values) - 1:
                color = (BB_REJECTED_COLOR if poll.outcome == "Не принят" else
                         'rgb(171, 126, 43)' if '*' in poll.outcome else 'rgb(97, 189, 109)')
                value = f"[B][COLOR={color}]{value}[/COLOR][/B]"
            # В ячейке вопроса заголовок и сведения оформлены отдельно,
            # чтобы BB-код не вкладывал два тега SIZE друг в друга.
            out.append(bb_cell(value, center=(i != 1), wrap_size=(i != 1)))
        out.append('[/TR]')
    out.append('[/TABLE]\n')
    return "\n".join(out)


def bb_notes(notes):
    return "[LIST=1]\n" + "\n".join("[*]" + bb_text(note) for note in notes) + "\n[/LIST]\n\n"


def bb_signature():
    signature = ("[B]Спикер Сената штата Сан-Андреас\nMarcus Nomad[/B]\n"
                 "Номер паспорта 85028\n\n13 ноября 2026 года")
    return f"[RIGHT]\n{bb_text(signature)}\n[/RIGHT]\n"


def build_bb(protocol=False):
    title = "ПРОТОКОЛ ЗАСЕДАНИЯ СЕНАТА" if protocol else "ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ СЕНАТА"
    intro = PROTOCOL_INTRO if protocol else RESULT_INTRO
    notes = PROTOCOL_NOTES if protocol else RESULT_NOTES
    text = bb_header(title)
    text += "\n\n".join(bb_text(paragraph) for paragraph in intro) + "\n\n"
    text += bb_heading("Хронология голосований" if protocol else "Результаты голосований")
    text += bb_table(protocol) + "\n"
    if protocol:
        text += bb_text("[I]«Состав» - количество сенаторов, учитываемое перед началом голосования; "
                        "«Порог» - необходимое количество голосов за, где оно определено.[/I]") + "\n\n"
    text += bb_heading("Вопросы, которые не рассматривались")
    text += bb_text(UNCONSIDERED_REASON) + "\n\n[LIST=1]\n"
    text += "\n".join("[*]" + bb_text(f"[URL='{url}']{question}[/URL] - [B]не рассматривалась[/B]")
                      for question, url in UNCONSIDERED)
    text += "\n[/LIST]\n\n"
    text += bb_heading("Примечания") + bb_notes(notes)
    text += bb_signature()
    return text


# ---------------------------------------------------------------- PNG-вёрстка
# Единый набор текста и чисел с BB-кодом. Ссылки намеренно не передаются в рендер.
W = 3000
LEFT, RIGHT = 240, 2760
BODY_W = RIGHT - LEFT
CENTER = W // 2
GREEN = (69, 137, 63)
GREEN_D = (46, 92, 42)
INK = (26, 26, 26)
MUTED = (102, 107, 109)
RULE = (203, 208, 201)
SHADE = (236, 242, 232)
RED = (150, 46, 46)
AMBER = (145, 103, 32)


def font_faces():
    paths = (os.environ.get("SENATE_FONT_DIR"), "/usr/share/fonts/truetype/msttcorefonts",
             "/usr/share/fonts/truetype/microsoft", "/usr/local/share/fonts", "/mnt/c/Windows/Fonts")
    layouts = (("times.ttf", "timesbd.ttf", "timesi.ttf"),
               ("Times New Roman.ttf", "Times New Roman Bold.ttf", "Times New Roman Italic.ttf"))
    for root in filter(None, paths):
        for layout in layouts:
            files = tuple(Path(root) / name for name in layout)
            if all(p.is_file() for p in files):
                names = [ImageFont.truetype(str(p), 12).getname() for p in files]
                if all(family == "Times New Roman" and style.lower() == expected
                       for (family, style), expected in zip(names, ("regular", "bold", "italic"))):
                    return files
    raise SystemExit("Нужны Times New Roman Regular, Bold и Italic; укажите SENATE_FONT_DIR")


class DocumentPainter:
    def __init__(self, draw, image, faces, painting):
        self.draw = draw
        self.image = image
        self.faces = faces
        self.painting = painting
        self.cache = {}
        self.texts = []

    def font(self, style, size):
        key = (style, size)
        if key not in self.cache:
            self.cache[key] = ImageFont.truetype(str(self.faces[{"r": 0, "b": 1, "i": 2}[style]]), size)
        return self.cache[key]

    def width(self, text, style, size):
        return self.draw.textlength(text, font=self.font(style, size))

    def text(self, x, y, text, style="r", size=42, color=INK):
        if "http://" in text or "https://" in text or "Google Docs" in text:
            raise ValueError("В PNG запрещены прямые ссылки и название сервиса")
        if self.painting:
            self.texts.append(text)
            self.draw.text((round(x), round(y)), text, font=self.font(style, size), fill=color)

    def line(self, coords, fill=RULE, width=2):
        if self.painting:
            self.draw.line(coords, fill=fill, width=width)

    def rectangle(self, coords, fill=None, outline=None, width=1):
        if self.painting:
            self.draw.rectangle(coords, fill=fill, outline=outline, width=width)

    def centered(self, y, text, style, size, color=INK):
        self.text(CENTER - self.width(text, style, size) / 2, y, text, style, size, color)

    def tokens(self, text, size, initial_style="r"):
        if any(x in text for x in ("http://", "https://", "Google Docs")):
            raise ValueError("Ссылка попала в текст PNG")
        style = initial_style
        out = []
        for part in re.split(r"(\[B\]|\[/B\]|\[I\]|\[/I\])", text):
            if not part:
                continue
            if part == "[B]":
                style = "b"
            elif part == "[I]":
                style = "i"
            elif part in ("[/B]", "[/I]"):
                style = initial_style
            else:
                for token in re.findall(r"\S+|\s+", part):
                    value = " " if token.isspace() else token
                    out.append((value, style, size))
        return out

    def lines(self, text, width, size, initial_style="r"):
        lines, current, current_width = [], [], 0.0
        for word, style, fs in self.tokens(text, size, initial_style):
            if word == " " and not current:
                continue
            w = self.width(word, style, fs)
            if word != " " and w > width:
                raise ValueError(f"Слишком длинное слово для колонки: {word!r}")
            if word != " " and current and current_width + w > width:
                while current and current[-1][0] == " ":
                    removed = current.pop()
                    current_width -= self.width(*removed)
                lines.append((current, current_width))
                current, current_width = [], 0.0
            if word == " " and current and current[-1][0] == " ":
                continue
            current.append((word, style, fs))
            current_width += w
        while current and current[-1][0] == " ":
            removed = current.pop()
            current_width -= self.width(*removed)
        if current:
            lines.append((current, current_width))
        return lines or [([], 0)]

    def rich(self, x, y, text, width, size=42, color=INK, style="r", line_height=None):
        line_height = line_height or round(size * 1.45)
        lines = self.lines(text, width, size, style)
        for line, _ in lines:
            xx = x
            for token, typ, fs in line:
                if token != " ":
                    self.text(xx, y, token, typ, fs, color)
                xx += self.width(token, typ, fs)
            y += line_height
        return y

    def paragraph(self, y, text, size=42, color=INK, after=24, indent=0):
        return self.rich(LEFT + indent, y, text, BODY_W - indent, size, color) + after

    def heading(self, y, text):
        self.text(LEFT, y, text, "b", 43, GREEN_D)
        self.line([(LEFT, y + 65), (RIGHT, y + 65)], fill=RULE, width=3)
        return y + 88

    def header(self, title, subtitle):
        if self.painting:
            emblem = Image.open(ASSETS / "state_emblem.png").convert("RGB").resize((250, 250), Image.Resampling.LANCZOS)
            self.image.paste(emblem, (CENTER - 125, 150))
        self.centered(440, "STATE of SAN ANDREAS", "b", 68, GREEN)
        self.centered(535, "SENATE OF THE STATE OF SAN ANDREAS", "b", 30, GREEN)
        self.line([(850, 612), (2150, 612)], fill=GREEN, width=3)
        self.centered(655, title, "b", 62, INK)
        self.centered(745, subtitle, "r", 30, MUTED)
        self.text(LEFT, 830, "13 ноября 2026 года, г. Лос-Сантос", "i", 32, MUTED)
        right = "Спикер Сената Marcus Nomad, номер паспорта 85028"
        self.text(RIGHT - self.width(right, "i", 32), 830, right, "i", 32, MUTED)
        self.line([(LEFT, 880), (RIGHT, 880)], fill=RULE, width=2)
        return 945

    def table(self, y, polls, protocol=False):
        if protocol:
            widths = (210, 1000, 150, 120, 150, 160, 160, 570)
            heads = ("Время", "Вопрос", "Состав", "За", "Против", "Возд.", "Порог", "Итог")
        else:
            widths = (210, 1200, 130, 170, 180, 630)
            heads = ("Время", "Вопрос", "За", "Против", "Возд.", "Итог")
        assert sum(widths) == BODY_W
        head_h, padx, pad_y = 82, 17, 18
        self.rectangle((LEFT, y, RIGHT, y + head_h), fill=SHADE)
        self.line([(LEFT, y), (RIGHT, y)], fill=GREEN_D, width=4)
        x = LEFT
        for head, w in zip(heads, widths):
            fs = 35
            if self.width(head, "b", fs) > w - 2 * padx:
                fs = 31
            self.text(x + (w - self.width(head, "b", fs)) / 2, y + 21, head, "b", fs, GREEN_D)
            x += w
        y += head_h
        for poll in polls:
            label_lines = self.lines(poll.title, widths[1] - 2 * padx, 40)
            meta_lines = self.lines(poll.meta, widths[1] - 2 * padx, 30, "i")
            detail_lines = self.lines(poll.detail, widths[1] - 2 * padx, 36) if poll.detail else []
            row_h = (2 * pad_y + len(label_lines) * 54 + len(meta_lines) * 43 + 10
                     + (8 + len(detail_lines) * 50 if detail_lines else 0))
            self.line([(LEFT, y + row_h), (RIGHT, y + row_h)], width=2)
            text_x = LEFT + widths[0] + padx
            label_y = y + pad_y
            meta_y = label_y + len(label_lines) * 54 + 8
            self.rich(text_x, label_y, poll.title, widths[1] - 2 * padx, 40, INK, line_height=54)
            self.rich(text_x, meta_y, poll.meta, widths[1] - 2 * padx, 30, MUTED, "i", line_height=43)
            if detail_lines:
                self.rich(text_x, meta_y + len(meta_lines) * 43 + 8, poll.detail,
                          widths[1] - 2 * padx, 36, INK, line_height=50)
            values = ([poll.interval, "", str(poll.active), str(poll.yes), str(poll.no),
                       str(poll.abstain), poll.threshold, poll.outcome] if protocol else
                      [poll.interval, "", str(poll.yes), str(poll.no), str(poll.abstain), poll.outcome])
            x = LEFT
            for i, (value, w) in enumerate(zip(values, widths)):
                if i == 1:
                    x += w
                    continue
                fs = 34 if i == 0 else 39
                typ = "b" if i == len(values) - 1 else "r"
                color = (RED if poll.outcome == "Не принят" else AMBER if '*' in poll.outcome else GREEN_D) if typ == "b" else INK
                if self.width(value, typ, fs) > w - 2 * padx:
                    raise ValueError(f"Ячейка {poll.key}/{i} не вмещается: {value}")
                yy = y + (row_h - fs) / 2 - 8
                self.text(x + (w - self.width(value, typ, fs)) / 2, yy, value, typ, fs, color)
                x += w
            y += row_h
        return y + 35

    def signature(self, y):
        y += 75
        if self.painting:
            seal = Image.open(ASSETS / "great_seal.png").convert("RGBA").resize((310, 310), Image.Resampling.LANCZOS)
            self.image.paste(seal, (LEFT + 35, int(y)), seal)
        self.line([(1650, y + 118), (RIGHT - 30, y + 118)], fill=INK, width=4)
        self.text(1690, y + 143, "Marcus Nomad", "b", 45, INK)
        self.text(1690, y + 200, "Спикер Сената штата Сан-Андреас", "i", 32, MUTED)
        self.text(1690, y + 244, "Номер паспорта 85028", "i", 30, MUTED)
        self.text(1690, y + 286, "13 ноября 2026 года", "i", 30, MUTED)
        return y + 365

    def footer(self, y):
        self.line([(LEFT, y), (RIGHT, y)], fill=RULE, width=2)
        self.centered(y + 28, "STATE OF SAN ANDREAS  -  SENATE", "r", 26, MUTED)
        return y + 140


def draw_document(painter, protocol=False):
    title = "ПРОТОКОЛ ЗАСЕДАНИЯ СЕНАТА" if protocol else "ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ"
    subtitle = "ПЛЕНАРНОЕ ЗАСЕДАНИЕ СЕНАТА" if protocol else "ОФИЦИАЛЬНОЕ СООБЩЕНИЕ СПИКЕРА СЕНАТА"
    y = painter.header(title, subtitle)
    for para in PROTOCOL_INTRO if protocol else RESULT_INTRO:
        y = painter.paragraph(y, para, size=42, after=24)
    y += 20
    y = painter.heading(y, "I.  ХРОНОЛОГИЯ ГОЛОСОВАНИЙ" if protocol else "I.  РЕЗУЛЬТАТЫ ГОЛОСОВАНИЙ")
    y = painter.table(y, POLLS if protocol else RESULT_POLLS, protocol)
    if protocol:
        y = painter.paragraph(y, "Состав - число сенаторов перед началом голосования; "
                              "порог - необходимое число голосов за, где оно определено.",
                              size=35, color=MUTED, after=26)
    y = painter.heading(y + 20, "II.  ВОПРОСЫ, КОТОРЫЕ НЕ РАССМАТРИВАЛИСЬ")
    y = painter.paragraph(y, UNCONSIDERED_REASON, size=40, after=24)
    for n, (question, _) in enumerate(UNCONSIDERED, 1):
        y = painter.paragraph(y, f"[B]{n}.[/B] {question} - [B]не рассматривалась[/B].",
                              size=40, after=20)
    y = painter.heading(y + 20, "III.  ПРИМЕЧАНИЯ")
    notes = PROTOCOL_NOTES if protocol else RESULT_NOTES
    for n, text in enumerate(notes, 1):
        y = painter.paragraph(y, f"[B]{n}.[/B] {text}", size=38, after=21)
    y = painter.signature(y)
    return painter.footer(y + 65)


def render_png(path, protocol=False):
    faces = font_faces()
    scratch = Image.new("RGB", (1, 1), "white")
    measure = DocumentPainter(ImageDraw.Draw(scratch), scratch, faces, False)
    bottom = draw_document(measure, protocol)
    height = int(bottom + 130)
    image = Image.new("RGB", (W, height), "white")
    painter = DocumentPainter(ImageDraw.Draw(image), image, faces, True)
    actual = draw_document(painter, protocol)
    if actual != bottom or actual > height - 100:
        raise ValueError("Ошибка расчёта высоты документа")
    painter.rectangle((116, 92, W - 124, height - 95), outline=GREEN, width=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", dpi=(300, 300), optimize=True)
    return image.size


def main():
    validate_polls_against_log()
    result_bb, protocol_bb = build_bb(False), build_bb(True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_BB.write_text(result_bb, encoding="utf-8")
    PROTOCOL_BB.write_text(protocol_bb, encoding="utf-8")
    for path, protocol in ((RESULT_PNG, False), (PROTOCOL_PNG, True)):
        print("PNG", path.relative_to(ROOT), render_png(path, protocol))
    print("BB", RESULT_BB.relative_to(ROOT))
    print("BB", PROTOCOL_BB.relative_to(ROOT))


if __name__ == "__main__":
    main()
