# -*- coding: utf-8 -*-
"""Уведомление Председателя Сената об оставлении инициативы без рассмотрения (PNG).

Две страницы A4 300 dpi в той же парадной вёрстке, что и протокол 09.11.2026.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

from make_senat_protocol_png import (  # noqa: E402
    ASSETS, BODY_L, BODY_R, BODY_W, CENTER, F, FB, FI, FR, GREEN, GREEN_D, INK, MUTED,
    RULE, SHADE, W, para, title_mixed, tracked, tw, wrap,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "Сенат",
                   "Уведомление об оставлении инициативы (12.11.2026)")

SIZE = 32
LH = 1.62

# ------------------------------------------------------------------ данные
ADDRESS = [
    ("Кому:", "Председателю политической партии, сенатору от Республиканской партии "
              "«Возрождение» Merkylka Fair (ID: 62277)"),
    ("От:", "Председателя Сената штата Сан-Андреас Marcus Nomad (ID: 85028)"),
    ("Дата:", "12.11.2026"),
]

TITLE = "РЕЗОЛЮЦИЯ ОБ ОСТАВЛЕНИИ ЗАКОНОДАТЕЛЬНОЙ ИНИЦИАТИВЫ БЕЗ РАССМОТРЕНИЯ"

INTRO = ("Рассмотрев в порядке ведения вопросов внутреннего распорядка Сената штата "
         "Сан-Андреас (пункт «в» части 4 статьи 3 Конституционного закона «О Сенате штата "
         "Сан-Андреас») обращение (законодательную инициативу), размещённое 11.11.2026 в "
         "09:23 Председателем политической партии с указанием внутри текста на "
         "представление инициативы сенатором от Республиканской партии «Возрождение» "
         "Merkylka Fair (ID: 62277),")

ITEMS = [
    ("1.", "Согласно части 1 статьи 60 Конституции штата Сан-Андреас, перечень субъектов "
           "права законодательной инициативы является исчерпывающим:",
     "Право законодательной инициативы принадлежит Губернатору штата Сан-Андреас, "
     "Вице-губернатору штата Сан-Андреас, Генеральному прокурору штата Сан-Андреас, "
     "Спикеру Сената штата Сан-Андреас и его заместителю, сенаторам штата Сан-Андреас и "
     "Верховному Суду штата Сан-Андреас.",
     "Председатель политической партии в данный перечень не входит, а политическая партия "
     "участвует в законотворчестве исключительно путём выдвижения своего представителя в "
     "Сенат (часть 9 статьи 5 Конституционного закона штата Сан-Андреас «О политических "
     "партиях»)."),
    ("2.", "В соответствии с частью 4 статьи 2 Конституционного закона «О нормативных "
           "правовых актах штата Сан-Андреас», законодательной инициативой признаётся "
           "официальное внесение законопроекта в законодательный орган именно субъектом "
           "права законодательной инициативы, установленным Конституцией. Частью 4 статьи 20 "
           "указанного Закона прямо закреплено:",
     "Сенаторы штата Сан-Андреас реализуют право законодательной инициативы лично.",
     None),
    ("3.", "Внесение инициативы в раздел предложений Сената лицом, не обладающим правом "
           "законодательной инициативы (председателем политической партии), нарушает "
           "установленный порядок реализации права законодательной инициативы. Указание "
           "внутри текста заявления от имени сенатора Merkylka Fair при фактической подаче "
           "документа ненадлежащим лицом не устраняет данное нарушение.", None, None),
]

BASIS = ("На основании изложенного, руководствуясь частью 1 статьи 60 Конституции штата "
         "Сан-Андреас, частью 4 статьи 20 Конституционного закона «О нормативных правовых "
         "актах штата Сан-Андреас», пунктами «в» и «ж» части 4 статьи 3 Конституционного "
         "закона «О Сенате штата Сан-Андреас»,")

DECISIONS = [
    ("1.", "Оставить законодательную инициативу, опубликованную 11.11.2026 в 09:23 "
           "Председателем политической партии, без рассмотрения и не включать её в повестку "
           "пленарного заседания Сената штата Сан-Андреас, назначенного на 13.11.2026 в "
           "19:00."),
    ("2.", "Разъяснить сенатору от Республиканской партии «Возрождение» Merkylka Fair "
           "(ID: 62277) право самостоятельно и лично внести указанную законодательную "
           "инициативу от своего имени в специальный раздел предложений Сената штата "
           "Сан-Андреас в соответствии с частью 1 статьи 6 Конституционного закона «О Сенате "
           "штата Сан-Андреас» и частью 4 статьи 20 Конституционного закона «О нормативных "
           "правовых актах штата Сан-Андреас»."),
]


# ------------------------------------------------------------------ блоки
def frame(d, draw=True):
    if draw:
        d.rectangle([116, 92, 2876, 4140], outline=GREEN, width=9)


def center_head(d, y, text, size=33, draw=True, space_before=10):
    y += space_before
    font = F(FB, size)
    tracked(d, y, text, font, 5, GREEN_D, draw=draw, left=True)
    if draw:
        d.line([(BODY_L, y + int(size * 1.75)), (BODY_R, y + int(size * 1.75))],
               fill=RULE, width=3)
    return y + int(size * 2.55)


def quote(d, y, text, size=None, draw=True, space=18):
    size = size or SIZE
    bar = BODY_L + 76
    y2 = para(d, y, [(text, "i", (74, 80, 74))], left=bar + 34,
              width=BODY_W - 150, size=size, draw=draw, space_after=0)
    if draw:
        d.line([(bar, y + 8), (bar, y2 - 24)], fill=GREEN, width=6)
    return y2 + space


def address_box(d, y, size=None, draw=True):
    size = (size or SIZE) - 2
    font = F(FR, size)
    lh = int(size * LH)
    pad = 26
    heights = []
    for _, txt in ADDRESS:
        heights.append(len(wrap(d, txt, font, BODY_W - 260)) * lh)
    box_h = sum(heights) + pad * 2 + 6 * (len(ADDRESS) - 1)
    if draw:
        d.rectangle([BODY_L, y, BODY_R, y + box_h], fill=(246, 250, 244), outline=RULE,
                    width=2)
        d.rectangle([BODY_L, y, BODY_L + 9, y + box_h], fill=GREEN)
    yy = y + pad
    for (label, txt), h in zip(ADDRESS, heights):
        lines = wrap(d, txt, font, BODY_W - 260)
        if draw:
            d.text((BODY_L + 34, yy + 2), label, font=F(FB, size), fill=GREEN_D)
            for i, ln in enumerate(lines):
                d.text((BODY_L + 236, yy + i * lh), ln, font=font, fill=INK)
        yy += h + 6
    return y + box_h + 34


def title_band(d, y, text, size=None, draw=True):
    size = size or 30
    font = F(FB, size)
    lines = wrap(d, text, font, BODY_W - 140)
    lh = int(size * 1.5)
    h = len(lines) * lh + 34
    if draw:
        d.rectangle([BODY_L, y, BODY_R, y + h], fill=SHADE)
        d.line([(BODY_L, y), (BODY_R, y)], fill=GREEN_D, width=3)
        d.line([(BODY_L, y + h), (BODY_R, y + h)], fill=GREEN_D, width=3)
        for i, ln in enumerate(lines):
            w = sum(tw(d, ch, font) + 4 for ch in ln) - 4
            x = CENTER - w / 2
            for ch in ln:
                d.text((x, y + 17 + i * lh), ch, font=font, fill=GREEN_D)
                x += tw(d, ch, font) + 4
    return y + h + 30


def item(d, y, num, text, quote_text=None, tail=None, size=None, draw=True, after=None):
    size = size or SIZE
    lh = int(size * LH)
    hang = 76
    y = para(d, y, [(num + " ", "b", GREEN_D), (text, "r", INK)], hang=hang, size=size,
             draw=draw, space_after=0)
    if quote_text:
        y = quote(d, y + 6, quote_text, size=size - 1, draw=draw, space=14)
    if tail:
        y = para(d, y, [(tail, "r", INK)], left=BODY_L + hang, width=BODY_W - hang,
                 size=size, draw=draw, space_after=0)
    return y + (after if after is not None else int(size * 0.68))


def top_band(d, draw=True, page_no=2, total=2):
    frame(d, draw)
    tracked(d, 168, "ОФИЦИАЛЬНОЕ УВЕДОМЛЕНИЕ ПРЕДСЕДАТЕЛЯ СЕНАТА  ·  12 НОЯБРЯ 2026 ГОДА",
            F(FB, 25), 3, GREEN, draw=draw)
    if draw:
        d.line([(BODY_L, 228), (BODY_R, 228)], fill=GREEN, width=3)
        right = f"стр. {page_no} из {total}"
        d.text((BODY_R - tw(d, right, F(FI, 23)), 250), right, font=F(FI, 23), fill=MUTED)
    return 312


def body(d, draw=True):
    frame(d, draw)
    em = Image.open(os.path.join(ASSETS, "state_emblem.png")).convert("RGB")
    em = em.resize((228, 228), Image.LANCZOS)
    if draw:
        d._image.paste(em, (CENTER - 114, 150))
    title_mixed(d, 422, [("STATE", F(FB, 50), 9), ("of", F(FI, 42), 2),
                         ("SAN ANDREAS", F(FB, 50), 9)], draw=draw)
    tracked(d, 514, "SENATE OF THE STATE OF SAN ANDREAS", F(FB, 24), 7, GREEN, draw=draw)
    if draw:
        d.line([(900, 584), (2100, 584)], fill=GREEN, width=3)

    tracked(d, 630, "ОФИЦИАЛЬНОЕ УВЕДОМЛЕНИЕ", F(FB, 46), 6, INK, draw=draw)
    tracked(d, 720, "ПРЕДСЕДАТЕЛЯ СЕНАТА ШТАТА САН-АНДРЕАС", F(FR, 26), 3, MUTED,
            draw=draw)

    y = 812
    y = address_box(d, y, draw=draw)
    y = title_band(d, y, TITLE, size=30, draw=draw)
    y = para(d, y, [(INTRO, "r", INK)], size=SIZE, draw=draw,
             space_after=int(SIZE * 0.7))
    y = center_head(d, y, "УСТАНОВЛЕНО:", size=32, draw=draw, space_before=22)
    for num, text, q, tail in ITEMS:
        y = item(d, y, num, text, q, tail, draw=draw, after=int(SIZE * 0.60))

    y += int(SIZE * 0.30)
    y = para(d, y, [(BASIS, "r", INK)], size=SIZE, draw=draw,
             space_after=int(SIZE * 0.70))
    y = center_head(d, y, "РЕШИЛ:", size=32, draw=draw, space_before=0)
    for num, text in DECISIONS:
        y = para(d, y, [(num + " ", "b", GREEN_D), (text, "r", INK)], hang=76,
                 size=SIZE, draw=draw, space_after=int(SIZE * 0.70))
    return y


def signature(d, sy, draw=True):
    d.line([(1820, sy + 150), (2660, sy + 150)], fill=INK, width=4)
    d.text((1850, sy + 172), "Marcus Nomad", font=F(FB, 34), fill=INK)
    d.text((1850, sy + 222), "Председатель Сената", font=F(FI, 26), fill=MUTED)
    d.text((1850, sy + 264), "штата Сан-Андреас", font=F(FI, 26), fill=MUTED)
    d.text((1850, sy + 314), "12 ноября 2026 года", font=F(FI, 24), fill=MUTED)

    seal = Image.open(os.path.join(ASSETS, "great_seal.png")).convert("RGBA")
    seal = seal.resize((430, 430), Image.LANCZOS)
    r, g, b, a = seal.split()
    r = r.point(lambda v: int(max(0, min(255, (v - 112) * 1.42 + 92))))
    g = g.point(lambda v: int(max(0, min(255, (v - 100) * 1.42 + 80))))
    b = b.point(lambda v: int(max(0, min(255, (v - 74) * 1.42 + 54))))
    seal = Image.merge("RGBA", (r, g, b, a))
    d._image.paste(seal, (1074, sy - 52), seal)

    d.line([(BODY_L, 3966), (BODY_R, 3966)], fill=RULE, width=2)
    tracked(d, 3996, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 22), 8, MUTED)
    return sy + 400


def page(d, draw=True):
    y = body(d, draw)
    sy = max(y + 120, 3180)
    if sy + 400 > 3900:
        sy = 3900 - 400
    if draw:
        signature(d, sy, draw)
    return sy + 400 if draw else y


def page1(d, draw=True):
    return page(d, draw)


def measure(builder, **kw):
    img = Image.new("RGB", (W, 4225), "white")
    d = ImageDraw.Draw(img)
    d._image = img
    return builder(d, draw=False, **kw)


def render(builder, path, **kw):
    img = Image.new("RGB", (W, 4225), "white")
    d = ImageDraw.Draw(img)
    d._image = img
    builder(d, draw=True, **kw)
    img.save(path, "PNG", dpi=(300, 300))
    print("OK", path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for sz in range(40, 23, -1):
        globals()["SIZE"] = sz
        e = measure(page)
        print(f"кегль {sz}: текст до {e}")
        if e <= 3300:
            break
    print("итоговый кегль:", SIZE)

    render(page, os.path.join(
        OUT, "Уведомление об оставлении инициативы без рассмотрения.png"))
