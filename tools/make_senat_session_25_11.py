# -*- coding: utf-8 -*-
"""Сообщение о заседании Сената 25.11.2026: PNG, текст и BB-код.

Форма использует рамку и графические элементы созыва от 19.11.2026, но не
переносит неподтверждённые место, подпись или ссылки на нормы из образца.
Для PNG нужны Pillow и Times New Roman Regular, Bold и Italic; при необходимости
укажите SENATE_FONT_DIR с файлами times.ttf, timesbd.ttf и timesi.ttf.
Только текстовые файлы можно обновить без этих зависимостей: --text-only.
"""
import argparse
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "Повестка" / "25.11.26" / "01 Созыв"
BASENAME = "Созыв заседания Сената - 25.11.2026"
BB_FILENAME = f"{BASENAME} - BB-код.txt"
PLAIN_FILENAME = "25.11.26.txt"
LOGO_URL = "https://i.ibb.co/zVnGyqQv/1.png"

TITLE = "О СОЗЫВЕ ЗАСЕДАНИЯ СЕНАТА"
SUBTITLE = "Сообщение о предстоящем заседании"
DATE_META = "Заседание: 25 ноября 2026 года"
TIME_META = "Начало: 19:00"
LEAD = "Сообщаем о предстоящем заседании Сената штата Сан-Андреас."
BAND = "25 НОЯБРЯ 2026 ГОДА, 19:00"
SECTIONS = (
    ("I. СВЕДЕНИЯ О ЗАСЕДАНИИ", "1.1.",
     "Заседание Сената штата Сан-Андреас состоится 25 ноября 2026 года в 19:00."),
    ("II. УЧАСТИЕ В ЗАСЕДАНИИ", "2.1.",
     "Просим сенаторов обеспечить явку к указанному времени."),
)


def plain_text():
    """Версия для сообщения без разметки."""
    lines = ["СЕНАТ ШТАТА САН-АНДРЕАС", "", TITLE, SUBTITLE, "", DATE_META,
             TIME_META, "", LEAD, "", BAND, ""]
    for heading, number, text in SECTIONS:
        lines.extend((heading, "", f"{number} {text}", ""))
    return "\n".join(lines)


def markdown():
    """Текст из того же источника, что PNG и форумная версия."""
    lines = ["# Созыв заседания Сената - 25 ноября 2026 года", "",
             "**СЕНАТ ШТАТА САН-АНДРЕАС**", "", f"**{TITLE}**", "",
             f"*{SUBTITLE}*", "", f"*{DATE_META}*", "", f"*{TIME_META}*", "",
             LEAD, "", f"**{BAND}**", ""]
    for heading, number, text in SECTIONS:
        lines.extend((f"## {heading}", "", f"**{number}** {text}", ""))
    return "\n".join(lines)


def bbcode():
    """BB-код для размещения на форуме, без вложенных тегов размера."""
    lines = [
        "[FONT=Times New Roman]", "[CENTER]",
        f'[IMG width="320px"]{LOGO_URL}[/IMG]', "",
        "[I][B][COLOR=rgb(97, 189, 109)][SIZE=6]STATE of SAN ANDREAS[/SIZE][/COLOR][/B][/I]",
        "[B][I][COLOR=rgb(97, 189, 109)][SIZE=6]SENATE OF THE STATE OF SAN ANDREAS[/SIZE][/COLOR][/I][/B]",
        "", f"[I][B][SIZE=6]{TITLE}[/SIZE][/B][/I]",
        f"[I][SIZE=4]{SUBTITLE.upper()}[/SIZE][/I]", "[/CENTER]", "",
        f"[SIZE=4][I]{DATE_META}[/I][/SIZE]",
        f"[SIZE=4][I]{TIME_META}[/I][/SIZE]", "", f"[SIZE=5]{LEAD}[/SIZE]", "",
        f"[CENTER][B][I][SIZE=6]{BAND}[/SIZE][/I][/B][/CENTER]", "",
    ]
    for heading, number, text in SECTIONS:
        lines.extend((f"[CENTER][B][I][SIZE=6]{heading}[/SIZE][/I][/B][/CENTER]", "",
                      f"[SIZE=5][B]{number}[/B] {text}[/SIZE]", ""))
    lines.extend(("[/FONT]", ""))
    return "\n".join(lines)


