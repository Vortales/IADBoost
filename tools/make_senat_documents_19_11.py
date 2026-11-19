# -*- coding: utf-8 -*-
"""Повестка и итоги 19.11.2026: одни подтверждённые данные для PNG и BB-кода.

Протокол не создаётся. Исходный лог и ранее выданный созыв не изменяются.
Перед записью сверяются результаты восьми опросов и пять сообщений об отзыве.
Точные редакции документов по внешним ссылкам в момент голосования не установлены.
"""
from dataclasses import dataclass
from pathlib import Path
import re

from PIL import Image, ImageDraw

import make_senat_documents_13_11 as previous

ROOT = Path(__file__).resolve().parent.parent
SESSION = ROOT / "Повестка" / "19.11.2026"
SOURCE = SESSION / "19.11.26.txt"
AGENDA_DIR = SESSION / "02 Повестка"
RESULT_DIR = SESSION / "03 Итоги"
AGENDA_NAME = "Повестка заседания 19.11.2026"
RESULT_NAME = "Итоги пленарного заседания Сената 19.11.2026"
ACTIVE_COUNT = 16  # указано пользователем; не означает установленную явку
MAJORITY = ACTIVE_COUNT // 2 + 1
SPEAKER = "Спикер Сената Marcus Nomad, номер паспорта 85028"
SANG = "Сенатор SANG Asher K., номер паспорта 68553"
PROSECUTOR = "Генеральный прокурор Pravik Killaz, номер паспорта 91999"
LOGO_URL = "https://i.ibb.co/zVnGyqQv/1.png"


@dataclass(frozen=True)
class Item:
    key: str
    label: str
    subject: str
    author: str
    posted: str
    url: str
    kind: str = "Законопроект"


ITEMS = (
    Item("299", "ACT. 299", "применение огнестрельного оружия при невыполнении требования покинуть Форт-Занкудо", SANG, "16.11.2026, 22:59", "https://docs.google.com/document/d/1I69yFqf36fxlCE2d_bE8XxZB4Yva7278WNAppp1yibY/edit?usp=sharing"),
    Item("300", "ACT. 300", "применение огнестрельного оружия военнослужащими Национальной гвардии", SANG, "16.11.2026, 23:30", "https://docs.google.com/document/d/1u52dXSkXD9J-VCKrx26DKq9uKeSkq9ntvUnqTqbf5kY/edit?usp=sharing"),
    Item("301", "ACT. 301", "освобождение и выход с охраняемого объекта", SPEAKER, "18:29", "https://docs.google.com/document/d/15FA-V6RkWpax6MN9N54XjoRI_X6RmakTuM3YXQFt4J8/edit?usp=sharing"),
    Item("302", "ACT. 302", "вызов начальства задержанного и его участие в задержании", SPEAKER, "18:29", "https://docs.google.com/document/d/1ptA_oj68MFgqWPtUN5Mo-dLK-5SihMk7uk7QEoQaHEA/edit?usp=sharing"),
    Item("303", "ACT. 303", "режим территорий и порядок доступа", SPEAKER, "18:29", "https://docs.google.com/document/d/1KLeUKKG9MDf_yOE3RdTGZlzREoU45ShbgvWJt3IIW6U/edit?usp=sharing"),
    Item("304", "ACT. 304", "вызов прокурора при споре об освобождении", SPEAKER, "18:30", "https://docs.google.com/document/d/1S4RQtVUeXYPM0vTTgsg1YVpg8IbECUOFClXAMVXYT8s/edit?usp=sharing"),
    Item("305", "ACT. 305", "изучение аудио- и видеоматериалов защиты", SPEAKER, "18:30", "https://docs.google.com/document/d/1i3vdfPPgPXEzvKkEmuWWTEwoA70K6KQEpXyJqAuXWuc/edit?usp=sharing"),
    Item("306", "ACT. 306", "рассмотрение устных ходатайств при задержании", SPEAKER, "18:30", "https://docs.google.com/document/d/1WHFutBJwNiv09rzlRQ14rpyIeH66PjG0sNLCWxzko6o/edit?usp=sharing"),
    Item("307", "ACT. 307", "сведения адвокату о фактических обстоятельствах", SPEAKER, "18:30", "https://docs.google.com/document/d/1ypdGE_wiUACXdDs2yZkMbfTOvqne2DzqjPXbkPFQ5QY/edit?usp=sharing"),
    Item("308", "ACT. 308", "нарушение порядка проведения собрания или митинга государственным служащим", PROSECUTOR, "18:37", "https://docs.google.com/document/d/15frJLeyQeQwYSjV56t7IC7LlCt-Y5ovcVW5DJi082dw/edit?usp=sharing"),
    Item("309", "ACT. 309", "повторное оскорбление представителя власти", PROSECUTOR, "19:11", "https://docs.google.com/document/d/15yAkl6dcM5wj9yuNqFf3aw9vhlyvoVfh4qLlH7g-CRk/edit?usp=sharing"),
    Item("cec", "Инициатива", "замена члена ЦИК: Arkasha Justice вместо Angel Insomnia", PROSECUTOR, "19:16", "https://docs.google.com/document/d/1JXsnweNUiC6PyIHO8vRt89pyWADjvnO-exRRMPV_Eyo/edit?usp=sharing", "Инициатива"),
)
ITEM = {item.key: item for item in ITEMS}
WITHDRAWN = (("302", "19:39"), ("304", "19:39"), ("305", "19:39"),
             ("306", "19:40"), ("307", "19:40"))
