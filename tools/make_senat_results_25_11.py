# -*- coding: utf-8 -*-
"""Итоги 25.11.2026 по четырём переданным опросам: Markdown, BB-код и PNG.

По уточнению пользователя перед голосованиями ACT. 316 и 317 учитывались 17
действующих сенаторов, а закрытие заседания было после рассмотрения ACT. 316.
Показаны отметки сообщений, а не предполагаемые интервалы заседания. Существующие
файлы не перезаписываются без --force; протокол и журнал скрипт не создаёт.
"""
from dataclasses import dataclass
from pathlib import Path
import argparse
import re

from PIL import Image, ImageDraw, ImageFont

import make_senat_documents_13_11 as base


ROOT = Path(__file__).resolve().parent.parent
SESSION = ROOT / "Повестка" / "25.11.26"
SOURCE = SESSION / "05 Исходные данные" / "Голосования 25.11.2026 - сведения пользователя.txt"
ATTENDANCE = SESSION / "Присутствующие"
OUTPUT_DIR = SESSION / "03 Итоги"
BASENAME = "Итоги пленарного заседания Сената 25.11.2026"
LOGO_URL = "https://i.ibb.co/zVnGyqQv/1.png"
SPEAKER = "Спикер Сената Marcus Nomad, номер паспорта 85028"
PROSECUTOR = "Разместил Генеральный прокурор Pravik Killaz, номер паспорта 91999"
BILL_ACTIVE_COUNT = 17  # уточнение пользователя для обоих голосований
BILL_MAJORITY = BILL_ACTIVE_COUNT // 2 + 1


@dataclass(frozen=True)
class Poll:
    key: str
    source_heading: str
    title: str
    meta: str
    post_time: str | None
    notice_time: str
    yes: int
    no: int
    abstain: int
    percentages: tuple[int, int, int]
    outcome: str
    url: str = ""

    @property
    def total(self):
        return self.yes + self.no + self.abstain

    @property
    def time_marks(self):
        return f"{self.post_time or '-'} / {self.notice_time}"

    @property
    def result_line(self):
        a, b, c = self.percentages
        return (f"За: {self.yes} ({a}%). Против: {self.no} ({b}%). "
                f"Воздержался: {self.abstain} ({c}%). Всего: {self.total}.")

    @property
    def detail_line(self):
        a, b, c = self.percentages
        return f"Всего {self.total} голосов: за - {a}%, против - {b}%, воздержался - {c}%."


POLLS = (
    Poll("open", "Открытие заседания", "[B]Открытие заседания[/B]", SPEAKER,
         "19:15", "19:26", 11, 0, 1, (92, 0, 8), "Открыто"),
    Poll("317", "ACT. 317", "[B]ACT. 317[/B] - изменение закона об офисе Генерального прокурора; заявлено удаление должности помощника прокурора",
         PROSECUTOR, "19:18", "19:27", 11, 1, 0, (92, 8, 0), "Принят Сенатом",
         "https://docs.google.com/document/d/1UV4n3S-7wMGSkGfVsVxinN1G0_NfFuwIvZfybCJUuvo/edit?usp=sharing"),
    Poll("316", "ACT. 316", "[B]ACT. 316[/B] - изменение Процессуального кодекса: направление уголовного дела в суд",
         PROSECUTOR, "19:20", "19:31", 11, 0, 1, (92, 0, 8), "Принят Сенатом",
         "https://docs.google.com/document/d/1kTukWWpBi4HVhwt-0Yaaozt5HMDShKwIbWAJidscTtI/edit?usp=sharing"),
    Poll("close", "Закрытие заседания", "[B]Закрытие заседания[/B]", "Опрос о закрытии заседания",
         None, "19:27", 9, 1, 1, (82, 9, 9), "Закрыто"),
)

