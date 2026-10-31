# -*- coding: utf-8 -*-
"""ACT. 269: Закон о СМИ, ст. 11 ч. 2 — срок хранения видеофиксации; ст. 14 ч. 3 — 15 минут."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fulltext import article, build, resolve

SM = os.path.basename(resolve("Закон О средствах массовой информации штата Сан-Андреас.json"))

OUT = "Законопроекты 266–269 (устранение коллизий)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "Законопроекты", OUT)
os.makedirs(DIR, exist_ok=True)

a11 = article(SM, "11")
a14 = article(SM, "14")

L11 = a11.split("\n")
i2 = [i for i, l in enumerate(L11) if l.startswith("ч. 2 ")][0]
p2_11 = " ".join(L11[i2:])          # часть разорвана переносом строки в источнике
TAIL11 = "до приезда сотрудника силовой структуры."
assert p2_11.endswith(TAIL11)
a11_ok = True

ADD11 = " Видеофиксация, предусмотренная настоящей частью, хранится не менее 48 часов."

c3_14 = [l for l in a14.split("\n") if l.startswith("ч. 3 ")][0]
TAIL14 = "передать им задержанного."
assert c3_14.endswith(TAIL14)

ADD14 = (" Ограничение свободы, предусмотренное частью 1 настоящей статьи, не может превышать "
         "15 минут с момента задержания; по истечении указанного срока задержанный подлежит освобождению.")

def pair(loc, body, tail, add):
    left = loc + "\n" + body.replace(tail, "[[R]]" + tail + "[[/R]]", 1)
    right = loc + "\n" + body + "[[G]]" + add + "[[/G]]"
    return (left, right)

body11 = " ".join(p2_11.split())
assert body11.endswith(TAIL11), body11[-80:]

rows = [
    pair("Статья 11, ч. 2", body11, TAIL11, ADD11),
    pair("Статья 14, ч. 3", c3_14, TAIL14, ADD14),
]

SECTION1 = (
    "Законопроект направлен на устранение правового пробела путем установления срока хранения "
    "видеофиксации и предельного срока ограничения свободы при гражданском задержании "
    "сотрудниками Weazel News."
)

fname = "ACT.269.Закон о СМИ (гражданское задержание).docx"
subtitle = "о внесении изменений в Закон «О средствах массовой информации штата San-Andreas»"
build([("SECTION. 2. ВНЕСЕНИЕ ПРАВКИ В Закон «О средствах массовой информации штата San-Andreas»", rows)],
      os.path.join(DIR, fname), "ACT. 269", subtitle, SECTION1)