WITHDRAWAL_TIME = dict(WITHDRAWN)


@dataclass(frozen=True)
class Poll:
    key: str
    raw_label: str
    start: str
    end: str
    yes: int
    no: int
    abstain: int
    percentages: tuple[int, int, int]
    outcome: str
    kind: str
    title: str
    meta: str
    url: str = ""
    second_url: str = ""
    detail: str = ""

    @property
    def total(self):
        return self.yes + self.no + self.abstain

    @property
    def interval(self):
        return f"{self.start}-{self.end}"


POLLS = (
    Poll("open", "Открытие сената 19.11", "19:08", "19:11", 13, 0, 0, (100, 0, 0), "Открыто", "служебное", "[B]Открытие заседания[/B]", SPEAKER, detail="Всего 13 голосов: за - 100%, против - 0%, воздержался - 0%."),
    Poll("299-300", "299 - 300", "19:18", "19:19", 4, 8, 1, (31, 62, 8), "Не приняты", "законопроекты", "[B]ACT. 299 и ACT. 300[/B] - предложения SANG об охране Форта", SANG, ITEM["299"].url, ITEM["300"].url, "Оба проекта вынесены на один общий опрос."),
    Poll("301", "301", "19:28", "19:33", 4, 7, 1, (33, 58, 8), "Не принят", "законопроект", "[B]ACT. 301[/B] - освобождение и выход с охраняемого объекта", SPEAKER, ITEM["301"].url),
    Poll("303", "303", "19:34", "19:35", 1, 10, 0, (9, 91, 0), "Не принят", "законопроект", "[B]ACT. 303[/B] - режим территорий и порядок доступа", SPEAKER, ITEM["303"].url),
    Poll("308", "308", "19:36", "19:43", 10, 1, 3, (71, 7, 21), "Принят Сенатом", "законопроект", "[B]ACT. 308[/B] - нарушение порядка проведения митинга государственным служащим", PROSECUTOR, ITEM["308"].url, detail="В названии указан [B]Дорожный кодекс[/B], но таблица содержит уголовную норму; название акта требует проверки."),
    Poll("cec", "Инициатива", "19:38", "19:44", 9, 1, 0, (90, 10, 0), "Поддержана", "инициатива", "[B]Инициатива[/B] о замене члена Центральной избирательной комиссии", PROSECUTOR, ITEM["cec"].url, detail="Предложен Arkasha Justice вместо Angel Insomnia; оформление решения не подтверждено."),
    Poll("309", "309", "19:39", "19:43", 12, 1, 1, (86, 7, 7), "Принят Сенатом", "законопроект", "[B]ACT. 309[/B] - повторное оскорбление представителя власти", PROSECUTOR, ITEM["309"].url, detail="Против в записи опроса указан Jacob Killa, номер паспорта 57474."),
    Poll("close", "Закрытие", "19:44", "19:48", 10, 1, 1, (83, 8, 8), "Закрыто", "служебное", "[B]Закрытие заседания[/B]", SPEAKER, detail="Всего 12 голосов: за - 83%, против - 8%, воздержался - 8%."),
)
BY_POLL = {poll.key: poll for poll in POLLS}

