# -*- coding: utf-8 -*-
"""Созыв заседания 19.11.2026: один текст для PNG, Markdown и BB-кода.

Вёрстка и печати взяты из созыва 13.11, исходный документ не перезаписывается.
Для PNG необходимы Times New Roman Regular, Bold и Italic; при необходимости
укажите SENATE_FONT_DIR с файлами times.ttf, timesbd.ttf и timesi.ttf.
BB-код можно обновить отдельно без пересборки изображения: --bb-only.
"""
import argparse
import os
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "Повестка" / "19.11.2026" / "01 Созыв"
BASENAME = "Созыв заседания Сената - 19.11.2026"
BB_FILENAME = f"{BASENAME} - BB-код.txt"
LOGO_URL = "https://i.ibb.co/zVnGyqQv/1.png"
DATE_LINE = "19 ноября 2026 года, г. Лос-Сантос"
RIGHT_META = "Спикер Сената Marcus Nomad, номер паспорта 85028"
TITLE = "О СОЗЫВЕ ПЛЕНАРНОГО ЗАСЕДАНИЯ"
SUBTITLE = "официальное сообщение Спикера Сената штата Сан-Андреас"
LEAD = "Настоящим объявляю созыв пленарного заседания Сената штата Сан-Андреас."
BAND = "19 НОЯБРЯ 2026 ГОДА, 19:00"
LAW = "Конституционного закона «О Сенате штата Сан-Андреас»"
CLOSING = "Прошу сенаторов обеспечить явку к указанному времени."

# Текст один и тот же для PNG, Markdown и BB-кода. В отдельных фрагментах
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


def bbcode():
    """Сообщение форума из тех же абзацев, что PNG и Markdown."""
    lines = [
        "[FONT=Times New Roman]",
        "[CENTER]",
        f'[IMG width="320px"]{LOGO_URL}[/IMG]',
        "",
        "[I][B][COLOR=rgb(97, 189, 109)][SIZE=6]STATE of SAN ANDREAS[/SIZE][/COLOR][/B][/I]",
        "[B][I][COLOR=rgb(97, 189, 109)][SIZE=6]SENATE OF THE STATE OF SAN ANDREAS[/SIZE][/COLOR][/I][/B]",
        "",
        f"[I][B][SIZE=6]{TITLE}[/SIZE][/B][/I]",
        f"[I][SIZE=4]{SUBTITLE.upper()}[/SIZE][/I]",
        "[/CENTER]",
        "",
        f"[SIZE=4][I]{DATE_LINE}[/I][/SIZE]",
        f"[SIZE=4][I]{RIGHT_META}[/I][/SIZE]",
        "",
        f"[SIZE=5]{LEAD}[/SIZE]",
        "",
        f"[CENTER][B][I][SIZE=6]{BAND}[/SIZE][/I][/B][/CENTER]",
        "",
    ]
    for heading, paragraphs in SECTIONS:
        lines.extend((f"[CENTER][B][I][SIZE=6]{heading}[/SIZE][/I][/B][/CENTER]", ""))
        for number, fragments in paragraphs:
            text = "".join(f"[B]{value}[/B]" if style == "b" else value
                           for value, style in fragments)
            lines.extend((f"[SIZE=5][B]{number}[/B] {text}[/SIZE]", ""))
    lines.extend((f"[SIZE=5]{CLOSING}[/SIZE]", "", "[RIGHT]", "[SIZE=5][B]Marcus Nomad[/B]",
                  "[I]Спикер Сената штата Сан-Андреас[/I][/SIZE]", "[/RIGHT]", "[/FONT]", ""))
    return "\n".join(lines)


def font_faces():
    """Находит настоящие начертания Times New Roman, без подмены шрифта."""
    from PIL import ImageFont

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
    import make_senat_session_png as layout

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
    import make_senat_session_png as layout

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
    import make_senat_session_png as layout

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


def build_bb(output_dir=OUT_DIR):
    """Записывает только BB-код, не изменяя изображение и текст созыва."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / BB_FILENAME
    path.write_text(bbcode(), encoding="utf-8")
    return path


def build(output_dir=OUT_DIR):
    """Создаёт PNG, Markdown и BB-код созыва 19.11 в указанной папке."""
    import make_senat_session_png as layout

    faces = font_faces()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with configured_layout(faces):
        layout.build(str(output_dir / f"{BASENAME}.png"))
        (output_dir / f"{BASENAME}.md").write_text(markdown(), encoding="utf-8")
        build_bb(output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR,
                        help="папка для PNG, Markdown и BB-кода")
    parser.add_argument("--bb-only", action="store_true",
                        help="обновить только BB-код без пересборки PNG")
    args = parser.parse_args()
    if args.bb_only:
        print("OK", build_bb(args.output_dir))
    else:
        build(args.output_dir)