INTRO = (
    "25 ноября 2026 года состоялось пленарное заседание Сената штата Сан-Андреас. Сообщения с опросами об открытии и по законопроектам размещены Спикером Сената Marcus Nomad, номер паспорта 85028.",
    f"В представленном списке присутствующих указаны 13 человек. Перед голосованиями по ACT. 316 и ACT. 317 для подсчёта учитывались {BILL_ACTIVE_COUNT} действующих сенаторов; для большинства необходимо {BILL_MAJORITY} голосов за.",
    "Опросы по проектам расположены по отметкам сообщений; закрытие приведено отдельно. Перечень не устанавливает полный состав вопросов заседания.",
)
NOTES = (
    "В столбце «Время*» указаны отметки сообщения с опросом и уведомления о его завершении; знак «-» означает, что отдельная отметка размещения не указана. В копии отметки обозначены «вчера», без явной календарной даты и часового пояса; это не время фактического открытия или закрытия заседания.",
    "Отметка уведомления по закрытию - 19:27, по ACT. 316 - 19:31. Фактически заседание закрыто после рассмотрения ACT. 316; точное время закрытия не указано.",
    f"По ACT. 316 и ACT. 317 подано по 11 голосов за при {BILL_ACTIVE_COUNT} действующих сенаторах. Принятие законопроекта Сенатом не подтверждает судебного одобрения, подписания, обнародования или вступления закона в силу.",
    "В графе воздержавшихся приведены голоса соответствующего варианта опроса; разница между списком присутствующих и числом голосов автоматически не распределена. Список не устанавливает поимённого участия в каждом опросе.",
)


def plain(value):
    return re.sub(r"\[/?[BI]\]", "", value)


def validate_source():
    text = SOURCE.read_text(encoding="utf-8")
    if "25.11.2026" not in text or "Это не оригинальная выгрузка Discord" not in text:
        raise ValueError("Не найдена дата заседания или оговорка об источнике")
    if (f"Перед голосованиями по ACT. 316 и ACT. 317 учитывались "
            f"{BILL_ACTIVE_COUNT} действующих сенаторов.") not in text:
        raise ValueError("Не подтверждено число действующих сенаторов для ACT. 316 и 317")
    if "Фактическое закрытие заседания состоялось после рассмотрения ACT. 316" not in text:
        raise ValueError("Не подтверждён порядок рассмотрения и закрытия")
    for poll in (poll for poll in POLLS if poll.key in ("316", "317")):
        if poll.yes < BILL_MAJORITY or poll.outcome != "Принят Сенатом":
            raise ValueError(f"Неверно определён результат голосования: {poll.key}")
    # Сохраняем порядок сводки независимо от порядка строк в итогах.
    starts = []
    for poll in POLLS:
        matches = list(re.finditer(rf"(?m)^{re.escape(poll.source_heading)}$", text))
        if len(matches) != 1:
            raise ValueError(f"Не найден уникальный опрос: {poll.source_heading}")
        starts.append((matches[0].start(), poll))
    starts.sort(key=lambda item: item[0])
    end = text.index("Поимённый список присутствующих", starts[-1][0])
    for i, (start, poll) in enumerate(starts):
        section = text[start:starts[i + 1][0] if i + 1 < len(starts) else end]
        if poll.result_line not in section:
            raise ValueError(f"Не совпадают голоса или проценты: {poll.key}")
        if poll.post_time and not re.search(
                rf"(?m)^Сообщение с опросом[^\n]*, {re.escape(poll.post_time)} \(", section):
            raise ValueError(f"Не найдена отметка сообщения: {poll.key}")
        if not re.search(rf"(?m)^Опрос завершён\. Отметка уведомления [^\n]*: "
                         rf"{re.escape(poll.notice_time)} \(", section):
            raise ValueError(f"Не найдена отметка уведомления: {poll.key}")
        if poll.url and poll.url not in section:
            raise ValueError(f"Не найдена ссылка на проект: {poll.key}")
    attendance = ATTENDANCE.read_text(encoding="utf-8")
    if (len(re.findall(r"(?m)^• ", attendance)) != 13 or "25.11.26" not in attendance
            or "Marcus Nomad | 85028" not in attendance or "Pravik Killaz | 91999" not in attendance):
        raise ValueError("Список присутствующих изменился: нужна повторная проверка")
    return True


