# -*- coding: utf-8 -*-
"""Постановление Губернатора в визуальном стиле документов Tommy Harlow.

Стиль снят с образца 32D0mMr.png: зелёная рамка, эмблема, двуязычная шапка
(STATE of SAN ANDREAS / OFFICE OF THE GOVERNOR / EXECUTIVE ORDER NO. XXXX),
рубленые жирные лид-ины, нумерованные пункты, блок «В УДОСТОВЕРЕНИЕ ЧЕГО»,
золотая Великая Печать, факсимиле подписи, Капитолий внизу.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 3000, 4225
GREEN = (69, 137, 63)
TEAL = (87, 137, 127)
INK = (20, 20, 20)
FRAME = (116, 92, 2876, 4140)
BODY_L, BODY_R = 455, 2505
BODY_W = BODY_R - BODY_L

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


def tracked(d, y, text, font, tracking, fill=INK, center_at=1500):
    widths = [tw(d, ch, font) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = center_at - total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking


def title_mixed(d, y, parts, center_at):
    total = 0
    for text, font, tr in parts:
        total += sum(tw(d, ch, font) for ch in text) + tr * (len(text) - 1) + 14
    total -= 14
    x = center_at - total / 2
    for text, font, tr in parts:
        for ch in text:
            d.text((x, y), ch, font=font, fill=GREEN)
            x += tw(d, ch, font) + tr
        x += 14


# ------------------------------------------------------------------ набор

def runs_to_tokens(runs):
    tokens = []
    for text, font, color in runs:
        parts = text.split(" ")
        for i, p in enumerate(parts):
            if p:
                tokens.append((p, font, color))
            if i < len(parts) - 1:
                tokens.append((None, font, color))
    return tokens


def tok_width(d, tok):
    return tw(d, " ", tok[1]) if tok[0] is None else tw(d, tok[0], tok[1])


def layout_lines(d, tokens, width, first_indent=0):
    lines, cur = [], []
    for tok in tokens:
        if tok[0] is None:
            if cur:
                cur.append(tok)
            continue
        trial = cur + [tok]
        limit = width - (first_indent if not lines else 0)
        if sum(tok_width(d, t) for t in trial) <= limit or not cur:
            cur.append(tok)
        else:
            while cur and cur[-1][0] is None:
                cur.pop()
            lines.append(cur)
            cur = [tok]
    while cur and cur[-1][0] is None:
        cur.pop()
    if cur:
        lines.append(cur)
    return lines


def draw_para(d, y, runs, width, lh, left=BODY_L, align="justify",
              space_after=0, first_indent=0, draw=True):
    lines = layout_lines(d, runs_to_tokens(runs), width, first_indent)
    for i, ln in enumerate(lines):
        last = (i == len(lines) - 1)
        x = left + (first_indent if i == 0 else 0)
        limit = width - (first_indent if i == 0 else 0)
        gaps = sum(1 for t in ln if t[0] is None)
        natural = sum(tok_width(d, t) for t in ln)
        extra = (limit - natural) / gaps if (gaps and align == "justify" and not last) else 0
        for tok, font, col in ln:
            if not draw:
                continue
            if tok is None:
                x += tw(d, " ", font) + extra
            else:
                d.text((x, y), tok, font=font, fill=col)
                x += tw(d, tok, font)
        y += lh
    return y + space_after


def P(text, size, bold=False, italic=False):
    font = F(FB if bold else (FI if italic else FR), size)
    return (text, font, INK)


def attestation(d, y, size, tracking=3):
    """Блок «В УДОСТОВЕРЕНИЕ ЧЕГО» — по левому краю, без выключки."""
    lh = 46
    right = 2609
    lead = "В УДОСТОВЕРЕНИЕ ЧЕГО,"
    tail = (" я приложил здесь свою руку и приказал прикрепить Великую Печать "
            "штата Сан-Андреас в Капитолии штата в этот «___» день ноября "
            "2026 года.")
    bold, reg = F(FB, size), F(FR, size)
    x = 1500
    for ch in lead:
        d.text((x, y), ch, font=bold, fill=INK)
        x += tw(d, ch, bold) + tracking

    space = tw(d, " ", reg)
    x += space
    tokens = [t for t in runs_to_tokens([(tail, reg, INK)])]
    first = True
    for tok in tokens:
        if tok[0] is None:
            if not first:
                x += space
            continue
        w = tok_width(d, tok)
        if x + w > right and x > 1500:
            y, x = y + lh, 1500
            first = True
            continue
        d.text((x, y), tok[0], font=reg, fill=INK)
        x += w
        first = False
    return y + lh


# --------------------------------------------------------------- контент

PREAMBLE = [
    P("ПРИНИМАЯ ВО ВНИМАНИЕ", 1, bold=True),
    P(" результаты выборов Губернатора штата Сан-Андреас, моё вступление в "
      "указанную должность, необходимость обеспечения верховенства Конституции "
      "штата Сан-Андреас и законности актов Губернатора, а также устранение "
      "правовой неопределённости, возникшей в связи с изданием Указа Губернатора "
      "штата Сан-Андреас № 81 от 30.10.2026,", 1),
]

SECOND = [
    P("Я, Tommy Harlow,", 1, bold=True),
    P(" Губернатор штата Сан-Андреас, руководствуясь частью 1 статьи 80, частью 3 "
      "статьи 80, частью 4 статьи 80 и частью 1 статьи 83 Конституции штата "
      "Сан-Андреас, частью 2 Поправки 8 к Конституции штата Сан-Андреас, пунктом "
      "«в» части 2 статьи 10 Конституционного закона «О Правительстве штата "
      "Сан-Андреас», частями 3 и 4 статьи 13 Конституционного закона "
      "«О нормативных правовых актах штата Сан-Андреас» и иными нормативными "
      "правовыми актами штата Сан-Андреас,", 1),
]

POINTS = [
    [P("1.", 1, bold=True),
     P(" Признать утратившим силу Указ Губернатора штата Сан-Андреас № 81 "
       "«Об отклонении закона (вето)» от 30.10.2026 — как не содержащий "
       "мотивированного обоснования, обязательного в силу части 1 статьи 83 "
       "Конституции штата Сан-Андреас, и не позволяющий достоверно установить "
       "отклоняемый акт.", 1)],
    [P("2.", 1, bold=True),
     P(" Подписать и обнародовать Закон штата Сан-Андреас «О внесении изменений "
       "в Процессуальный кодекс штата Сан-Андреас» (ACT. 244), принятый Сенатом "
       "штата Сан-Андреас 28.10.2026 и одобренный Федеральным Судом штата "
       "Сан-Андреас (акт от ", 1),
     P("«___» __________ 2026 года № ____", 1, italic=True),
     P(").", 1)],
    [P("3.", 1, bold=True),
     P(" Установить, что Закон, указанный в пункте 2 настоящего Указа, "
       "вступает в силу со дня его подписания и обнародования — в порядке, "
       "предусмотренном частью 2 Поправки 8 к Конституции штата Сан-Андреас.", 1)],
    [P("4.", 1, bold=True),
     P(" Установить, что настоящий Указ не является повторным "
       "направлением Закона, указанного в пункте 2, и не возобновляет течение "
       "срока, предусмотренного частью 4 статьи 80 Конституции штата "
       "Сан-Андреас.", 1)],
    [P("5.", 1, bold=True),
     P(" Администрации Губернатора штата Сан-Андреас обеспечить включение Закона, "
       "указанного в пункте 2, в Законодательную базу штата Сан-Андреас и его "
       "официальное опубликование в порядке, установленном статьёй 16 "
       "Конституционного закона «О нормативных правовых актах штата "
       "Сан-Андреас».", 1)],
]

ATTEST = [
    P("В УДОСТОВЕРЕНИЕ ЧЕГО,", 1, bold=True),
    P(" я приложил здесь свою руку и приказал прикрепить Великую Печать штата "
      "Сан-Андреас в Капитолии штата в этот «___» день ноября 2026 года.", 1),
]


def scale(runs, size):
    """Подставляет реальный кегль вместо заглушки 1."""
    out = []
    for text, font, col in runs:
        if "Bold" in font.path:
            fnt = F(FB, size)
        elif "Italic" in font.path:
            fnt = F(FI, size)
        else:
            fnt = F(FR, size)
        out.append((text, fnt, col))
    return out


def body(d, size, draw=True):
    """Тело документа. Возвращает y после последнего абзаца."""
    lh = int(size * 1.5)
    y = 972
    y = draw_para(d, y, scale(PREAMBLE, size), BODY_W, lh,
                  space_after=int(size * 0.62), draw=draw)
    y = draw_para(d, y, scale(SECOND, size), BODY_W, lh,
                  space_after=int(size * 0.92), draw=draw)

    if draw:
        d.text((BODY_L, y), "НАСТОЯЩИМ УКАЗЫВАЮ:",
               font=F(FB, size), fill=INK)
    y += int(size * 1.42)

    for pts in POINTS:
        y = draw_para(d, y, scale(pts, size), BODY_W, lh,
                      space_after=int(size * 0.60), draw=draw)
    return y


def force_block(d, y, size, draw=True):
    runs = [
        P("НАСТОЯЩИЙ УКАЗ ВСТУПАЕТ В СИЛУ", 1, bold=True),
        P(" с момента публикации ", 1),
        P("настоящего Указа", 1, italic=True),
        P(" на официальном портале штата Сан-Андреас.", 1),
    ]
    lh = int(size * 1.44)
    return draw_para(d, y, scale(runs, size), BODY_W, lh, draw=draw)


def render(size):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.rectangle(FRAME, outline=GREEN, width=8)

    em = Image.open(os.path.join(ASSETS, "state_emblem.png")).convert("RGB")
    img.paste(em, (1500 - em.width // 2, 164))

    title_mixed(d, 588, [("STATE", F(FB, 62), 10),
                         ("of", F(FI, 54), 2),
                         ("SAN ANDREAS", F(FB, 62), 10)], 1500)
    tracked(d, 716, "OFFICE OF THE GOVERNOR", F(FB, 34), 8, GREEN)
    tracked(d, 846, "EXECUTIVE ORDER NO. 0011", F(FB, 38), 4, INK)

    end = body(d, size)
    end = force_block(d, max(end + int(size * 0.45), end), int(size * 0.94))
    return img, end


def build(path):
    chosen = None
    for size in range(44, 25, -1):
        scratch = Image.new("RGB", (W, H), "white")
        d0 = ImageDraw.Draw(scratch)
        end = body(d0, size, draw=False)
        end = force_block(d0, end + int(size * 0.45), int(size * 0.94), draw=False)
        # нижняя граница тела + место под блок печати и подписи
        if end <= 2930:
            chosen = size
            break
    if chosen is None:
        chosen = 26
    print("кегль тела:", chosen)

    img, end = render(chosen)
    d = ImageDraw.Draw(img)

    # золотая печать
    seal = Image.open(os.path.join(ASSETS, "great_seal.png")).convert("RGBA")
    seal = seal.resize((795, 795), Image.LANCZOS)
    img.paste(seal, (380, 3013), seal)

    # блок удостоверения (правая колонка)
    attestation(d, 3043, 30)

    # подпись
    sg = Image.open(os.path.join(ASSETS, "signature.png")).convert("RGBA")
    sg = sg.resize((640, int(640 * sg.height / sg.width)), Image.LANCZOS)
    img.paste(sg, (1671, 3296), sg)
    d.line([(1500, 3567), (2600, 3567)], fill=INK, width=5)
    cap = F(FI, 32)
    d.text((1543, 3588), "Tommy Harlow, Governor of the", font=cap, fill=INK)
    d.text((1543, 3626), "State of San Andreas", font=cap, fill=INK)

    # Капитолий
    cp = Image.open(os.path.join(ASSETS, "capitol.png")).convert("RGBA")
    cp = cp.resize((720, int(720 * cp.height / cp.width)), Image.LANCZOS)
    img.paste(cp, (1150, 3690), cp)
    tracked(d, 4069, "STATE OF SAN ANDREAS", F(FR, 30), 9, TEAL)

    img.save(path, "PNG", dpi=(300, 300))
    print("OK", path, img.size, "| низ тела:", end)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "order.png")
