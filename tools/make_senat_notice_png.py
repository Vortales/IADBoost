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
                   "Уведомление о перенесении рассмотрения (12.11.2026)")

SIZE = 32
LH = 1.74

# ------------------------------------------------------------------ данные
ADDRESS = [
    ("Кому:", "Председателю политической партии, сенатору от Республиканской партии "
              "«Возрождение» Merkylka Fair, номер паспорта 62277"),
    ("От:", "Председателя Сената штата Сан-Андреас Marcus Nomad, номер паспорта 85028"),
    ("Дата:", "12.11.2026"),
]

TITLE = ("РЕЗОЛЮЦИЯ О ПЕРЕНЕСЕНИИ РАССМОТРЕНИЯ ИНИЦИАТИВЫ "
         "НА СЛЕДУЮЩЕЕ ЗАСЕДАНИЕ")

INTRO = ("Рассмотрев в порядке ведения вопросов внутреннего распорядка Сената штата "
         "Сан-Андреас (пункт «в» части 4 статьи 3 Конституционного закона «О Сенате штата "
         "Сан-Андреас») обращение (законодательную инициативу), размещённое 11.11.2026 в "
         "09:23 Председателем политической партии с указанием внутри текста на "
         "представление инициативы сенатором от Республиканской партии «Возрождение» "
         "Merkylka Fair, номер паспорта 62277,")

ITEMS = [
    ("1.", "Частью 1 статьи 60 Конституции штата Сан-Андреас установлен перечень "
           "субъектов права законодательной инициативы, и председатель политической партии "
           "в него не входит:",
     "Право законодательной инициативы принадлежит Губернатору штата Сан-Андреас, "
     "Вице-губернатору штата Сан-Андреас, Генеральному прокурору штата Сан-Андреас, "
     "Спикеру Сената штата Сан-Андреас и его заместителю, сенаторам штата Сан-Андреас и "
     "Верховному Суду штата Сан-Андреас.",
     "Политическая партия участвует в законотворчестве путём выдвижения своего "
     "представителя в Сенат (часть 9 статьи 5 Конституционного закона штата Сан-Андреас "
     "«О политических партиях»), однако правом законодательной инициативы наделён сам "
     "сенатор, а не председатель партии."),
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
    ("4.", "Вопрос, изложенный в указанной инициативе, подлежит рассмотрению Сенатом штата "
           "Сан-Андреас на следующем пленарном заседании. Председатель Сената ведает "
           "вопросами внутреннего распорядка Сената (пункт «в» части 4 статьи 3 "
           "Конституционного закона «О Сенате штата Сан-Андреас») и не вправе исключить "
           "вопрос из рассмотрения Сенатом по существу.", None, None),
]

BASIS = ("На основании изложенного, руководствуясь частью 1 статьи 60 Конституции штата "
         "Сан-Андреас, частью 4 статьи 20 Конституционного закона «О нормативных правовых "
         "актах штата Сан-Андреас», пунктами «в» и «ж» части 4 статьи 3 Конституционного "
         "закона «О Сенате штата Сан-Андреас»,")

DECISIONS = [
    ("1.", "Оставить законодательную инициативу, опубликованную 11.11.2026 в 09:23 "
           "Председателем политической партии, без рассмотрения на пленарном заседании "
           "Сената штата Сан-Андреас, назначенном на 13.11.2026 в 19:00, и не включать её в "
           "повестку дня указанного заседания."),
    ("2.", "Включить вопрос, изложенный в указанной инициативе, в проект повестки дня "
           "следующего пленарного заседания Сената штата Сан-Андреас. Инициатива подлежит "
           "рассмотрению на следующем пленарном заседании, если иное не предусмотрено "
           "пунктом 5 настоящей резолюции."),
    ("3.", "Разъяснить сенатору от Республиканской партии «Возрождение» Merkylka Fair"
           ", номер паспорта 62277, право самостоятельно и лично внести указанную законодательную "
           "инициативу от своего имени в специальный раздел предложений Сената штата "
           "Сан-Андреас в соответствии с частью 1 статьи 6 Конституционного закона «О Сенате "
           "штата Сан-Андреас» и частью 4 статьи 20 Конституционного закона «О нормативных "
           "правовых актах штата Сан-Андреас»."),
    ("4.", "Разъяснить, что повторное внесение указанной инициативы сенатором Merkylka Fair"
           ", номер паспорта 62277, лично, в том числе в ходе пленарного заседания, назначенного на "
           "13.11.2026 в 19:00, само по себе не влечёт её рассмотрения в этом заседании и не "
           "создаёт обязанности председательствующего ставить её на голосование, за "
           "исключением случаев, предусмотренных пунктом 5 настоящей резолюции."),
    ("5.", "Разъяснить, что из пункта 4 настоящей резолюции установлены следующие "
           "исключения:"),
]

