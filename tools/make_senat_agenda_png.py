# -*- coding: utf-8 -*-
"""Повестка пленарного заседания Сената - официальное сообщение (PNG).

Вёрстка та же, что у «Созыва заседания»: зелёная рамка, печать Сената,
двуязычная шапка, рубленые разделы и блок подписи. Прямые ссылки и название
сервиса размещения документов в PNG не печатаются.
"""
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 3000, 5200
GREEN = (69, 137, 63)
GREEN_D = (46, 92, 42)
INK = (26, 26, 26)
MUTED = (108, 112, 116)
RULE = (203, 208, 201)
FRAME = (116, 92, 2876, H - 85)
BODY_L, BODY_R = 300, 2700
BODY_W = BODY_R - BODY_L
CENTER = (BODY_L + BODY_R) // 2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "Обращения", "IAD — отзыв вето (Губернатор Harlow)", "assets")
OUT = os.path.join(ROOT, "Повестка", "Повестка заседания 13.11.2026.png")


def font_faces():
    """Нужны настоящие Times New Roman Regular, Bold и Italic; шрифты не поставляются в репозитории."""
    paths = (os.environ.get("SENATE_FONT_DIR"),
             "/usr/share/fonts/truetype/msttcorefonts",
             "/usr/share/fonts/truetype/microsoft",
             "/usr/local/share/fonts",
             "/mnt/c/Windows/Fonts",
             "C:/Windows/Fonts")
    layouts = (("times.ttf", "timesbd.ttf", "timesi.ttf"),
               ("Times New Roman.ttf", "Times New Roman Bold.ttf", "Times New Roman Italic.ttf"))
    for path in filter(None, paths):
        for layout in layouts:
            files = tuple(os.path.join(path, name) for name in layout)
            if all(os.path.isfile(f) for f in files):
                names = [ImageFont.truetype(f, 12).getname() for f in files]
                if all(family == "Times New Roman" and style.lower() == expected
                       for (family, style), expected in zip(names, ("regular", "bold", "italic"))):
                    return files
    raise SystemExit("Нужны Times New Roman Regular, Bold и Italic; укажите SENATE_FONT_DIR")


FR, FB, FI = font_faces()

_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tw(d, s, font):
    b = d.textbbox((0, 0), s, font=font)
    return b[2] - b[0]