INTRO = (
    "Пленарное заседание Сената штата Сан-Андреас состоялось 19 ноября 2026 года под председательством Спикера Сената Marcus Nomad, номер паспорта 85028.",
    "Для подсчёта учтены 16 действующих сенаторов. Поимённая явка в предоставленном логе не указана; для большинства от этого состава необходимо 9 голосов за.",
    "Голосования приведены по времени начала; часть опросов проводилась одновременно. Неучастие не приравнивается к воздержанию.",
)
AGENDA_INTRO = (
    "Перечень составлен по предоставленным сообщениям о заседании 19 ноября 2026 года. Утверждённая первоначальная повестка отдельно не предоставлена.",
    "В материалах указаны 11 законопроектов ACT. 299-309 и одна инициатива. По ACT. 299 и 300 проведён один совместный опрос; сведения об отзыве отражены по сообщениям Спикера.",
)
WITHDRAWN_NOTE = ("ACT. 302, 304 и 305 отозваны в 19:39; ACT. 306 и 307 - в 19:40. "
                  "Отдельные голосования по ним в предоставленном логе не зафиксированы.")
ENACTMENT_NOTE = ("Принятие законопроекта Сенатом не подтверждает его судебного одобрения, "
                  "подписания, обнародования или вступления в силу.")
SOURCE_NOTE = ("Указаны время начала и окончания опросов с точностью до минуты. "
               "Проценты в исходных сообщениях округлены; голосование об открытии не заменяет поимённую регистрацию явки.")
ACT308_NOTE = ("В ACT. 308 название указывает на [B]Дорожный кодекс[/B], а сравнительная таблица - "
               "на уголовную норму. Перед дальнейшим оформлением необходимо уточнить название изменяемого акта.")