def result_markdown():
    lines = [f"# {BASENAME}", "", *INTRO, "", "## Результаты голосований", "",
             "| Время* | Вопрос | За | Против | Воздержался | Всего | Итог |",
             "|---|---|---:|---:|---:|---:|---|"]
    for poll in POLLS:
        title = plain(poll.title)
        if poll.url:
            title = f"[{title}]({poll.url})"
        lines.append(f"| {poll.time_marks} | {title} | {poll.yes} | {poll.no} | {poll.abstain} | {poll.total} | {poll.outcome} |")
    lines += ["", "Ссылки на ACT. 316 и ACT. 317 разместил Генеральный прокурор Pravik Killaz, номер паспорта 91999.",
              "", "## Примечания", ""]
    lines.extend(f"- {note}" for note in NOTES)
    return "\n".join(lines) + "\n"


def bb_text(value, size=5):
    return f"[SIZE={size}]{value}[/SIZE]"


def result_bbcode():
    text = ('[FONT=Times New Roman]\n[CENTER]\n'
            f'[IMG width="320px"]{LOGO_URL}[/IMG]\n\n'
            '[I][B][COLOR=rgb(97, 189, 109)][SIZE=6]STATE of SAN ANDREAS[/SIZE][/COLOR][/B][/I]\n'
            '[B][I][COLOR=rgb(97, 189, 109)][SIZE=6]OFFICE of THE SPEAKER of THE SENATE[/SIZE][/COLOR][/I][/B]\n\n'
            '[I][B][SIZE=6]ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ СЕНАТА[/SIZE][/B][/I]\n'
            '[B][I][SIZE=6]25 ноября 2026 года[/SIZE][/I][/B]\n[/CENTER]\n\n')
    text += "\n\n".join(bb_text(p) for p in INTRO)
    text += "\n\n[CENTER][B][I][SIZE=6]Результаты голосований[/SIZE][/I][/B][/CENTER]\n\n"
    headers = (("Время*", 15), ("Вопрос", 39), ("За", 7), ("Против", 9),
               ("Воздержался", 12), ("Итог", 18))
    rows = ['[TABLE width="100%"]', '[TR]']
    rows.extend(f'[td width="{width}%"][CENTER]{bb_text(f"[B][I]{name}[/I][/B]")}[/CENTER][/td]'
                for name, width in headers)
    rows.append('[/TR]')
    for poll in POLLS:
        title = f"[URL='{poll.url}']{poll.title}[/URL]" if poll.url else poll.title
        question = "\n".join((bb_text(title), bb_text(poll.meta, 3), bb_text(poll.detail_line)))
        outcome = f"[B][COLOR=rgb(97, 189, 109)]{poll.outcome}[/COLOR][/B]"
        values = (poll.time_marks, question, str(poll.yes), str(poll.no), str(poll.abstain), outcome)
        rows.append('[TR]')
        for i, value in enumerate(values):
            cell = value if i == 1 else bb_text(value)
            rows.append(f'[td]{cell if i == 1 else f"[CENTER]{cell}[/CENTER]"}[/td]')
        rows.append('[/TR]')
    rows.append('[/TABLE]')
    text += "\n".join(rows)
    text += "\n\n[CENTER][B][I][SIZE=6]Примечания[/SIZE][/I][/B][/CENTER]\n\n[LIST=1]\n"
    text += "\n".join("[*]" + bb_text(note) for note in NOTES)
    text += ("\n[/LIST]\n\n[RIGHT]\n[SIZE=5][B]Спикер Сената штата Сан-Андреас\n"
             "Marcus Nomad[/B]\nНомер паспорта 85028[/SIZE]\n[/RIGHT]\n[/FONT]\n")
    return text