EXCEPTIONS = [
    ("а)", "законопроект или инициатива, подписанные более чем половиной от общего числа "
           "действующих сенаторов штата Сан-Андреас, подлежат обязательному включению в "
           "повестку дня ближайшего пленарного заседания, в том числе назначенного на "
           "13.11.2026, в качестве внеочередного вопроса. "
           "При общем числе действующих сенаторов, равном шестнадцати, инициатива должна "
           "быть подписана не менее чем девятью сенаторами (часть 5 статьи 80 Конституции "
           "штата Сан-Андреас). При соблюдении этого условия отказ во включении инициативы в "
           "повестку дня не допускается;"),
    ("б)", "Сенат вправе включить вопрос в повестку дня пленарного заседания, назначенного "
           "на 13.11.2026 в 19:00, собственным решением, принятым большинством голосов от "
           "общего числа действующих сенаторов (часть 5 статьи 80 Конституции штата "
           "Сан-Андреас), в порядке ведения заседания (пункт «в» части 4 статьи 3 "
           "Конституционного закона «О Сенате штата Сан-Андреас»)."),
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
              width=BODY_W - 150, size=size, lh=int(size * LH), justify=False,
              draw=draw, space_after=0)
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
    lines = wrap(d, text, font, BODY_W - 120)
    lh = int(size * 1.5)
    h = len(lines) * lh + 34
    if draw:
        d.rectangle([BODY_L, y, BODY_R, y + h], fill=SHADE)
        d.line([(BODY_L, y), (BODY_R, y)], fill=GREEN_D, width=3)
        d.line([(BODY_L, y + h), (BODY_R, y + h)], fill=GREEN_D, width=3)
        for i, ln in enumerate(lines):
            x = BODY_L + 44
            for ch in ln:
                d.text((x, y + 17 + i * lh), ch, font=font, fill=GREEN_D)
                x += tw(d, ch, font) + 4
    return y + h + 30


def item(d, y, num, text, quote_text=None, tail=None, size=None, draw=True, after=None):
    size = size or SIZE
    lh = int(size * LH)
    hang = 76
    y = para(d, y, [(num + " ", "b", GREEN_D), (text, "r", INK)], hang=hang, size=size,
             lh=int(size * LH), draw=draw, space_after=0)
    if quote_text:
        y = quote(d, y + 6, quote_text, size=size - 1, draw=draw, space=14)
    if tail:
        y = para(d, y, [(tail, "r", INK)], left=BODY_L + hang, width=BODY_W - hang,
                 size=size, lh=int(size * LH), draw=draw, space_after=0)
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


def letterhead(d, draw=True):
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
    return 812


def body1(d, draw=True, air=0):
    y = letterhead(d, draw)
    y = address_box(d, y, draw=draw)
    y = title_band(d, y, TITLE, size=30, draw=draw)
    y = para(d, y, [(INTRO, "r", INK)], size=SIZE, lh=int(SIZE * LH), draw=draw,
             space_after=int(SIZE * 1.0))
    y = center_head(d, y, "УСТАНОВЛЕНО:", size=32, draw=draw, space_before=22 + air)
    for num, text, q, tail in ITEMS:
        y = item(d, y, num, text, q, tail, draw=draw,
                 after=int(SIZE * 1.05) + air)
    return y


