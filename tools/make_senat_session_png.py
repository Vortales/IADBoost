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
    H, INK, MUTED, RULE, W, F, para, tracked, tw, wrap, heading,
)

OUT_DIR = os.path.join(os.path.dirname(HERE), "Сенат", "Заседание 13.11.2026")
OUT = os.path.join(OUT_DIR, "Созыв заседания Сената - 13.11.2026.png")

DATE_LINE = "12 ноября 2026 года, г. Лос-Сантос"
RIGHT_META = "Спикер Сената Marcus Nomad, UID-85028"
TITLE = "О СОЗЫВЕ ПЛЕНАРНОГО ЗАСЕДАНИЯ"
SUBTITLE = "официальное сообщение Председателя (Спикера) Сената штата Сан-Андреас"
LEAD = "Настоящим объявляю созыв пленарного заседания Сената штата Сан-Андреас."
BAND = "13 НОЯБРЯ 2026 ГОДА, 19:00"

SECTIONS = [
    ("I.  СВЕДЕНИЯ О ЗАСЕДАНИИ", [
        [("1.1.", "b", GREEN_D),
         (" Пленарное заседание Сената штата Сан-Андреас состоится 13 ноября 2026 года "
          "в 19:00 в зале заседаний Сената, Капитолий штата Сан-Андреас, г. Лос-Сантос.",
          "r", INK)],
        [("1.2.", "b", GREEN_D),
         (" Заседание созывается Председателем (Спикером) Сената штата Сан-Андреас "
          "Marcus Nomad (пункт «а» части 4 статьи 3 Конституционного закона «О Сенате "
          "штата Сан-Андреас»); он же председательствует.", "r", INK)],
    ]),
    ("II.  ЯВКА И ПРАВОМОЧНОСТЬ", [
        [("2.1.", "b", GREEN_D),
         (" Явка сенаторов обязательна; неявка на плановое заседание влечёт меры, "
          "предусмотренные пунктом «и» части 4 статьи 3 Конституционного закона "
          "«О Сенате штата Сан-Андреас».", "r", INK)],
        [("2.2.", "b", GREEN_D),
         (" Заседание правомочно при присутствии не менее половины действующих сенаторов "
          "(часть 1 статьи 9 Конституционного закона «О Сенате штата Сан-Андреас»).",
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
            y = para(d, y, runs, hang=92, size=size, lh=lh,
                     space_after=int(size * 0.50), draw=draw)
    return y


def body(d, size, draw=True):
    y = 1035
    y = para(d, y, [(LEAD, "r", INK)], size=size, lh=int(size * 1.62),
             space_after=int(size * 1.25), draw=draw)
    y = band(d, y, size, draw)
    y += int(size * 1.0)
    y = sections(d, y, size, draw)
    y += int(size * 0.35)
    y = para(d, y, [("Прошу сенаторов обеспечить явку к указанному времени.", "r", INK)],
             size=size, lh=int(size * 1.62), draw=draw)
    return y


def render(size):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle(FRAME, outline=GREEN, width=9)

    em = Image.open(os.path.join(ASSETS, "state_emblem.png")).convert("RGB")
    em = em.resize((260, 260), Image.LANCZOS)
    img.paste(em, (CENTER - 130, 150))

    base.title_mixed(d, 455, [("STATE", F(FB, 58), 10),
                              ("of", F(FI, 50), 2),
                              ("SAN ANDREAS", F(FB, 58), 10)])
    tracked(d, 560, "SENATE OF THE STATE OF SAN ANDREAS", F(FB, 26), 7, GREEN)
    d.line([(840, 640), (2160, 640)], fill=GREEN, width=3)

    tracked(d, 690, TITLE, F(FB, 54), 3, INK)
    tracked(d, 790, SUBTITLE.upper(), F(FR, 23), 2, MUTED)

    d.text((BODY_L, 875), DATE_LINE, font=F(FI, 26), fill=MUTED)
    d.text((BODY_R - tw(d, RIGHT_META, F(FI, 26)), 875), RIGHT_META,
           font=F(FI, 26), fill=MUTED)
    d.line([(BODY_L, 925), (BODY_R, 925)], fill=RULE, width=2)

    end = body(d, size)

    sy = max(end + int(size * 1.6), 3010)
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
    for size in range(48, 21, -1):
        scratch = Image.new("RGB", (W, H), "white")
        d0 = ImageDraw.Draw(scratch)
        end = body(d0, size, draw=False)
        if end <= 3150:
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