def validate_source(path=SOURCE):
    """Проверяет каждый опрос по тексту, времени, итогам и варианту ответа."""
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()]
    text = "\n".join(lines)
    if "Сенат 19.11.26" not in lines or not all(item.url in text for item in ITEMS):
        raise ValueError("В логе не найдены дата заседания или ссылки на вопросы")
    if not all(name in text for name in ("Asher K.", "68553", "Pravik Killaz", "91999", "Marcus Nomad", "85028")):
        raise ValueError("В логе не найдены сведения об авторах сообщений")
    if len({p.key for p in POLLS}) != len(POLLS) or [p.start for p in POLLS] != sorted(p.start for p in POLLS):
        raise ValueError("Повтор или нарушение порядка опросов")
    for poll in POLLS:
        candidates = []
        for i, line in enumerate(lines):
            if line != poll.raw_label:
                continue
            recent = lines[max(0, i - 8):i]
            if (any(re.search(rf"—\s*{re.escape(poll.start)}\s*$", value) for value in recent)
                    and "За" in lines[i + 1:i + 5]):
                candidates.append(i)
        if len(candidates) != 1:
            raise ValueError(f"{poll.key}: не найден единственный опрос начала {poll.start}")
        start = candidates[0]
        try:
            finish = lines.index("Опрос завершён", start)
        except ValueError as exc:
            raise ValueError(f"{poll.key}: отсутствует окончание опроса") from exc
        block = lines[start + 1:finish]
        positions = []
        for label in ("За", "Против", "Воздержался"):
            matches = [i for i, value in enumerate(block) if value == label]
            if len(matches) != 1:
                raise ValueError(f"{poll.key}: некорректный вариант {label}")
            positions.append(matches[0])
        if positions != sorted(positions):
            raise ValueError(f"{poll.key}: нарушен порядок вариантов")
        counts, percentages = [], []
        for j, pos in enumerate(positions):
            right = positions[j + 1] if j + 1 < len(positions) else len(block)
            chunk = block[pos + 1:right]
            nums = [int(m.group(1)) for value in chunk
                    if (m := re.fullmatch(r"(\d+)\s+голос(?:ов|а)?", value))]
            pct = [int(m.group(1)) for value in chunk if (m := re.fullmatch(r"(\d+)%", value))]
            if not nums or len(pct) != 1:
                raise ValueError(f"{poll.key}: отсутствуют числа или проценты")
            counts.append(nums[0])
            percentages.append(pct[0])
            if j == 2 and (len(nums) < 2 or nums[-1] != poll.total):
                raise ValueError(f"{poll.key}: сумма голосов не подтверждена")
        if tuple(counts) != (poll.yes, poll.no, poll.abstain) or tuple(percentages) != poll.percentages:
            raise ValueError(f"{poll.key}: расхождение голосов или процентов")
        end_message = f"«{poll.raw_label}» завершён. — {poll.end}"
        if not any(end_message in line for line in lines[finish + 1:finish + 6]):
            raise ValueError(f"{poll.key}: окончание опроса не подтверждено")
        if poll.total > ACTIVE_COUNT or poll.start > poll.end:
            raise ValueError(f"{poll.key}: невозможно сопоставить голоса или времена")
    for key, time in WITHDRAWN:
        anchor = f"ACT.{key}"
        if lines.count(anchor) != 1:
            raise ValueError(f"{key}: неоднозначный заголовок")
        begin = lines.index(anchor)
        end = next((i for i in range(begin + 1, len(lines))
                    if re.fullmatch(r"(?:ACT\.|АСТ\s*)\s*30[2-9]", lines[i])), len(lines))
        section = lines[begin:end]
        hits = [i for i, line in enumerate(section) if line == "Отозван"]
        if len(hits) != 1 or not any(re.search(rf"—\s*{time}\s*$", s)
                                     for s in section[max(0, hits[0] - 5):hits[0]]):
            raise ValueError(f"{key}: отзыв или его время не подтверждены")
    against = text.split("\n309\nЗа\n", 1)[1].split("\nВоздержался\n", 1)[0]
    if "СЕНТА I JACOB KILLA 57474" not in against:
        raise ValueError("Поимённое указание по ACT. 309 не найдено")
    return True


def plain(value):
    return re.sub(r"\[/?[BI]\]", "", value)


def date_posted(item):
    # Для сообщений без отдельной даты не добавляем дату публикации из контекста.
    return item.posted


def agenda_markdown():
    text = ["# Повестка заседания Сената - 19 ноября 2026 года", "", *AGENDA_INTRO,
            "", "Заседание назначено на **19:00**, зал заседаний Сената, Капитолий штата Сан-Андреас, город Лос-Сантос.",
            "Сообщение подготовлено Спикером Сената Marcus Nomad, номер паспорта 85028.", "", "## Законопроекты"]
    for item in ITEMS:
        if item.kind == "Инициатива":
            continue
        status = f" Отозван в {WITHDRAWAL_TIME[item.key]}." if item.key in WITHDRAWAL_TIME else ""
        text += ["", f"- **{item.label}** - {item.subject}. {item.author}. Размещено: {date_posted(item)}.{status} [Документ]({item.url})."]
    item = ITEM["cec"]
    text += ["", "## Инициатива", "", f"- **{item.label}** - {item.subject}. {item.author}. Размещено: {date_posted(item)}. [Документ]({item.url}).",
             "", "## Уточнения", "", f"- {WITHDRAWN_NOTE}",
             "- По ACT. 299 и ACT. 300 проведено одно совместное голосование; раздельных результатов в логе нет.",
             f"- {plain(ACT308_NOTE)}", "- Для сообщений, где указано только время, дата размещения отдельно не установлена.",
             "- Содержание ссылок может изменяться; идентичность текущих документов редакциям во время голосования не подтверждена.", ""]
    return "\n".join(text)


