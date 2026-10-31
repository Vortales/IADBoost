# -*- coding: utf-8 -*-
"""ACT. 263: Приложение № 1, ст. 8 ч. 1 — пропуск только на территорию своего органа."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fulltext import article, build, resolve
from by_act import row, line

PR = os.path.basename(resolve(
    "Приложение №1 к Уголовному кодексу штата Сан-Андреас О закрытых, охраняемых и особо охраня….json"))

OUT = "Законопроекты 263 (пропуска на закрытые территории)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "Законопроекты", OUT)
os.makedirs(DIR, exist_ok=True)

a8 = article(PR, "8")
p1 = line(a8, "ч. 1 Руководитель государственного органа")

P1_NEW = p1.replace(
    "его заместитель, Губернатор",
    "его заместитель (в отношении закрытой территории, находящейся в ведении соответствующего "
    "государственного органа), Губернатор")
assert P1_NEW != p1

L, R = row("Статья 8, ч. 1", p1, P1_NEW)
if "[[R]]" not in L:                       # правка только добавляет текст
    assert "заместитель" in L
    L = L.replace("заместитель", "[[R]]заместитель[[/R]]", 1)
rows = [(L, R)]

SECTION1 = (
    "Законопроект направлен на устранение правовой коллизии путем ограничения полномочия "
    "руководителя государственного органа по выдаче пропуска закрытой территорией, находящейся в "
    "его ведении."
)

fname = "ACT.263.Приложение № 1 к Уголовному кодексу (пропуска на закрытые территории).docx"
subtitle = "о внесении изменений в Приложение № 1 к Уголовному кодексу штата San-Andreas"
build([("SECTION. 2. ВНЕСЕНИЕ ПРАВКИ В Приложение № 1 к Уголовному кодексу штата San-Andreas", rows)],
      os.path.join(DIR, fname), "ACT. 263", subtitle, SECTION1)