def font_faces(family="times", directory=None):
    if family == "times" and directory is None:
        return base.font_faces()
    if directory is None:
        raise ValueError("Для выбранного шрифта необходимо указать --font-dir")
    directory = Path(directory)
    names = (("times.ttf", "timesbd.ttf", "timesi.ttf") if family == "times" else
             ("Tinos-Regular.ttf", "Tinos-Bold.ttf", "Tinos-Italic.ttf"))
    paths = tuple(directory / name for name in names)
    if not all(path.is_file() for path in paths):
        raise ValueError(f"Отсутствуют файлы шрифтов в {directory}")
    expected_family = "Times New Roman" if family == "times" else "Tinos"
    expected_styles = ("regular", "bold", "italic")
    for path, style in zip(paths, expected_styles):
        actual_family, actual_style = ImageFont.truetype(str(path), 12).getname()
        if actual_family != expected_family or actual_style.lower() != style:
            raise ValueError(f"Некорректный шрифт: {path}, {actual_family} {actual_style}")
    return paths


class Painter(base.DocumentPainter):
    def header(self):
        if self.painting:
            emblem = Image.open(base.ASSETS / "state_emblem.png").convert("RGB").resize((250, 250), Image.Resampling.LANCZOS)
            self.image.paste(emblem, (base.CENTER - 125, 150))
        self.centered(440, "STATE of SAN ANDREAS", "b", 68, base.GREEN)
        self.centered(535, "SENATE OF THE STATE OF SAN ANDREAS", "b", 30, base.GREEN)
        self.line([(850, 612), (2150, 612)], fill=base.GREEN, width=3)
        self.centered(655, "ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ", "b", 62, base.INK)
        self.centered(745, "СВОДКА ПО ПРЕДСТАВЛЕННЫМ ГОЛОСОВАНИЯМ", "r", 30, base.MUTED)
        self.text(base.LEFT, 830, "Заседание 25 ноября 2026 года", "i", 32, base.MUTED)
        self.text(base.RIGHT - self.width(SPEAKER, "i", 32), 830, SPEAKER, "i", 32, base.MUTED)
        self.line([(base.LEFT, 880), (base.RIGHT, 880)], fill=base.RULE, width=2)
        return 945

    def poll_table(self, y):
        widths = (280, 1130, 130, 170, 180, 630)
        heads = ("Время*", "Вопрос", "За", "Против", "Возд.", "Итог")
        assert sum(widths) == base.BODY_W
        padx, pady, head_height = 17, 18, 82
        self.rectangle((base.LEFT, y, base.RIGHT, y + head_height), fill=base.SHADE)
        self.line([(base.LEFT, y), (base.RIGHT, y)], fill=base.GREEN_D, width=4)
        x = base.LEFT
        for head, width in zip(heads, widths):
            size = 35 if self.width(head, "b", 35) <= width - 2 * padx else 29
            self.text(x + (width - self.width(head, "b", size)) / 2, y + 21, head, "b", size, base.GREEN_D)
            x += width
        y += head_height
        for poll in POLLS:
            details = poll.detail_line
            title_lines = self.lines(poll.title, widths[1] - 2 * padx, 40)
            meta_lines = self.lines(poll.meta, widths[1] - 2 * padx, 30, "i")
            detail_lines = self.lines(details, widths[1] - 2 * padx, 34)
            height = 2 * pady + len(title_lines) * 54 + len(meta_lines) * 43 + len(detail_lines) * 47 + 20
            self.line([(base.LEFT, y + height), (base.RIGHT, y + height)], width=2)
            question_x = base.LEFT + widths[0] + padx
            title_y = y + pady
            meta_y = title_y + len(title_lines) * 54 + 5
            self.rich(question_x, title_y, poll.title, widths[1] - 2 * padx, 40, base.INK, line_height=54)
            self.rich(question_x, meta_y, poll.meta, widths[1] - 2 * padx, 30, base.MUTED, "i", line_height=43)
            self.rich(question_x, meta_y + len(meta_lines) * 43 + 5, details,
                      widths[1] - 2 * padx, 34, base.INK, line_height=47)
            values = (poll.time_marks, "", str(poll.yes), str(poll.no), str(poll.abstain), poll.outcome)
            x = base.LEFT
            for i, (value, width) in enumerate(zip(values, widths)):
                if i == 1:
                    x += width
                    continue
                size = 30 if i == 0 else 37
                style = "b" if i == len(values) - 1 else "r"
                if self.width(value, style, size) > width - 2 * padx:
                    raise ValueError(f"Ячейка {poll.key}/{i} не вмещается: {value}")
                color = base.GREEN_D if style == "b" else base.INK
                self.text(x + (width - self.width(value, style, size)) / 2,
                          y + (height - size) / 2 - 8, value, style, size, color)
                x += width
            y += height
        return y + 35

    def signature(self, y):
        y += 75
        if self.painting:
            seal = Image.open(base.ASSETS / "great_seal.png").convert("RGBA").resize((310, 310), Image.Resampling.LANCZOS)
            self.image.paste(seal, (base.LEFT + 35, int(y)), seal)
        self.line([(1650, y + 118), (base.RIGHT - 30, y + 118)], fill=base.INK, width=4)
        self.text(1690, y + 143, "Marcus Nomad", "b", 45, base.INK)
        self.text(1690, y + 200, "Спикер Сената штата Сан-Андреас", "i", 32, base.MUTED)
        self.text(1690, y + 244, "Номер паспорта 85028", "i", 30, base.MUTED)
        self.text(1690, y + 286, "Заседание 25 ноября 2026 года", "i", 30, base.MUTED)
        return y + 365


