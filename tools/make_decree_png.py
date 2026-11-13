# -*- coding: utf-8 -*-
"""Рендер проекта указа Губернатора в PNG (A4, 200 dpi, DejaVu Serif).

Подбирает кегль основного текста так, чтобы документ занимал одну страницу
и не наезжал на колонтитул.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1654, 2339          # A4 @ 200 dpi
ML, MR, MT, MB = 170, 145, 120, 120
CW = W - ML - MR
FOOTER_Y = H - MB - 40     # граница, выше которой должен закончиться текст

FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

INK = (26, 26, 26)
GREY = (110, 110, 110)
RULE = (120, 120, 120)

_cache = {}


def f(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tw(d, text, font):
    b = d.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def center(d, y, text, font, fill=INK, tracking=0):
    if tracking:
        widths = [tw(d, ch, font) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=font, fill=fill)
            x += w + tracking
        return y + font.size + 6
    d.text(((W - tw(d, text, font)) / 2, y), text, font=font, fill=fill)
    return y + font.size + 6


def line_lr(d, y, left, right, font):
    d.text((ML, y), left, font=font, fill=INK)
    d.text((W - MR - tw(d, right, font), y), right, font=font, fill=INK)
    return y + font.size + 8


def wrap(d, text, font, width):
    lines, cur = [], ""
    for wd in text.split():
        probe = wd if not cur else cur + " " + wd
        if tw(d, probe, font) <= width:
            cur = probe
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def para(d, y, text, font, width=CW, lh=None, indent=0, justify=True,
         space_after=0, fill=INK):
    lh = lh or int(font.size * 1.45)
    lines = wrap(d, text, font, width - indent)
    for i, ln in enumerate(lines):
        last = (i == len(lines) - 1)
        x = ML + (indent if i == 0 else 0)
        avail = width - (indent if i == 0 else 0)
        if justify and not last:
            words = ln.split()
            if len(words) > 1:
                natural = sum(tw(d, w_, font) for w_ in words)
                space = (avail - natural) / (len(words) - 1)
                cx = x
                for w_ in words:
                    d.text((cx, y), w_, font=font, fill=fill)
                    cx += tw(d, w_, font) + space
            else:
                d.text((x, y), ln, font=font, fill=fill)
        else:
            d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y + space_after


PREAMBLE_1 = ("Руководствуясь частью 1 статьи 80, частью 3 статьи 80, частью 4 статьи 80 "
              "и частью 1 статьи 83 Конституции штата Сан-Андреас, частью 2 Поправки 8 "
              "к Конституции штата Сан-Андреас, пунктом «в» части 2 статьи 10 "
              "Конституционного закона «О Правительстве штата Сан-Андреас», частями 3 и 4 "
              "статьи 13 Конституционного закона «О нормативных правовых актах штата "
              "Сан-Андреас», статьями 26 и 74 Конституции штата Сан-Андреас,")

PREAMBLE_2 = ("принимая во внимание, что Указ Губернатора штата Сан-Андреас № 81 "
              "«Об отклонении закона (вето)» от 30 октября 2026 года не содержит "
              "мотивированного обоснования, обязательного в силу части 1 статьи 83 "
              "Конституции штата Сан-Андреас; не позволяет достоверно установить "
              "отклоняемый акт, поскольку реквизит даты его принятия не заполнен, "
              "наименование Указа говорит об отклонении «закона», а постановляющая "
              "часть — об отклонении «поправки», что противоречит требованию "
              "однозначности терминологии (часть 1 статьи 11 Конституционного закона "
              "«О нормативных правовых актах штата Сан-Андреас»); издан в отношении "
              "Закона, принятого Сенатом штата Сан-Андреас и получившего предварительное "
              "одобрение Федерального Суда штата Сан-Андреас,")

TITLE = ("О признании утратившим силу Указа Губернатора штата Сан-Андреас № 81 "
         "от 30 октября 2026 года и о подписании и обнародовании Закона штата "
         "Сан-Андреас, принятого Сенатом штата Сан-Андреас 28 октября 2026 года")

POINTS = [
    "1. Признать утратившим силу Указ Губернатора штата Сан-Андреас № 81 "
    "«Об отклонении закона (вето)» от 30 октября 2026 года со дня официального "
    "опубликования настоящего Указа.",

    "2. Подписать и обнародовать Закон штата Сан-Андреас «О внесении изменений "
    "в Процессуальный кодекс штата Сан-Андреас» (ACT. 244), принятый Сенатом штата "
    "Сан-Андреас 28 октября 2026 года и одобренный Федеральным Судом штата "
    "Сан-Андреас (акт от «____» ____________ 2026 года № ________).",

    "3. Установить, что Закон, указанный в пункте 2 настоящего Указа, вступает в силу "
    "со дня его подписания и обнародования — в порядке, предусмотренном частью 2 "
    "Поправки 8 к Конституции штата Сан-Андреас.",

    "4. Установить, что настоящий Указ не является повторным направлением Закона, "
    "указанного в пункте 2 настоящего Указа, и не возобновляет течение срока, "
    "предусмотренного частью 4 статьи 80 Конституции штата Сан-Андреас.",

    "5. Администрации Губернатора штата Сан-Андреас обеспечить включение Закона, "
    "указанного в пункте 2 настоящего Указа, в Законодательную базу штата "
    "Сан-Андреас и его официальное опубликование в порядке, установленном статьёй 16 "
    "Конституционного закона «О нормативных правовых актах штата Сан-Андреас».",

    "6. Настоящий Указ вступает в силу со дня его официального опубликования.",
]


def layout(d, size):
    """Рисует документ; возвращает нижнюю границу текста."""
    body = f(FONT_R, size)
    lh = int(size * 1.46)
    tf = f(FONT_B, 25)

    y = MT
    y = center(d, y, "ГУБЕРНАТОР", f(FONT_B, 30), tracking=7)
    y = center(d, y, "ШТАТА САН-АНДРЕАС", f(FONT_B, 20), tracking=4)
    y += 6
    d.line([(ML + 250, y), (W - MR - 250, y)], fill=RULE, width=2)
    y += 16
    y = center(d, y, "УКАЗ", f(FONT_B, 38), tracking=10)
    y = center(d, y, "№ ________", f(FONT_R, 21), fill=GREY)
    y += 2
    y = line_lr(d, y, "«____» ноября 2026 года", "г. Лос-Сантос", f(FONT_R, 20))
    y += 12

    for ln in wrap(d, TITLE, tf, CW):
        d.text(((W - tw(d, ln, tf)) / 2, y), ln, font=tf, fill=INK)
        y += int(tf.size * 1.38)
    y += 14

    y = para(d, y, PREAMBLE_1, body, lh=lh, indent=int(size * 1.7), space_after=10)
    y = para(d, y, PREAMBLE_2, body, lh=lh, indent=int(size * 1.7), space_after=18)

    y = center(d, y, "ПОСТАНОВЛЯЮ:", f(FONT_B, 24), tracking=3)
    y += 16

    for p in POINTS:
        y = para(d, y, p, body, lh=lh, indent=int(size * 1.7), space_after=13)

    y += 40
    gf = f(FONT_R, 24)
    d.text((ML, y), "Губернатор", font=gf, fill=INK)
    d.text((ML, y + 32), "штата Сан-Андреас", font=gf, fill=INK)
    d.text((W - MR - 460, y + 16), "__________________", font=gf, fill=INK)
    d.text((W - MR - 445, y + 46), "Tommy Harlow", font=f(FONT_B, 20), fill=INK)
    return y + 82


def build(path):
    # подбор кегля
    size = None
    for cand in (28, 27, 26, 25, 24, 23, 22, 21):
        scratch = Image.new("RGB", (W, H), "white")
        bottom = layout(ImageDraw.Draw(scratch), cand)
        if bottom <= FOOTER_Y:
            size = cand
            break
    if size is None:
        size = 21
    print("кегль:", size)

    img = Image.new("RGB", (W, H), "white")

    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    wf = f(FONT_B, 300)
    w_, h_ = wd.textbbox((0, 0), "ПРОЕКТ", font=wf)[2], wd.textbbox((0, 0), "ПРОЕКТ", font=wf)[3]
    layer = Image.new("RGBA", (w_ + 80, h_ + 140), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((40, 40), "ПРОЕКТ", font=wf, fill=(0, 0, 0, 26))
    layer = layer.rotate(28, expand=True, resample=Image.BICUBIC)
    wm.paste(layer, ((W - layer.width) // 2, (H - layer.height) // 2), layer)
    img = Image.alpha_composite(img.convert("RGBA"), wm).convert("RGB")

    d = ImageDraw.Draw(img)
    layout(d, size)

    d.line([(ML, H - MB - 34), (W - MR, H - MB - 34)], fill=(205, 205, 205), width=1)
    ff = f(FONT_R, 15)
    note = ("Проект. Номер и дата Указа, реквизиты акта Федерального Суда и дата "
            "официального опубликования заполняются при подписании.")
    for i, ln in enumerate(wrap(d, note, ff, CW)):
        d.text((ML, H - MB - 24 + i * 19), ln, font=ff, fill=GREY)

    img.save(path, "PNG", dpi=(200, 200))
    print("OK", path, img.size)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "decree.png")
