# -*- coding: utf-8 -*-
"""Итоги пленарного заседания Сената - парадный PNG-документ.

Стиль снят с обращений Сената (зелёная рамка, печать Сената, двуязычная шапка,
рубленые лид-ины, нумерованные абзацы с висячим отступом, таблица голосований).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 3000, 4225
GREEN = (69, 137, 63)
GREEN_D = (46, 92, 42)
INK = (26, 26, 26)
MUTED = (108, 112, 116)
RULE = (203, 208, 201)
SHADE = (236, 242, 232)
RED = (150, 46, 46)
FRAME = (116, 92, 2876, 4140)
BODY_L, BODY_R = 300, 2700
BODY_W = BODY_R - BODY_L
CENTER = (BODY_L + BODY_R) // 2

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "Обращения",
                      "IAD — отзыв вето (Губернатор Harlow)", "assets")
MPL = "/usr/local/lib/python3.11/dist-packages/matplotlib/mpl-data/fonts/ttf"
FR = os.path.join(MPL, "DejaVuSerif.ttf")
FB = os.path.join(MPL, "DejaVuSerif-Bold.ttf")
FI = os.path.join(MPL, "DejaVuSerif-Italic.ttf")

_cache = {}


def F(path, size):
    k = (path, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(path, size)
    return _cache[k]


def tw(d, s, font):
    b = d.textbbox((0, 0), s, font=font)
    return b[2] - b[0]


def tracked(d, y, text, font, tracking, fill=INK, center_at=CENTER, draw=True):
    widths = [tw(d, text[i], font) for i in range(len(text))]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = center_at - total / 2
    for ch, w in zip(text, widths):
        if draw:
            d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def title_mixed(d, y, parts, draw=True):
    total = 0
    for text, font, tr in parts:
        total += sum(tw(d, ch, font) for ch in text) + tr * (len(text) - 1) + 20
    total -= 20
    x = CENTER - total / 2
    for text, font, tr in parts:
        for ch in text:
            if draw:
                d.text((x, y), ch, font=font, fill=GREEN)
            x += tw(d, ch, font) + tr
        x += 20
    return total


# ------------------------------------------------------------------ текст

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


def para(d, y, runs, width=BODY_W, left=BODY_L, hang=0, lh=None,
         size=30, justify=True, draw=True, space_after=0, first_bold_prefix=True):
    """Абзац с висячим отступом: runs — список (текст, стиль, цвет)."""
    lh = lh or int(size * 1.62)
    # единый поток слов с сохранением начертаний
    tokens = []
    for text, style, color in runs:
        parts = text.split(" ")
        for i, p in enumerate(parts):
            if p:
                tokens.append((p, style, color))
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


def style_font(style):
    return {"r": FR, "b": FB, "i": FI}[style]


def heading(d, y, text, size=30, draw=True):
    font = F(FB, size)
    tracked(d, y, text, font, 3, GREEN_D, center_at=BODY_L + tw(d, text, font) / 2 + 5 * len(text) / 2,
            draw=draw)
    if draw:
        d.line([(BODY_L, y + int(size * 1.9)), (BODY_R, y + int(size * 1.9))], fill=RULE, width=3)
    return y + int(size * 2.9)


# ------------------------------------------------------------------ таблица

# ------------------------------------------------------------------ контент

def essence(d, y, size, draw=True):
    """Одна строка-суть вместо итогов голосования."""
    h = 118
    text = "7 ЗАКОНОПРОЕКТОВ ПРИНЯТЫ; ИНИЦИАТИВА О ЦИК И ACT. 283 НЕ ПРИНЯТЫ"
    fs = 40
    while fs > 22 and tw(d, text, F(FB, fs)) + 3 * (len(text) - 1) > BODY_W - 60:
        fs -= 1
    if draw:
        d.line([(BODY_L, y), (BODY_R, y)], fill=GREEN, width=3)
        d.line([(BODY_L, y + h), (BODY_R, y + h)], fill=RULE, width=2)
        tracked(d, y + (h - fs) // 2 - 6, text, F(FB, fs), 3, GREEN_D, draw=draw)
    return y + h


def numbered(d, y, items, size, draw=True):
    lh = int(size * 1.62)
    for runs in items:
        y = para(d, y, runs, hang=92, size=size, lh=lh,
                 space_after=int(size * 0.50), draw=draw)
    return y


def section_common(d, y, size, draw=True):
    items = [
        [("1.1.", "b", GREEN_D),
         (" Заседание открыто и признано правомочным: присутствовало не менее половины "
          "действующих сенаторов (часть 1 статьи 9 Конституционного закона «О Сенате "
          "штата Сан-Андреас»).", "r", INK)],
        [("1.2.", "b", GREEN_D),
         (" Общее число действующих сенаторов - 14. Для принятия решения большинством "
          "голосов требовалось 8 голосов, то есть число, превышающее половину общего "
          "числа действующих сенаторов (часть 5 статьи 80 Конституции штата "
          "Сан-Андреас).", "r", INK)],
        [("1.3.", "b", GREEN_D),
         (" Заседание проведено под председательством Председателя (Спикера) Сената "
          "штата Сан-Андреас Marcus Nomad.", "r", INK)],
    ]
    return numbered(d, y, items, size, draw)


def section_decisions(d, y, size, draw=True):
    items = [
        [("2.1. Приняты", "b", GREEN_D),
         (" законопроекты ACT. 277, ACT. 278, ACT. 279, ACT. 280, ACT. 282, ACT. 284 и "
          "ACT. 285 - всего 7 законопроектов.", "r", INK)],
        [("2.2. Не принята", "b", RED),
         (" инициатива об избрании председателя и членов Центральной избирательной "
          "комиссии штата Сан-Андреас: 7 голосов «за», 6 «против», 0 «воздержался» "
          "при необходимых 8.", "r", INK)],
        [("2.3. Не принят", "b", RED),
         (" законопроект ACT. 283: 7 голосов «за», 5 «против», 1 «воздержался» при "
          "необходимых 8.", "r", INK)],
        [("2.4. Отозван", "b", MUTED),
         (" законопроект ACT. 281 - инициатором, до голосования.", "r", INK)],
    ]
    return numbered(d, y, items, size, draw)


def section_send(d, y, size, draw=True):
    items = [
        [("3.1.", "b", GREEN_D),
         (" Принятые законы в течение двух дней направляются в Федеральный Суд штата "
          "Сан-Андреас, а после получения его одобрения - Губернатору штата "
          "Сан-Андреас для подписания и обнародования (часть 3 статьи 80 Конституции "
          "штата Сан-Андреас).", "r", INK)],
        [("3.2.", "b", GREEN_D),
         (" Направление принятых законов обеспечивает Председатель (Спикер) Сената "
          "штата Сан-Андреас.", "r", INK)],
        [("3.3.", "b", GREEN_D),
         (" Настоящие итоги не заменяют протокол заседания: при расхождении применяются "
          "сведения протокола.", "r", INK)],
    ]
    return numbered(d, y, items, size, draw)


def body(d, size, draw=True):
    y = 1035
    y = para(d, y, [("Настоящим объявляю итоги пленарного заседания Сената штата "
                     "Сан-Андреас, состоявшегося 9 ноября 2026 года в городе "
                     "Лос-Сантос.", "r", INK)],
             size=size, lh=int(size * 1.62), space_after=int(size * 1.35), draw=draw)

    y = essence(d, y, size, draw)
    y += int(size * 1.05)

    y = heading(d, y, "I.  ОБЩИЕ СВЕДЕНИЯ", size, draw)
    y = section_common(d, y, size, draw)

    y = heading(d, y, "II.  РЕШЕНИЯ ЗАСЕДАНИЯ", size, draw)
    y = section_decisions(d, y, size, draw)

    y = heading(d, y, "III.  НАПРАВЛЕНИЕ ПРИНЯТЫХ ЗАКОНОВ", size, draw)
    y = section_send(d, y, size, draw)
    return y


def render(size):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle(FRAME, outline=GREEN, width=9)

    em = Image.open(os.path.join(ASSETS, "state_emblem.png")).convert("RGB")
    em = em.resize((260, 260), Image.LANCZOS)
    img.paste(em, (CENTER - 130, 150))

    title_mixed(d, 455, [("STATE", F(FB, 58), 10),
                         ("of", F(FI, 50), 2),
                         ("SAN ANDREAS", F(FB, 58), 10)])
    tracked(d, 560, "SENATE OF THE STATE OF SAN ANDREAS", F(FB, 26), 7, GREEN)
    d.line([(840, 640), (2160, 640)], fill=GREEN, width=3)

    tracked(d, 690, "ИТОГИ ПЛЕНАРНОГО ЗАСЕДАНИЯ", F(FB, 58), 4, INK)
    tracked(d, 790, "ОФИЦИАЛЬНОЕ СООБЩЕНИЕ ПРЕДСЕДАТЕЛЯ (СПИКЕРА) СЕНАТА", F(FR, 24), 2, MUTED)

    # метаданные
    d.text((BODY_L, 875), "9 ноября 2026 года, г. Лос-Сантос", font=F(FI, 26), fill=MUTED)
    right = "Спикер Сената Marcus Nomad, UID-85028"
    d.text((BODY_R - tw(d, right, F(FI, 26)), 875), right, font=F(FI, 26), fill=MUTED)
    d.line([(BODY_L, 925), (BODY_R, 925)], fill=RULE, width=2)

    end = body(d, size)

    # подпись
    sy = max(end + int(size * 1.1), 3380)
    d.line([(1560, sy + 150), (2660, sy + 150)], fill=INK, width=4)
    d.text((1590, sy + 172), "Marcus Nomad", font=F(FB, 34), fill=INK)
    d.text((1590, sy + 222), "Председатель (Спикер) Сената", font=F(FI, 26), fill=MUTED)
    d.text((1590, sy + 264), "штата Сан-Андреас", font=F(FI, 26), fill=MUTED)

    seal = Image.open(os.path.join(ASSETS, "great_seal.png")).convert("RGBA")
    seal = seal.resize((330, 330), Image.LANCZOS)
    img.paste(seal, (BODY_L + 45, sy + 8), seal)

    d.line([(BODY_L, 3970), (BODY_R, 3970)], fill=RULE, width=2)
    tracked(d, 4000, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 22), 8, MUTED)
    return img, end, sy


def build(path):
    chosen = None
    for size in range(40, 21, -1):
        scratch = Image.new("RGB", (W, H), "white")
        d0 = ImageDraw.Draw(scratch)
        end = body(d0, size, draw=False)
        if end <= 3150:
            chosen = size
            break
    chosen = chosen or 22
    print("кегль тела:", chosen)

    img, end, sy = render(chosen)
    img.save(path, "PNG", dpi=(300, 300))
    print("OK", path, img.size, "| низ тела:", end, "| подпись:", sy)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "senate_results.png")