def draw_results(painter):
    y = painter.header()
    for paragraph in INTRO:
        y = painter.paragraph(y, paragraph, size=40, after=22)
    y = painter.heading(y + 20, "I.  РЕЗУЛЬТАТЫ ГОЛОСОВАНИЙ")
    y = painter.poll_table(y)
    y = painter.heading(y + 20, "II.  ПРИМЕЧАНИЯ")
    for number, note in enumerate(NOTES, 1):
        y = painter.paragraph(y, f"[B]{number}.[/B] {note}", size=37, after=18)
    return painter.footer(painter.signature(y) + 65)


def render_png(path, faces):
    scratch = Image.new("RGB", (1, 1), "white")
    bottom = draw_results(Painter(ImageDraw.Draw(scratch), scratch, faces, False))
    height = int(bottom + 130)
    image = Image.new("RGB", (base.W, height), "white")
    painter = Painter(ImageDraw.Draw(image), image, faces, True)
    actual = draw_results(painter)
    if actual != bottom or actual > height - 100:
        raise ValueError("Ошибка расчёта высоты документа")
    painter.rectangle((116, 92, base.W - 124, height - 95), outline=base.GREEN, width=9)
    image.save(path, format="PNG", dpi=(300, 300), optimize=True)
    return image.size


def build(output_dir=OUTPUT_DIR, *, force=False, text_only=False, family="times", font_dir=None):
    validate_source()
    output_dir = Path(output_dir)
    paths = [output_dir / f"{BASENAME}.md", output_dir / f"{BASENAME} - BB-код.txt"]
    if not text_only:
        paths.append(output_dir / f"{BASENAME}.png")
    if not force and any(path.exists() for path in paths):
        raise FileExistsError("Файлы итогов уже существуют; для пересборки явно укажите --force")
    faces = None if text_only else font_faces(family, font_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(result_markdown(), encoding="utf-8")
    paths[1].write_text(result_bbcode(), encoding="utf-8")
    if faces:
        render_png(paths[2], faces)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--font-family", choices=("times", "tinos"), default="times")
    parser.add_argument("--font-dir", type=Path)
    parser.add_argument("--text-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for path in build(args.output_dir, force=args.force, text_only=args.text_only,
                      family=args.font_family, font_dir=args.font_dir):
        print(path)


if __name__ == "__main__":
    main()