def results_markdown():
    text = ["# Итоги пленарного заседания Сената - 19 ноября 2026 года", "", *INTRO,
            "", "## Результаты голосований", "", "| Время | Вопрос | За | Против | Воздержался | Итог |", "|---|---|---:|---:|---:|---|"]
    for p in POLLS:
        if p.second_url:
            title = f"[ACT. 299]({p.url}) и [ACT. 300]({p.second_url}) - предложения SANG об охране Форта"
        elif p.url:
            title = f"[{plain(p.title)}]({p.url})"
        else:
            title = plain(p.title)
        text.append(f"| {p.interval} | {title} | {p.yes} | {p.no} | {p.abstain} | {p.outcome} |")
    text += ["", "## Отозванные проекты", "", WITHDRAWN_NOTE, "", "## Примечания", "",
             f"- {plain(ACT308_NOTE)}", "- По инициативе предложен Arkasha Justice вместо Angel Insomnia; факт отдельного оформления решения не представлен.",
             "- По ACT. 309 голос против в записи указан за Jacob Killa, номер паспорта 57474.",
             f"- {SOURCE_NOTE}", f"- {ENACTMENT_NOTE}", ""]
    return "\n".join(text)


def bb_header(title):
    return (f'[FONT=Times New Roman]\n[CENTER]\n[IMG width="320px"]{LOGO_URL}[/IMG]\n\n'
            '[I][B][COLOR=rgb(97, 189, 109)][SIZE=6]STATE of SAN ANDREAS[/SIZE][/COLOR][/B][/I]\n'
            '[B][I][COLOR=rgb(97, 189, 109)][SIZE=6]OFFICE of THE SPEAKER of THE SENATE[/SIZE][/COLOR][/I][/B]\n\n'
            f'[I][B][SIZE=6]{title}[/SIZE][/B][/I]\n'
            '[B][I][SIZE=6]19 ноября 2026 года[/SIZE][/I][/B]\n[/CENTER]\n\n')


def bb_text(value, size=5):
    return f"[SIZE={size}]{value}[/SIZE]"


def bb_heading(value):
    return f"[CENTER][B][I][SIZE=6]{value}[/SIZE][/I][/B][/CENTER]\n\n"


def bb_signature():
    return ("[RIGHT]\n[SIZE=5][B]Спикер Сената штата Сан-Андреас\nMarcus Nomad[/B]\n"
            "Номер паспорта 85028\n\n19 ноября 2026 года[/SIZE]\n[/RIGHT]\n[/FONT]\n")


def agenda_bb():
    text = bb_header("ПОВЕСТКА ПЛЕНАРНОГО ЗАСЕДАНИЯ СЕНАТА")
    text += "\n\n".join(bb_text(p) for p in AGENDA_INTRO) + "\n\n"
    text += bb_text("Заседание назначено на 19 ноября 2026 года, 19:00, зал заседаний Сената, Капитолий штата Сан-Андреас, город Лос-Сантос.") + "\n\n"
    text += bb_heading("Вопросы повестки дня")
    headings = (("Документ", 14), ("Предмет", 38), ("Тип", 14), ("Автор сообщения", 20), ("Размещено", 14))
    rows = ['[TABLE width="100%"]', '[TR]']
    rows += [f'[td width="{width}%"][CENTER]{bb_text(f"[B][I]{name}[/I][/B]")}[/CENTER][/td]' for name, width in headings]
    rows.append('[/TR]')
    for item in ITEMS:
        status = f" [B]Отозван в {WITHDRAWAL_TIME[item.key]}.[/B]" if item.key in WITHDRAWAL_TIME else ""
        label = f"[URL='{item.url}'][B]{item.label}[/B][/URL]"
        values = (label, item.subject + "." + status, item.kind, item.author, date_posted(item))
        rows.append('[TR]')
        for i, value in enumerate(values):
            content = bb_text(value)
            rows.append(f'[td]{content if i == 1 else f"[CENTER]{content}[/CENTER]"}[/td]')
        rows.append('[/TR]')
    rows.append('[/TABLE]\n')
    text += "\n".join(rows) + "\n" + bb_heading("Примечания") + "[LIST=1]\n"
    text += "\n".join("[*]" + bb_text(note) for note in (WITHDRAWN_NOTE,
        "По ACT. 299 и ACT. 300 проведено одно совместное голосование; раздельных результатов в логе нет.",
        ACT308_NOTE, "Для сообщений без явной даты указано только время размещения."))
    return text + "\n[/LIST]\n\n" + bb_signature()