def body2(d, draw=True, air=0):
    y = top_band(d, draw, 2, 2)
    y = para(d, y, [(BASIS, "r", INK)], size=SIZE, lh=int(SIZE * LH), draw=draw,
             space_after=int(SIZE * 1.05))
    y = center_head(d, y, "РЕШИЛ:", size=32, draw=draw, space_before=6 + air)
    for num, text in DECISIONS:
        y = para(d, y, [(num + " ", "b", GREEN_D), (text, "r", INK)], hang=76,
                 size=SIZE, lh=int(SIZE * LH), draw=draw,
                 space_after=int(SIZE * 0.85) + air)
    for num, text in EXCEPTIONS:
        y = para(d, y, [(num + " ", "b", GREEN_D), (text, "r", INK)], hang=110,
                 left=BODY_L + 76, width=BODY_W - 76, size=SIZE, lh=int(SIZE * LH),
                 draw=draw, space_after=int(SIZE * 0.85) + air)
    return y


def signature(d, sy, draw=True):
    d.line([(1820, sy + 150), (2660, sy + 150)], fill=INK, width=4)
    d.text((1850, sy + 172), "Marcus Nomad", font=F(FB, 34), fill=INK)
    d.text((1850, sy + 222), "Председатель Сената", font=F(FI, 26), fill=MUTED)
    d.text((1850, sy + 264), "штата Сан-Андреас", font=F(FI, 26), fill=MUTED)
    d.text((1850, sy + 314), "12 ноября 2026 года", font=F(FI, 24), fill=MUTED)

    seal = Image.open(os.path.join(ASSETS, "great_seal.png")).convert("RGBA")
    seal = seal.resize((540, 540), Image.LANCZOS)
    r, g, b, a = seal.split()
    r = r.point(lambda v: int(max(0, min(255, (v - 112) * 1.42 + 92))))
    g = g.point(lambda v: int(max(0, min(255, (v - 100) * 1.42 + 80))))
    b = b.point(lambda v: int(max(0, min(255, (v - 74) * 1.42 + 54))))
    seal = Image.merge("RGBA", (r, g, b, a))
    d._image.paste(seal, (800, sy - 96), seal)

    d.line([(BODY_L, 3966), (BODY_R, 3966)], fill=RULE, width=2)
    tracked(d, 3996, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 22), 8, MUTED)
    return sy + 400


def page1(d, draw=True, air=0):
    y = body1(d, draw, air)
    if draw and y < 3900:
        d.line([(BODY_L, 3966), (BODY_R, 3966)], fill=RULE, width=2)
        tracked(d, 3996, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 22), 8, MUTED)
    return y


def page2(d, draw=True, air=0):
    y = body2(d, draw, air)
    if not draw:
        return y
    sy = max(y + 130, 3170)
    if sy + 440 > 3900:
        sy = 3900 - 440
    signature(d, sy, draw)
    return sy + 440


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
    best = 26
    for sz in range(39, 25, -1):
        globals()["SIZE"] = sz
        e1 = measure(page1)
        e2 = measure(page2)
        print(f"кегль {sz}: стр.1 -> {e1}, стр.2 -> {e2}")
        if e1 <= 3260 and e2 <= 2760:
            best = sz
            break
    globals()["SIZE"] = best
    print("кегль:", best)

    e1 = measure(page1)
    air1 = 0
    if e1 < 3690:
        air1 = min(70, int((3690 - e1) / 7))
    e2 = measure(page2)
    air2 = 0
    if e2 < 2900:
        air2 = min(96, int((2900 - e2) / 8))
    print("воздух:", air1, air2)

    base = "Уведомление о перенесении рассмотрения инициативы"
    render(page1, os.path.join(OUT, base + " - стр. 1.png"), air=air1)
    render(page2, os.path.join(OUT, base + " - стр. 2.png"), air=air2)
