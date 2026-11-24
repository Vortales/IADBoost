# -*- coding: utf-8 -*-
"""Созыв 25.11.2026: содержание и оформление образца 19.11 с заменой даты.

Ссылки на нормы и сведения о месте и подписанте воспроизведены из образца;
перед публикацией требуется сверка, описанная в README заседания.
Для PNG нужны Pillow и Times New Roman Regular, Bold и Italic. При необходимости
укажите SENATE_FONT_DIR с файлами times.ttf, timesbd.ttf и timesi.ttf.
Только текстовые файлы можно обновить без Pillow и шрифтов: --text-only.
"""
import argparse
import re
import sys
from contextlib import contextmanager
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import make_senat_session_19_11 as template

ROOT = TOOLS.parent
OUT_DIR = ROOT / "Повестка" / "25.11.26" / "01 Созыв"
SAMPLE_DIR = ROOT / "Повестка" / "19.11.2026" / "01 Созыв"
BASENAME = "Созыв заседания Сената - 25.11.2026"
BB_FILENAME = f"{BASENAME} - BB-код.txt"
PLAIN_FILENAME = "25.11.26.txt"


def new_date(text):
    """Заменяет в тексте образца только дату сообщения и заседания."""
    return (text.replace("19 ноября 2026 года", "25 ноября 2026 года")
                .replace("19 НОЯБРЯ 2026 ГОДА", "25 НОЯБРЯ 2026 ГОДА"))


DATE_LINE = new_date(template.DATE_LINE)
RIGHT_META = template.RIGHT_META
TITLE = template.TITLE
SUBTITLE = template.SUBTITLE
LEAD = template.LEAD
BAND = new_date(template.BAND)
LAW = template.LAW
CLOSING = template.CLOSING
LOGO_URL = template.LOGO_URL
SECTIONS = tuple(
    (heading, tuple(
        (number, tuple((new_date(value), style) for value, style in fragments))
        for number, fragments in paragraphs
    ))
    for heading, paragraphs in template.SECTIONS
)


def markdown():
    """Точный текст Markdown-образца с заменой даты 19 на 25 ноября."""
    sample = SAMPLE_DIR / f"{template.BASENAME}.md"
    return new_date(sample.read_text(encoding="utf-8"))


def bbcode():
    """Точный BB-код образца с заменой даты 19 на 25 ноября."""
    return new_date((SAMPLE_DIR / template.BB_FILENAME).read_text(encoding="utf-8"))


def plain_text():
    """Текст самого сообщения без Markdown-разметки и служебного предисловия."""
    _, separator, content = markdown().partition("\n---\n\n")
    if not separator:
        raise ValueError("Не найдено начало сообщения в Markdown-образце")
    return re.sub(r"(?m)^#{1,6}\s+", "", content).replace("*", "")


@contextmanager
def configured_template():
    """Временно подставляет дату, не меняя генератор образца и его файлы."""
    names = ("DATE_LINE", "BAND", "SECTIONS")
    original = {name: getattr(template, name) for name in names}
    try:
        template.DATE_LINE = DATE_LINE
        template.BAND = BAND
        template.SECTIONS = SECTIONS
        yield
    finally:
        for name, value in original.items():
            setattr(template, name, value)


def render_png(path):
    """Собирает PNG той же вёрсткой, что исходный созыв 19 ноября."""
    import make_senat_session_png as layout

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    faces = template.font_faces()
    with configured_template(), template.configured_layout(faces):
        layout.build(str(path))
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