def bb_question(poll):
    if poll.key == "299-300":
        title = (f"[URL='{poll.url}'][B]ACT. 299[/B][/URL] и "
                 f"[URL='{poll.second_url}'][B]ACT. 300[/B][/URL] - предложения SANG об охране Форта")
    else:
        title = f"[URL='{poll.url}']{poll.title}[/URL]" if poll.url else poll.title
    result = [bb_text(title), bb_text(poll.meta, 3)]
    if poll.detail:
        result.append(bb_text(poll.detail))
    return "\n".join(result)


def result_bb():
    text = bb_header("ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ СЕНАТА")
    text += "\n\n".join(bb_text(p) for p in INTRO) + "\n\n" + bb_heading("Результаты голосований")
    headers = (("Время", 14), ("Вопрос", 41), ("За", 7), ("Против", 8), ("Воздержался", 12), ("Итог", 18))
    rows = ['[TABLE width="100%"]', '[TR]']
    rows += [f'[td width="{width}%"][CENTER]{bb_text(f"[B][I]{name}[/I][/B]")}[/CENTER][/td]' for name, width in headers]
    rows.append('[/TR]')
    for p in POLLS:
        color = "rgb(210, 55, 55)" if p.outcome in ("Не принят", "Не приняты") else "rgb(97, 189, 109)"
        values = (p.interval, bb_question(p), str(p.yes), str(p.no), str(p.abstain), f"[B][COLOR={color}]{p.outcome}[/COLOR][/B]")
        rows.append('[TR]')
        for i, value in enumerate(values):
            cell = value if i == 1 else bb_text(value)
            rows.append(f'[td]{cell if i == 1 else f"[CENTER]{cell}[/CENTER]"}[/td]')
        rows.append('[/TR]')
    rows.append('[/TABLE]\n')
    text += "\n".join(rows) + "\n" + bb_heading("Отозванные проекты") + bb_text(WITHDRAWN_NOTE) + "\n\n"
    text += bb_heading("Примечания") + "[LIST=1]\n"
    text += "\n".join("[*]" + bb_text(note) for note in (SOURCE_NOTE, ENACTMENT_NOTE))
    return text + "\n[/LIST]\n\n" + bb_signature()


