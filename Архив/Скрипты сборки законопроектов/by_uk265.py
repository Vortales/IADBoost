# -*- coding: utf-8 -*-
"""ACT. 265: УК ст. 12.8 ч. 2 — устройства аудио-, видеозаписи, прослушивания и иные
технические средства наблюдения."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fulltext import article, build, resolve

UK = os.path.basename(resolve("Уголовный Кодекс штата Сан-Андреас.json"))

OUT = "Законопроекты 265 (технические средства наблюдения)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "Законопроекты", OUT)
os.makedirs(DIR, exist_ok=True)

a128 = article(UK, "12.8")
lines = a128.split("\n")
i = lines.index("ч. 2")
unit = "\n".join(lines[i:i + 4])          # ч. 2 + наказание + размер наказания

OLD_TAIL = "мед. инструментов."
NEW_TAIL = ("мед. инструментов, а также устройств аудиозаписи, видеозаписи, прослушивания "
            "либо иных технических средств наблюдения.")
assert unit.count(OLD_TAIL) == 1

LOC = "Статья 12.8, ч. 2"
L = LOC + "\n" + unit.replace(OLD_TAIL, "[[R]]" + OLD_TAIL + "[[/R]]", 1)
R = LOC + "\n" + unit.replace(
    OLD_TAIL,
    "мед. инструментов,[[G]] а также устройств аудиозаписи, видеозаписи, прослушивания "
    "либо иных технических средств наблюдения[[/G]].")
assert R.count("[[G]]") == 1
rows = [(L, R)]

SECTION1 = (
    "Законопроект направлен на устранение правового пробела путем отнесения устройств "
    "аудиозаписи, видеозаписи, прослушивания и иных технических средств наблюдения к предметам, "
    "незаконные хранение, ношение и использование которых запрещены статьей 12.8 Уголовного кодекса."
)

fname = "ACT.265.Уголовный кодекс (технические средства наблюдения).docx"
subtitle = "о внесении изменений в Уголовный Кодекс штата San-Andreas"
build([("SECTION. 2. ВНЕСЕНИЕ ПРАВКИ В Уголовный Кодекс штата San-Andreas", rows)],
      os.path.join(DIR, fname), "ACT. 265", subtitle, SECTION1)