def tracked(d, y, text, font, tracking, fill=INK, center_at=CENTER, draw=True):
    widths = [tw(d, ch, font) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = center_at - total / 2
    for ch, w in zip(text, widths):
        if draw:
            d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def title_mixed(d, y, parts, draw=True):
    """Двуязычная шапка: части идут подряд и центрируются как одно целое."""
    gap = 26
    total = sum(sum(tw(d, ch, f) for ch in text) + tr * (len(text) - 1)
                for text, f, tr in parts) + gap * (len(parts) - 1)
    x = CENTER - total / 2
    for text, f, tr in parts:
        for ch in text:
            if draw:
                d.text((x, y), ch, font=f, fill=GREEN)
            x += tw(d, ch, f) + tr
        x += gap
    return total


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(d, trial, font) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def style_font(style):
    return {"r": FR, "b": FB, "i": FI}[style]


def para(d, y, runs, width=BODY_W, left=BODY_L, hang=0, lh=None,
         size=30, justify=True, draw=True, space_after=0):
    """Абзац с висячим отступом: runs - список (текст, стиль, цвет)."""
    lh = lh or int(size * 1.62)
    tokens = []
    for text, style, color in runs:
        parts = text.split(" ")
        for i, part in enumerate(parts):
            if part:
                tokens.append((part, style, color))
            if i < len(parts) - 1:
                tokens.append((None, style, color))

    lines, cur, curw = [], [], 0.0
    for tok in tokens:
        if tok[0] is None:
            if cur:
                cur.append(tok)
            continue
        limit = width - (hang if not lines else 0)
        w = tw(d, tok[0], F(style_font(tok[1]), size))
        sp = tw(d, " ", F(style_font(tok[1]), size)) if cur else 0
        if curw + sp + w <= limit or not cur:
            if cur:
                curw += sp
            cur.append(tok)
            curw += w
        else:
            while cur and cur[-1][0] is None:
                cur.pop()
            lines.append(cur)
            cur = [tok]
            curw = w
    while cur and cur[-1][0] is None:
        cur.pop()
    if cur:
        lines.append(cur)

    for i, ln in enumerate(lines):
        x = left + (hang if i else 0)
        limit = width - (hang if i else 0)
        gaps = sum(1 for t in ln if t[0] is None)
        natural = sum(tw(d, " ", F(style_font(t[1]), size)) if t[0] is None
                      else tw(d, t[0], F(style_font(t[1]), size)) for t in ln)
        extra = (limit - natural) / gaps if (gaps and justify and i < len(lines) - 1) else 0
        for tok, style, color in ln:
            font = F(style_font(style), size)
            if tok is None:
                x += tw(d, " ", font) + extra
            else:
                if draw:
                    d.text((x, y), tok, font=font, fill=color)
                x += tw(d, tok, font)
        y += lh
    return y + space_after


# ------------------------------------------------------------------ данные
DATE_LINE = "13 ноября 2026 года, 19:00, г. Лос-Сантос"
RIGHT_META = "Спикер Сената Marcus Nomad, номер паспорта 85028"
TITLE = "ПОВЕСТКА ПЛЕНАРНОГО ЗАСЕДАНИЯ"
SUBTITLE = "ОФИЦИАЛЬНОЕ СООБЩЕНИЕ СПИКЕРА СЕНАТА"
LEAD = ("Настоящим объявляю повестку пленарного заседания Сената штата Сан-Андреас, "
        "созванного на 13 ноября 2026 года.")

ACTS = [
    ("ACT. 286",
     "о внесении изменений в Закон «Об Экстренной Медицинской Службе в штате Сан-Андреас»",
     "Сенатор Kiray Fair, номер паспорта 37492"),
    ("ACT. 287",
     "о внесении изменений в Закон «Об адвокатской деятельности и адвокатуре в штате San-Andreas»",
     "Губернатор Tommy Harlow, номер паспорта 98650"),
    ("ACT. 288",
     "о принятии нового закона и признании утратившим силу ранее действующего",
     "Губернатор Tommy Harlow, номер паспорта 98650"),
    ("ACT. 289",
     "о внесении изменений в Закон «Об адвокатской деятельности и адвокатуре в штате San-Andreas»",
     "Спикер Сената Marcus Nomad, номер паспорта 85028"),
    ("ACT. 290",
     "о внесении изменений в Конституционный закон «О Сенате штата Сан-Андреас», "
     "Конституционный закон «О нормативных правовых актах штата Сан-Андреас» и Закон "
     "«О системе ордеров штата Сан-Андреас»",
     "Спикер Сената Marcus Nomad, номер паспорта 85028 · изображение"),
    ("ACT. 291",
     "о внесении изменений в Приложение № 1 к Уголовному кодексу штата San-Andreas "
     "«О закрытых, охраняемых и особо охраняемых территориях»",
     "Спикер Сената Marcus Nomad, номер паспорта 85028"),
    ("ACT. 292",
     "о внесении изменений в Конституционный закон «О Сенате штата Сан-Андреас» и "
     "Конституционный закон «О политических партиях»",
     "Спикер Сената Marcus Nomad, номер паспорта 85028"),
    ("ACT. 293",
     "о внесении изменений в Закон «О политических партиях на территории штата San-Andreas»",
     "Спикер Сената Marcus Nomad, номер паспорта 85028"),
    ("ACT. 294",
     "о внесении изменений в Процессуальный кодекс штата Сан-Андреас "
     "(вызов прокурора адвокатом при задержании)",
     "Заместитель Генерального прокурора Gogal Killaz, номер паспорта 63823 · 17:34"),
    ("ACT. 295",
     "о внесении изменений в Уголовный кодекс штата San-Andreas",
     "Заместитель Генерального прокурора Gogal Killaz, номер паспорта 63823 · 17:34"),
    ("ACT. 296",
     "о внесении изменений в Процессуальный кодекс штата Сан-Андреас",
     "Заместитель Генерального прокурора Gogal Killaz, номер паспорта 63823 · 17:35"),
    ("ACT. 297",
     "о внесении изменений в Дорожный кодекс штата Сан-Андреас",
     "Заместитель Генерального прокурора Gogal Killaz, номер паспорта 63823 · 17:35"),
]

INITS = [
    ("Инициатива",
     "об избрании Председателя и членов Центральной избирательной комиссии штата Сан-Андреас",
     "Сенатор Merkylka Fair, номер паспорта 62277 · изображение"),
    ("Инициатива",
     "об избрании Председателя и членов Центральной избирательной комиссии штата Сан-Андреас",
     "Губернатор Tommy Harlow, номер паспорта 98650"),
    ("Инициатива",
     "о пожизненном лишении Jonny Zakonov права занимать должность сенатора и отстранении "
     "Республиканской партии «Возрождение» от участия в заседаниях Сената",
     "Губернатор Tommy Harlow, номер паспорта 98650"),
    ("Инициатива",
     "об избрании Afelia Suspect (номер паспорта 14077) на должность Вице-Спикера "
     "(заместителя Спикера) Сената",
     "Губернатор Tommy Harlow, номер паспорта 98650 · текст сообщения"),
]

REJECTED = ("Инициатива",
            "о рассмотрении вопроса о назначении специального прокурора",
            "Председатель политической партии Jonny Zakonov, номер паспорта 55454")

REJECT_NOTE = ("В повестку не включена и отклонена при её формировании: правом законодательной "
               "инициативы обладает сенатор и реализует его лично (часть 1 статьи 60 Конституции "
               "штата Сан-Андреас, часть 4 статьи 20 Конституционного закона «О нормативных "
               "правовых актах штата Сан-Андреас»).")

CLOSING = "Итоги голосования по каждому вопросу публикуются после окончания заседания."

# Официальные названия актов выделяются полужирным в предмете вопроса.
ACT_TITLES = (
    "Закон «Об Экстренной Медицинской Службе в штате Сан-Андреас»",
    "Закон «Об адвокатской деятельности и адвокатуре в штате San-Andreas»",
    "Конституционный закон «О Сенате штата Сан-Андреас»",
    "Конституционный закон «О нормативных правовых актах штата Сан-Андреас»",
    "Закон «О системе ордеров штата Сан-Андреас»",
    "Приложение № 1 к Уголовному кодексу штата San-Andreas "
    "«О закрытых, охраняемых и особо охраняемых территориях»",
    "Конституционный закон «О политических партиях»",
    "Закон «О политических партиях на территории штата San-Andreas»",
    "Процессуальный кодекс штата Сан-Андреас",
    "Уголовный кодекс штата San-Andreas",
    "Дорожный кодекс штата Сан-Андреас",
)
ACT_TITLE_PATTERN = re.compile("|".join(re.escape(x) for x in sorted(ACT_TITLES, key=len, reverse=True)))


def subject_runs(text):
    runs, pos = [], 0
    for match in ACT_TITLE_PATTERN.finditer(text):
        if match.start() > pos:
            runs.append((text[pos:match.start()], "r", INK))
        runs.append((match.group(), "b", INK))
        pos = match.end()
    if pos < len(text):
        runs.append((text[pos:], "r", INK))
    return runs


# ------------------------------------------------------------------ блоки
def heading(d, y, text, size=30, draw=True):
    font = F(FB, max(20, size - 2))
    x = BODY_L
    for ch in text:
        if draw:
            d.text((x, y), ch, font=font, fill=GREEN_D)
        x += tw(d, ch, font) + 3
    if draw:
        d.line([(BODY_L, y + int(size * 1.55)), (BODY_R, y + int(size * 1.55))],
               fill=RULE, width=3)
    return y + int(size * 2.35)


def item(d, y, i, doc, subject, meta, size, draw=True):
    hang = int(tw(d, "00. ", F(FB, size)))
    prefix = [("{}. ".format(i), "b", GREEN_D)] if i is not None else []
    runs = prefix + [(doc, "b", INK)] + subject_runs(" - " + subject)
    y = para(d, y, runs, hang=hang, size=size, lh=int(size * 1.52),
             space_after=int(size * 0.30), draw=draw)
    y = para(d, y, [(meta, "i", MUTED)], left=BODY_L + hang, width=BODY_W - hang,
             size=max(16, int(size * 0.80)), lh=int(size * 1.16),
             space_after=int(size * 0.95), justify=False, draw=draw)
    return y


def body(d, size, draw=True):
    y = 1035
    y = para(d, y, [(LEAD, "r", INK)], size=size, lh=int(size * 1.58),
             justify=False, space_after=int(size * 1.15), draw=draw)

    y = heading(d, y, "I.  ЗАКОНОПРОЕКТЫ", size, draw)
    for i, (doc, subj, meta) in enumerate(ACTS, 1):
        y = item(d, y, i, doc, subj, meta, size, draw)
    y = para(d, y, [("Время размещения ACT. 294-297 указано по исходным записям; "
                     "дата в них не приведена.", "i", MUTED)],
             size=int(size * 0.80), lh=int(size * 1.20), justify=False, draw=draw)

    y += int(size * 0.5)
    y = heading(d, y, "II.  ИНИЦИАТИВЫ", size, draw)
    for i, (doc, subj, meta) in enumerate(INITS, len(ACTS) + 1):
        y = item(d, y, i, doc, subj, meta, size, draw)

    y += int(size * 0.5)
    y = heading(d, y, "III.  НЕ ВКЛЮЧЕНО В ПОВЕСТКУ", size, draw)
    y = item(d, y, None, *REJECTED, size=size, draw=draw)
    y = para(d, y, [(REJECT_NOTE, "r", INK)], size=int(size * 0.86),
             lh=int(size * 1.36), space_after=int(size * 1.0), draw=draw)

    y = para(d, y, [(CLOSING, "r", INK)], size=size, lh=int(size * 1.58),
             justify=False, draw=draw)
    return y


def render(size):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle(FRAME, outline=GREEN, width=9)

    emblem = Image.open(os.path.join(ASSETS, "state_emblem.png")).convert("RGB")
    emblem = emblem.resize((236, 236), Image.LANCZOS)
    img.paste(emblem, (CENTER - 118, 152))

    title_mixed(d, 452, [("STATE", F(FB, 56), 10),
                         ("of", F(FI, 46), 2),
                         ("SAN ANDREAS", F(FB, 56), 10)])
    tracked(d, 556, "SENATE OF THE STATE OF SAN ANDREAS", F(FB, 25), 7, GREEN)
    d.line([(900, 628), (2100, 628)], fill=GREEN, width=3)

    tracked(d, 676, TITLE, F(FB, 52), 3, INK)
    tracked(d, 772, SUBTITLE, F(FR, 22), 2, MUTED)

    d.text((BODY_L, 858), DATE_LINE, font=F(FI, 25), fill=MUTED)
    d.text((BODY_R - tw(d, RIGHT_META, F(FI, 25)), 858), RIGHT_META, font=F(FI, 25), fill=MUTED)
    d.line([(BODY_L, 906), (BODY_R, 906)], fill=RULE, width=2)

    end = body(d, size)

    sy = max(end + int(size * 2.2), H - 1045)
    if sy > H - 925:
        raise ValueError("Основной текст не оставляет места для подписи")
    sig_name = "Marcus Nomad"
    sig_role = ["Спикер Сената", "штата Сан-Андреас"]
    f_name, f_role = F(FB, 60), F(FI, 44)
    block_w = max([tw(d, sig_name, f_name)] + [tw(d, t, f_role) for t in sig_role])
    line_l = BODY_R - block_w

    d.line([(line_l, sy), (BODY_R, sy)], fill=INK, width=4)
    d.text((line_l, sy + 42), sig_name, font=f_name, fill=INK)
    d.text((line_l, sy + 120), sig_role[0], font=f_role, fill=MUTED)
    d.text((line_l, sy + 174), sig_role[1], font=f_role, fill=MUTED)
    d.text((line_l, sy + 246), "13 ноября 2026 года", font=F(FI, 30), fill=MUTED)

    footer_y = H - 285
    seal = Image.open(os.path.join(ASSETS, "great_seal.png")).convert("RGBA")
    seal = seal.resize((708, 708), Image.LANCZOS)
    img.paste(seal, (BODY_L + 10, footer_y - 708 - 6), seal)

    d.line([(BODY_L, footer_y), (BODY_R, footer_y)], fill=RULE, width=2)
    tracked(d, footer_y + 36, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 21), 8, MUTED)
    return img, end, sy


def build(path):
    chosen = None
    for size in range(44, 20, -1):
        scratch = Image.new("RGB", (W, H), "white")
        d0 = ImageDraw.Draw(scratch)
        end = body(d0, size, draw=False)
        if end <= H - 1085:
            chosen = size
            break
    if chosen is None:
        raise ValueError("Повестка не помещается на изображении")
    print("кегль тела:", chosen)

    img, end, sy = render(chosen)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG", dpi=(300, 300))
    print("OK", path, img.size, "| низ тела:", end, "| подпись:", sy)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else OUT)