class Painter(previous.DocumentPainter):
    """Оформление как в итогах 13.11, с датой и содержанием нового заседания."""
    def header(self, title, subtitle):
        if self.painting:
            emblem = Image.open(previous.ASSETS / "state_emblem.png").convert("RGB").resize((250, 250), Image.Resampling.LANCZOS)
            self.image.paste(emblem, (previous.CENTER - 125, 150))
        self.centered(440, "STATE of SAN ANDREAS", "b", 68, previous.GREEN)
        self.centered(535, "SENATE OF THE STATE OF SAN ANDREAS", "b", 30, previous.GREEN)
        self.line([(850, 612), (2150, 612)], fill=previous.GREEN, width=3)
        self.centered(655, title, "b", 62, previous.INK)
        self.centered(745, subtitle, "r", 30, previous.MUTED)
        self.text(previous.LEFT, 830, "19 ноября 2026 года, г. Лос-Сантос", "i", 32, previous.MUTED)
        right = SPEAKER
        self.text(previous.RIGHT - self.width(right, "i", 32), 830, right, "i", 32, previous.MUTED)
        self.line([(previous.LEFT, 880), (previous.RIGHT, 880)], fill=previous.RULE, width=2)
        return 945

    def signature(self, y):
        y += 75
        if self.painting:
            seal = Image.open(previous.ASSETS / "great_seal.png").convert("RGBA").resize((310, 310), Image.Resampling.LANCZOS)
            self.image.paste(seal, (previous.LEFT + 35, int(y)), seal)
        self.line([(1650, y + 118), (previous.RIGHT - 30, y + 118)], fill=previous.INK, width=4)
        self.text(1690, y + 143, "Marcus Nomad", "b", 45, previous.INK)
        self.text(1690, y + 200, "Спикер Сената штата Сан-Андреас", "i", 32, previous.MUTED)
        self.text(1690, y + 244, "Номер паспорта 85028", "i", 30, previous.MUTED)
        self.text(1690, y + 286, "19 ноября 2026 года", "i", 30, previous.MUTED)
        return y + 365

    def poll_table(self, y):
        widths = (240, 1170, 130, 170, 180, 630)
        heads = ("Время", "Вопрос", "За", "Против", "Возд.", "Итог")
        assert sum(widths) == previous.BODY_W
        head_h, padx, pady = 82, 17, 18
        self.rectangle((previous.LEFT, y, previous.RIGHT, y + head_h), fill=previous.SHADE)
        self.line([(previous.LEFT, y), (previous.RIGHT, y)], fill=previous.GREEN_D, width=4)
        x = previous.LEFT
        for head, width in zip(heads, widths):
            size = 35 if self.width(head, "b", 35) <= width - 2 * padx else 30
            self.text(x + (width - self.width(head, "b", size)) / 2, y + 21, head, "b", size, previous.GREEN_D)
            x += width
        y += head_h
        for poll in POLLS:
            title_lines = self.lines(poll.title, widths[1] - 2 * padx, 40)
            meta_lines = self.lines(poll.meta, widths[1] - 2 * padx, 30, "i")
            detail_lines = self.lines(poll.detail, widths[1] - 2 * padx, 36) if poll.detail else []
            height = (2 * pady + len(title_lines) * 54 + len(meta_lines) * 43 + 10
                      + (8 + len(detail_lines) * 50 if detail_lines else 0))
            self.line([(previous.LEFT, y + height), (previous.RIGHT, y + height)], width=2)
            text_x = previous.LEFT + widths[0] + padx
            title_y = y + pady
            meta_y = title_y + len(title_lines) * 54 + 8
            self.rich(text_x, title_y, poll.title, widths[1] - 2 * padx, 40, previous.INK, line_height=54)
            self.rich(text_x, meta_y, poll.meta, widths[1] - 2 * padx, 30, previous.MUTED, "i", line_height=43)
            if detail_lines:
                self.rich(text_x, meta_y + len(meta_lines) * 43 + 8, poll.detail,
                          widths[1] - 2 * padx, 36, previous.INK, line_height=50)
            values = (poll.interval, "", str(poll.yes), str(poll.no), str(poll.abstain), poll.outcome)
            x = previous.LEFT
            for i, (value, width) in enumerate(zip(values, widths)):
                if i == 1:
                    x += width
                    continue
                size = 34 if i == 0 else 39
                style = "b" if i == len(values) - 1 else "r"
                color = (previous.RED if poll.outcome in ("Не принят", "Не приняты") else previous.GREEN_D) if style == "b" else previous.INK
                if self.width(value, style, size) > width - 2 * padx:
                    raise ValueError(f"Ячейка {poll.key}/{i} не вмещается: {value}")
                self.text(x + (width - self.width(value, style, size)) / 2,
                          y + (height - size) / 2 - 8, value, style, size, color)
                x += width
            y += height
        return y + 35


