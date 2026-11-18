# -*- coding: utf-8 -*-
"""Созыв заседания 19.11.2026: один текст для PNG и Markdown.

Вёрстка и печати взяты из созыва 13.11, исходный документ не перезаписывается.
Для PNG необходимы Times New Roman Regular, Bold и Italic; при необходимости
укажите SENATE_FONT_DIR с файлами times.ttf, timesbd.ttf и timesi.ttf.
"""
import argparse
import os
from contextlib import contextmanager
from pathlib import Path

from PIL import ImageFont

import make_senat_session_png as layout

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "Повестка" / "19.11.2026" / "01 Созыв"
BASENAME = "Созыв заседания Сената - 19.11.2026"
DATE_LINE = "19 ноября 2026 года, г. Лос-Сантос"
RIGHT_META = "Спикер Сената Marcus Nomad, номер паспорта 85028"
TITLE = "О СОЗЫВЕ ПЛЕНАРНОГО ЗАСЕДАНИЯ"
SUBTITLE = "официальное сообщение Спикера Сената штата Сан-Андреас"
LEAD = "Настоящим объявляю созыв пленарного заседания Сената штата Сан-Андреас."
BAND = "19 НОЯБРЯ 2026 ГОДА, 19:00"
LAW = "Конституционного закона «О Сенате штата Сан-Андреас»"
CLOSING = "Прошу сенаторов обеспечить явку к указанному времени."

# Текст один и тот же для Markdown и изображения. В отдельных фрагментах
# полужирным выделено название акта; номер паспорта не обозначается как ID.
SECTIONS = (
    ("I. СВЕДЕНИЯ О ЗАСЕДАНИИ", (
        ("1.1.", (("Пленарное заседание Сената штата Сан-Андреас состоится "
                   "19 ноября 2026 года в 19:00 в зале заседаний Сената, "
                   "Капитолий штата Сан-Андреас, город Лос-Сантос.", "r"),)),
        ("1.2.", (("Заседание созывается Спикером Сената штата Сан-Андреас "
                   "Marcus Nomad (пункт «а» части 4 статьи 3 ", "r"),
                  (LAW, "b"), ("); он же председательствует.", "r"))),
    )),
    ("II. ЯВКА И ПРАВОМОЧНОСТЬ", (
        ("2.1.", (("При неявке на плановое заседание Спикер Сената вправе "
                   "применить меры, предусмотренные пунктом «и» части 4 статьи 3 ", "r"),
                  (LAW, "b"), (".", "r"))),
        ("2.2.", (("Заседание правомочно при присутствии не менее половины "
                   "действующих сенаторов (часть 1 статьи 9 ", "r"),
                  (LAW, "b"), (").", "r"))),
    )),
)


def markdown():
    """Текст созыва, составленный из тех же фрагментов, что и PNG."""
    lines = [
        "# О созыве пленарного заседания Сената - 19 ноября 2026 года",
        "",
        "Официальное сообщение Спикера Сената штата Сан-Андреас Marcus Nomad.",
        "PNG оформлен по образцу созыва 13.11.2026.",
        "",
        "---",
        "",
        "**СЕНАТ ШТАТА САН-АНДРЕАС**",
        "",
        f"**{TITLE}**",
        "",
        f"*{SUBTITLE}*",
        "",
        DATE_LINE,
        "",
        f"*{RIGHT_META}*",
        "",
        LEAD,
        "",
        f"**{BAND}**",
        "",
    ]
    for heading, paragraphs in SECTIONS:
        lines.extend((f"## {heading}", ""))
        for number, fragments in paragraphs:
            text = "".join(f"**{value}**" if style == "b" else value
                           for value, style in fragments)
            lines.extend((f"**{number}** {text}", ""))
    lines.extend((CLOSING, "", "С уважением,", "", "**Marcus Nomad**", "",
                  "*Спикер Сената штата Сан-Андреас*", "", "19 ноября 2026 года", ""))
    return "\n".join(lines)


def font_faces():
    """Находит настоящие начертания Times New Roman, без подмены шрифта."""
    roots = (os.environ.get("SENATE_FONT_DIR"), "/usr/share/fonts/truetype/msttcorefonts",
             "/usr/share/fonts/truetype/microsoft", "/usr/local/share/fonts", "/mnt/c/Windows/Fonts")
    names = (("times.ttf", "timesbd.ttf", "timesi.ttf"),
             ("Times New Roman.ttf", "Times New Roman Bold.ttf", "Times New Roman Italic.ttf"))
    for root in filter(None, roots):
        for triple in names:
            faces = tuple(Path(root) / name for name in triple)
            if all(path.is_file() for path in faces):
                info = [ImageFont.truetype(str(path), 12).getname() for path in faces]
                if all(family == "Times New Roman" and style.lower() == expected
                       for (family, style), expected in zip(info, ("regular", "bold", "italic"))):
                    return faces
    raise SystemExit("Нужны Times New Roman Regular, Bold и Italic; укажите SENATE_FONT_DIR")


def body(d, size, draw=True):
    """Повторяет расположение текста образца, используя данные нового созыва."""
    y = 1035
    y = layout.para(d, y, [(LEAD, "r", layout.INK)], size=size, lh=int(size * 1.62),
                    justify=False, space_after=int(size * 1.25), draw=draw)
    y = layout.band(d, y, size, draw)
    y += int(size * 1.0)
    y = layout.sections(d, y, size, draw)
    y += int(size * 0.35)
    return layout.para(d, y, [(CLOSING, "r", layout.INK)], size=size,
                       lh=int(size * 1.62), justify=False, draw=draw)


def configure_layout(faces):
    """Использует прежнюю графическую форму только с данными нового созыва."""
    for module in (layout, layout.base):
        module.FR, module.FB, module.FI = (str(path) for path in faces)
    layout.base._cache.clear()
    layout.DATE_LINE = DATE_LINE
    layout.RIGHT_META = RIGHT_META
    layout.TITLE = TITLE
    layout.SUBTITLE = SUBTITLE
    layout.LEAD = LEAD
    layout.BAND = BAND
    layout.body = body
    layout.SECTIONS = [
        (heading.replace(". ", ".  ", 1), [
            [(number, "b", layout.GREEN_D)] + [
                ((" " if i == 0 else "") + value, style, layout.INK)
                for i, (value, style) in enumerate(fragments)
            ]
            for number, fragments in paragraphs
        ])
        for heading, paragraphs in SECTIONS
    ]


@contextmanager
def configured_layout(faces):
    """Не оставляет данные 19.11 в общем модуле созыва 13.11 после сборки."""
    names = ("FR", "FB", "FI", "DATE_LINE", "RIGHT_META", "TITLE", "SUBTITLE",
             "LEAD", "BAND", "body", "SECTIONS")
    old_layout = {name: getattr(layout, name) for name in names}
    old_base = {name: getattr(layout.base, name) for name in ("FR", "FB", "FI")}
    try:
        configure_layout(faces)
        yield
    finally:
        for name, value in old_layout.items():
            setattr(layout, name, value)
        for name, value in old_base.items():
            setattr(layout.base, name, value)
        layout.base._cache.clear()


def build(output_dir=OUT_DIR):
    """Создаёт только созыв 19.11 в указанной папке, не меняя старые файлы."""
    faces = font_faces()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with configured_layout(faces):
        layout.build(str(output_dir / f"{BASENAME}.png"))
        (output_dir / f"{BASENAME}.md").write_text(markdown(), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR,
                        help="папка для PNG и Markdown")
    build(parser.parse_args().output_dir)
