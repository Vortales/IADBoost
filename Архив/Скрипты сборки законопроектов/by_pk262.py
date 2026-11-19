# -*- coding: utf-8 -*-
"""ACT. 262: ПК ст. 75 ч. 2 — ссылка на несуществующую статью 6.6 УК заменена статьёй 7.4."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fulltext import article, build, resolve
from by_act import row, line

PK = os.path.basename(resolve("Процессуальный кодекс штата Сан-Андреас.json"))

OUT = "Законопроекты 262 (частное обвинение)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "Законопроекты", OUT)
os.makedirs(DIR, exist_ok=True)

a75 = article(PK, "75")
p2 = line(a75, "Уголовные дела о преступлениях, предусмотренных статьей 6.6")

P2_NEW = p2.replace("статьей 6.6", "статьей 7.4 частью первой")
assert P2_NEW != p2

rows = [
    row("Статья 75, ч. 2", p2, P2_NEW),
]

SECTION1 = (
    "Законопроект направлен на устранение правовой коллизии путем замены недействительной ссылки "
    "на статью 6.6 Уголовного кодекса ссылкой на действующую статью 7.4, устанавливающую "
    "ответственность за клевету."
)

fname = "ACT.262.Процессуальный кодекс (частное обвинение).docx"
subtitle = "о внесении изменений в Процессуальный кодекс штата San-Andreas"
build([("SECTION. 2. ВНЕСЕНИЕ ПРАВКИ В Процессуальный кодекс штата San-Andreas", rows)],
      os.path.join(DIR, fname), "ACT. 262", subtitle, SECTION1)
