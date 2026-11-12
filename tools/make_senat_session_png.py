# -*- coding: utf-8 -*-
"""Официальное сообщение о созыве пленарного заседания Сената - PNG.

Стиль тот же, что у «Итогов пленарного заседания»: зелёная рамка, печать Сената,
двуязычная шапка, полоса-суть, рубленые лид-ины, блок подписи.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import make_senat_results_png as base                      # noqa: E402
from PIL import Image, ImageDraw                           # noqa: E402

from make_senat_results_png import (                       # noqa: E402
    ASSETS, BODY_L, BODY_R, BODY_W, CENTER, FB, FI, FR, FRAME, GREEN, GREEN_D,
    H, INK, MUTED, RULE, W, F, para, tracked, tw,
)

TRACK = 4


def heading(d, y, text, size=30, draw=True):
    """Заголовок раздела: по левому краю, с линейкой под ним."""
    font = F(FB, size)
    if draw:
        x = BODY_L
        for ch in text:
            d.text((x, y), ch, font=font, fill=GREEN_D)
            x += tw(d, ch, font) + TRACK
        d.line([(BODY_L, y + int(size * 1.55)), (BODY_R, y + int(size * 1.55))],
               fill=RULE, width=3)
    return y + int(size * 2.35)

OUT_DIR = os.path.join(os.path.dirname(HERE), "Сенат", "Заседание 13.11.2026")
OUT = os.path.join(OUT_DIR, "Созыв заседания Сената - 13.11.2026.png")

DATE_LINE = "12 ноября 2026 года, г. Лос-Сантос"
RIGHT_META = "Спикер Сената Marcus Nomad, номер паспорта 85028"
TITLE = "О СОЗЫВЕ ПЛЕНАРНОГО ЗАСЕДАНИЯ"
SUBTITLE = "официальное сообщение Спикера Сената штата Сан-Андреас"
LEAD = "Настоящим объявляю созыв пленарного заседания Сената штата Сан-Андреас."
BAND = "13 НОЯБРЯ 2026 ГОДА, 19:00"

SECTIONS = [
    ("I.  СВЕДЕНИЯ О ЗАСЕДАНИИ", [
        [("1.1.", "b", GREEN_D),
         (" Пленарное заседание Сената штата Сан-Андреас состоится 13 ноября 2026 года "
          "в 19:00 в зале заседаний Сената, Капитолий штата Сан-Андреас, город "
          "Лос-Сантос.", "r", INK)],
        [("1.2.", "b", GREEN_D),
         (" Заседание созывается Спикером Сената штата Сан-Андреас "
          "Marcus Nomad (пункт «а» части 4 статьи 3 Конституционного закона «О Сенате "
          "штата Сан-Андреас»); он же председательствует.", "r", INK)],
    ]),
    ("II.  ЯВКА И ПРАВОМОЧНОСТЬ", [
        [("2.1.", "b", GREEN_D),
         (" Явка сенаторов обязательна; неявка на плановое заседание влечёт меры, "
          "предусмотренные пунктом «и» части 4 статьи 3 Конституционного закона "
          "«О Сенате штата Сан-Андреас».", "r", INK)],
        [("2.2.", "b", GREEN_D),
         (" Заседание правомочно при присутствии не менее половины действующих сенаторов "
          "(часть 1 статьи 9 Конституционного закона «О Сенате штата Сан-Андреас»).",
          "r", INK)],
    ]),
]


def band(d, y, size, draw=True):
    """Полоса с датой и временем заседания."""
    h = 150
    text = BAND
    fs = 58
    while fs > 26 and tw(d, text, F(FB, fs)) + 3 * (len(text) - 1) > BODY_W - 80:
        fs -= 1
    if draw:
        d.line([(BODY_L, y), (BODY_R, y)], fill=GREEN, width=3)
        d.line([(BODY_L, y + h), (BODY_R, y + h)], fill=RULE, width=2)
        tracked(d, y + (h - fs) // 2 - 8, text, F(FB, fs), 3, GREEN_D, draw=draw)
    return y + h


def sections(d, y, size, draw=True):
    lh = int(size * 1.62)
    for title, items in SECTIONS:
        y = heading(d, y, title, size, draw)
        for runs in items:
            y = para(d, y, runs, hang=92, size=size, lh=lh, justify=False,
                     space_after=int(size * 0.50), draw=draw)
    return y


def body(d, size, draw=True):
    y = 1035
    y = para(d, y, [(LEAD, "r", INK)], size=size, lh=int(size * 1.62),
             justify=False, space_after=int(size * 1.25), draw=draw)
    y = band(d, y, size, draw)
    y += int(size * 1.0)
    y = sections(d, y, size, draw)
    y += int(size * 0.35)
    y = para(d, y, [("Прошу сенаторов обеспечить явку к указанному времени.", "r", INK)],
             size=size, lh=int(size * 1.62), justify=False, draw=draw)
    return y


def render(size):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle(FRAME, outline=GREEN, width=9)

    em = Image.open(os.path.join(ASSETS, "state_emblem.png")).convert("RGB")
    em = em.resize((236, 236), Image.LANCZOS)
    img.paste(em, (CENTER - 118, 152))

    base.title_mixed(d, 450, [("STATE", F(FB, 56), 10),
                              ("of", F(FI, 48), 2),
                              ("SAN ANDREAS", F(FB, 56), 10)])
    tracked(d, 552, "SENATE OF THE STATE OF SAN ANDREAS", F(FB, 25), 7, GREEN)
    d.line([(900, 628), (2100, 628)], fill=GREEN, width=3)

    tracked(d, 676, TITLE, F(FB, 52), 3, INK)
    tracked(d, 772, SUBTITLE.upper(), F(FR, 22), 2, MUTED)

    d.text((BODY_L, 858), DATE_LINE, font=F(FI, 25), fill=MUTED)
    d.text((BODY_R - tw(d, RIGHT_META, F(FI, 25)), 858), RIGHT_META,
           font=F(FI, 25), fill=MUTED)
    d.line([(BODY_L, 906), (BODY_R, 906)], fill=RULE, width=2)

    end = body(d, size)

    # --- подпись и печать: общий нижний блок
    sy = min(max(end + int(size * 2.6), 3170), 3300)
    # подпись прижата к правому краю текстовой колонки, как строки метаданных сверху
    line_r = BODY_R
    sig_name = "Marcus Nomad"
    sig_role = ["Спикер Сената", "штата Сан-Андреас"]
    f_name, f_role = F(FB, 64), F(FI, 48)
    block_w = max([tw(d, sig_name, f_name)] +
                  [tw(d, t, f_role) for t in sig_role])
    line_l = BODY_R - block_w

    d.line([(line_l, sy), (line_r, sy)], fill=INK, width=4)
    d.text((line_l, sy + 46), sig_name, font=f_name, fill=INK)
    d.text((line_l, sy + 132), sig_role[0], font=f_role, fill=MUTED)
    d.text((line_l, sy + 190), sig_role[1], font=f_role, fill=MUTED)

    seal = Image.open(os.path.join(ASSETS, "great_seal.png")).convert("RGBA")
    seal = seal.resize((708, 708), Image.LANCZOS)      # втрое крупнее
    img.paste(seal, (BODY_L + 10, 3938 - 708 - 6), seal)   # низ печати - над подвалом

    d.line([(BODY_L, 3940), (BODY_R, 3940)], fill=RULE, width=2)
    tracked(d, 3976, "STATE OF SAN ANDREAS  ·  SENATE", F(FR, 21), 8, MUTED)
    return img, end, sy


def build(path):
    chosen = None
    for size in range(64, 21, -1):
        scratch = Image.new("RGB", (W, H), "white")
        d0 = ImageDraw.Draw(scratch)
        end = body(d0, size, draw=False)
        if end <= 2960:
            chosen = size
            break
    chosen = chosen or 22
    print("кегль тела:", chosen)

    img, end, sy = render(chosen)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG", dpi=(300, 300))
    print("OK", path, img.size, "| низ тела:", end, "| подпись:", sy)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else OUT)