def draw_agenda(p):
    y = p.header("ПОВЕСТКА ПЛЕНАРНОГО ЗАСЕДАНИЯ", "ПЕРЕЧЕНЬ ПО ПРЕДОСТАВЛЕННЫМ МАТЕРИАЛАМ")
    for value in AGENDA_INTRO:
        y = p.paragraph(y, value, size=42, after=24)
    y = p.paragraph(y, "Время и место: 19 ноября 2026 года, 19:00, зал заседаний Сената, Капитолий, город Лос-Сантос.", size=40, after=30)
    y = p.heading(y + 10, "I.  ЗАКОНОПРОЕКТЫ")
    for i, item in enumerate((x for x in ITEMS if x.kind == "Законопроект"), 1):
        status = f" [B]Отозван в {WITHDRAWAL_TIME[item.key]}.[/B]" if item.key in WITHDRAWAL_TIME else ""
        y = p.paragraph(y, f"[B]{i}. {item.label}[/B] - {item.subject}.{status}", size=40, after=5)
        y = p.paragraph(y, f"{item.author}; размещено {date_posted(item)}.", size=30, color=previous.MUTED, after=23, indent=25)
    y = p.heading(y + 18, "II.  ИНИЦИАТИВА")
    item = ITEM["cec"]
    y = p.paragraph(y, f"[B]Инициатива[/B] - {item.subject}.", size=40, after=5)
    y = p.paragraph(y, f"{item.author}; размещено {date_posted(item)}.", size=30, color=previous.MUTED, after=25, indent=25)
    y = p.heading(y + 18, "III.  ПРИМЕЧАНИЯ")
    for i, value in enumerate((WITHDRAWN_NOTE, "По ACT. 299 и 300 проведён один совместный опрос.", ACT308_NOTE,
                               "Для сообщений без явной даты указано только время размещения."), 1):
        y = p.paragraph(y, f"[B]{i}.[/B] {value}", size=37, after=18)
    return p.footer(p.signature(y) + 65)


def draw_results(p):
    y = p.header("ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ", "ОФИЦИАЛЬНОЕ СООБЩЕНИЕ СПИКЕРА СЕНАТА")
    for value in INTRO:
        y = p.paragraph(y, value, size=42, after=24)
    y = p.heading(y + 20, "I.  РЕЗУЛЬТАТЫ ГОЛОСОВАНИЙ")
    y = p.poll_table(y)
    y = p.heading(y + 20, "II.  ОТОЗВАННЫЕ ПРОЕКТЫ")
    y = p.paragraph(y, WITHDRAWN_NOTE, size=40, after=30)
    y = p.heading(y + 20, "III.  ПРИМЕЧАНИЯ")
    for i, value in enumerate((SOURCE_NOTE, ENACTMENT_NOTE), 1):
        y = p.paragraph(y, f"[B]{i}.[/B] {value}", size=38, after=21)
    return p.footer(p.signature(y) + 65)


def render_png(path, agenda=False):
    faces = previous.font_faces()
    scratch = Image.new("RGB", (1, 1), "white")
    measure = Painter(ImageDraw.Draw(scratch), scratch, faces, False)
    draw = draw_agenda if agenda else draw_results
    bottom = draw(measure)
    height = int(bottom + 130)
    image = Image.new("RGB", (previous.W, height), "white")
    painter = Painter(ImageDraw.Draw(image), image, faces, True)
    actual = draw(painter)
    if actual != bottom or actual > height - 100:
        raise ValueError("Ошибка расчёта высоты документа")
    painter.rectangle((116, 92, previous.W - 124, height - 95), outline=previous.GREEN, width=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", dpi=(300, 300), optimize=True)
    return image.size


def main():
    validate_source()
    AGENDA_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    for directory, name, markdown, bb, agenda in (
        (AGENDA_DIR, AGENDA_NAME, agenda_markdown(), agenda_bb(), True),
        (RESULT_DIR, RESULT_NAME, results_markdown(), result_bb(), False),
    ):
        (directory / f"{name}.md").write_text(markdown, encoding="utf-8")
        (directory / f"{name} - BB-код.txt").write_text(bb, encoding="utf-8")
        path = directory / f"{name}.png"
        print("PNG", path.relative_to(ROOT), render_png(path, agenda))


if __name__ == "__main__":
    main()