@contextmanager
def configured_layout():
    """Временно подставляет шрифты и полосу даты в существующую вёрстку."""
    import make_senat_session_19_11 as previous
    import make_senat_session_png as layout

    faces = previous.font_faces()
    old_layout = {name: getattr(layout, name) for name in ("FR", "FB", "FI", "BAND")}
    old_base = {name: getattr(layout.base, name) for name in ("FR", "FB", "FI")}
    try:
        for module in (layout, layout.base):
            module.FR, module.FB, module.FI = (str(path) for path in faces)
        layout.BAND = BAND
        layout.base._cache.clear()
        yield layout
    finally:
        for name, value in old_layout.items():
            setattr(layout, name, value)
        for name, value in old_base.items():
            setattr(layout.base, name, value)
        layout.base._cache.clear()


def render_png(path):
    """Рисует страницу по образцу, не добавляя неподтверждённую подпись."""
    from PIL import Image, ImageDraw

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with configured_layout() as layout:
        img = Image.new("RGB", (layout.W, layout.H), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle(layout.FRAME, outline=layout.GREEN, width=9)

        with Image.open(Path(layout.ASSETS) / "state_emblem.png") as source:
            emblem = source.convert("RGB").resize((236, 236), Image.LANCZOS)
        img.paste(emblem, (layout.CENTER - 118, 152))
        layout.base.title_mixed(draw, 450, [("STATE", layout.F(layout.FB, 56), 10),
                                             ("of", layout.F(layout.FI, 48), 2),
                                             ("SAN ANDREAS", layout.F(layout.FB, 56), 10)])
        layout.tracked(draw, 552, "SENATE OF THE STATE OF SAN ANDREAS",
                       layout.F(layout.FB, 25), 7, layout.GREEN)
        draw.line([(900, 628), (2100, 628)], fill=layout.GREEN, width=3)
        layout.tracked(draw, 676, TITLE, layout.F(layout.FB, 52), 3, layout.INK)
        layout.tracked(draw, 772, SUBTITLE.upper(), layout.F(layout.FR, 22), 2, layout.MUTED)

        meta_font = layout.F(layout.FI, 25)
        draw.text((layout.BODY_L, 858), DATE_META, font=meta_font, fill=layout.MUTED)
        draw.text((layout.BODY_R - layout.tw(draw, TIME_META, meta_font), 858),
                  TIME_META, font=meta_font, fill=layout.MUTED)
        draw.line([(layout.BODY_L, 906), (layout.BODY_R, 906)], fill=layout.RULE, width=2)

        size = 64
        y = layout.para(draw, 1035, [(LEAD, "r", layout.INK)], size=size,
                        lh=int(size * 1.62), justify=False, space_after=80)
        y = layout.band(draw, y, size)
        y += 120
        for heading, number, text in SECTIONS:
            y = layout.heading(draw, y, heading.replace(". ", ".  ", 1), size=58)
            y = layout.para(draw, y, [(number, "b", layout.GREEN_D),
                                      (" " + text, "r", layout.INK)],
                            hang=92, size=size, lh=int(size * 1.62),
                            justify=False, space_after=145)
        if y > 3120:
            raise ValueError("Текст созыва не помещается над печатью")

        with Image.open(Path(layout.ASSETS) / "great_seal.png") as source:
            seal = source.convert("RGBA").resize((708, 708), Image.LANCZOS)
        img.paste(seal, (layout.BODY_L + 10, 3938 - 708 - 6), seal)
        draw.line([(layout.BODY_L, 3940), (layout.BODY_R, 3940)], fill=layout.RULE, width=2)
        layout.tracked(draw, 3976, "STATE OF SAN ANDREAS  ·  SENATE",
                       layout.F(layout.FR, 21), 8, layout.MUTED)
        img.save(path, "PNG", dpi=(300, 300))
    return path


def build_texts(output_dir=OUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = (output_dir / PLAIN_FILENAME, output_dir / f"{BASENAME}.md", output_dir / BB_FILENAME)
    for path, text in zip(paths, (plain_text(), markdown(), bbcode())):
        path.write_text(text, encoding="utf-8")
    return paths


def build(output_dir=OUT_DIR):
    output_dir = Path(output_dir)
    image = render_png(output_dir / f"{BASENAME}.png")
    return (image, *build_texts(output_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR,
                        help="папка для изображения и текстовых версий")
    parser.add_argument("--text-only", action="store_true",
                        help="обновить только Markdown, обычный текст и BB-код")
    args = parser.parse_args()
    for result in (build_texts(args.output_dir) if args.text_only else build(args.output_dir)):
        print("OK", result)
