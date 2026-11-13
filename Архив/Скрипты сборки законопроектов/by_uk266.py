# -*- coding: utf-8 -*-
"""ACT. 266: УК ст. 15.4 и 15.5 — денежная взятка до 100.000$ не образует состава."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fulltext import article, build, resolve
from by_act import row

UK = os.path.basename(resolve("Уголовный Кодекс штата Сан-Андреас.json"))

OUT = "Законопроекты 266–269 (устранение коллизий)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "Законопроекты", OUT)
os.makedirs(DIR, exist_ok=True)

a154 = article(UK, "15.4")
assert a154.endswith("5 лет лишения свободы.")
a154 = a154.split("\n", 1)[1]           # без строки-заголовка «Статья 15.4»

a155 = article(UK, "15.5")
cut = a155.find("\nС\nтатья 15.5.1")
assert cut > 0, "не найден разрыв перед 15.5.1"
a155 = a155[:cut].split("\n", 1)[1]     # без заголовка и без склейки с 15.5.1

NOTE4 = ("Примечание: получение должностным лицом взятки в денежной форме в размере, "
         "не превышающем 100.000$, не образует состава преступления, предусмотренного "
         "настоящей статьей.")
NOTE5 = ("Примечание: дача должностному лицу взятки в денежной форме в размере, "
         "не превышающем 100.000$, не образует состава преступления, предусмотренного "
         "настоящей статьей.")

def pair(loc, body, note):
    anchor = "5 лет лишения свободы."
    assert body.count(anchor) == 1
    left = loc + "\n" + body.replace(anchor, "5 лет лишения [[R]]свободы.[[/R]]", 1)
    right = loc + "\n" + body + "\n[[G]]" + note + "[[/G]]"
    return (left, right)

rows = [
    pair("Статья 15.4", a154, NOTE4),
    pair("Статья 15.5", a155, NOTE5),
]

SECTION1 = (
    "Законопроект направлен на устранение правовой коллизии путем исключения из состава "
    "преступления получения и дачи взятки в денежной форме в размере, не превышающем 100.000$."
)

fname = "ACT.266.Уголовный кодекс (взятки).docx"
subtitle = "о внесении изменений в Уголовный Кодекс штата San-Andreas"
build([("SECTION. 2. ВНЕСЕНИЕ ПРАВКИ В Уголовный Кодекс штата San-Andreas", rows)],
      os.path.join(DIR, fname), "ACT. 266", subtitle, SECTION1)
